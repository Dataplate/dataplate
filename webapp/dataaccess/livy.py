import os
import time
import requests
import hashlib
import re
import json
import copy
import datetime

from urllib.parse import urlencode
from flask_login import current_user

from .app import app, db
from .models import GlobalConfig, LivySession, Dataset, Role
from .audit import log_action
from .filesystem import file_exists
from .ssm import SSM


class StatementError(Exception):
    pass


class LivyClient:
    def __init__(self, refresh=False, b_async=False):
        """
        Constructs Livy client

        Parameters
        ----------
        refresh : boolean
            Whether to use force running query even cached results already exist (default: False)
        async : boolean
            Whether should the client wait for query to finish or return control back to client (default: False)
        """
        self.refresh = refresh
        self.b_async = b_async
        self.config = GlobalConfig.get()
        if self.config.livy_url:
            self.livy_url = self.config.livy_url.rstrip('/')
        if self.config.output_path:
            self.output_path = self.config.output_path.rstrip('/')

    def validate_session(self):
        """
        Make sure there's live Livy session.
        """
        if current_user.livy_session is None:
            self.new_session()
        else:
            self.wait_for_session(renew=True)

    def new_session(self):
        """
        Start new Livy session.
        """
        properties = {
            'proxyUser': 'hadoop',
            'name': '{} ({})'.format(self.config.session_name, current_user.username),
            'heartbeatTimeoutInSecond': 0,
            'driverMemory': '{}M'.format(self.config.driver_memory_mb),
            'conf': json.loads(self.config.spark_conf)
        }
        r = requests.post('{}/sessions'.format(self.livy_url), json=properties)
        r.raise_for_status()
        r_json = r.json()

        current_user.livy_session = LivySession(
            livy_id=r_json['id'], info=r_json)
        db.session.commit()

        app.logger.info('Starting new session for user {}: {}'.format(
            current_user.username, r_json))

        self.wait_for_session()

    def update_session_status(self):
        """
        Retrieve current Livy session status from server.
        """
        if current_user.livy_session:
            session = copy.deepcopy(current_user.livy_session.info)
            r = requests.get(\
                    '{}/sessions/{}'.format(self.livy_url, current_user.livy_session.livy_id))
            if r.status_code == 404:
                session['state'] = 'dead'
            else:
                r.raise_for_status()
                session = r.json()
                session.pop('log', None)
            current_user.livy_session.info = session
            current_user.livy_session.updated_on = datetime.datetime.utcnow()
            db.session.commit()

    def wait_for_session(self, renew=False):
        """
        Wait until Livy session is available.

        Parameters
        ----------
        renew : boolean
            Whether to start new session if old session is dead.
        """
        start = time.time()
        ready = False
        while not ready and time.time(
        ) - start < self.config.session_wait_timeout:
            time.sleep(1)
            self.update_session_status()
            if current_user.livy_session.info['state'] in ['idle', 'busy']:
                if not renew:
                    app.logger.info('Session is ready: {}'.format(
                        current_user.livy_session.info))
                    log_action('new_session',
                               str(current_user.livy_session.info))
                ready = True
            elif current_user.livy_session.info['state'] \
                    in ['shutting_down', 'error', 'dead', 'success']:
                app.logger.info('Livy reached its final state: {}'.format(
                    current_user.livy_session.info))
                break
        if not ready:
            if renew:
                self.new_session()
            else:
                raise Exception('Timeout waiting for session')

    def is_running(self, code):
        """
        Checks whether the same code is running already in the same session
        to prevent multiple executions.
        """
        if current_user.livy_session:
            r = requests.get('{}/sessions/{}/statements'.format(
                self.livy_url, current_user.livy_session.livy_id))
            if r.status_code == 200:
                running_statements = [
                    s['code'] for s in r.json()['statements']
                    if s['state'] == 'running'
                ]
                if code in running_statements:
                    return True
        return False

    def execute_code(self, code, kind='spark'):
        """
        Executes source code using current Livy session.
        
        Parameters
        ----------
        code : str
            Source code
        kind : str
            Source code type supported by Livy (spark, pyspark, sparkr, sql)
        """
        self.validate_session()
        properties = {'code': code, 'kind': kind}
        log_action('execute', code)
        r = requests.post(\
                '{}/sessions/{}/statements'.format(self.livy_url, current_user.livy_session.livy_id),
                json=properties)
        r.raise_for_status()
        self.statement = r.json()
        app.logger.info('Executing new statement: {}'.format(self.statement))
        if not self.b_async:
            self.wait_for_statement()

    def execute_query(self, query):
        """
        Executes SQL query using current Livy session

        Parameters
        ----------
        query : str
            SQL query

        Returns
        -------
        finished?   : If the query finished executing.
        output_path : Path where output is written
        """
        if '"""' in query:
            raise StatementError('The query contains illegal characters')

        normalized_query = re.sub(r'\s+', ' ', query).strip()

        query_hash = hashlib.md5(normalized_query.encode('utf-8')).hexdigest()
        output_path = '/'.join([
            self.output_path, current_user.username,
            query_hash
        ])

        code = '\n'.join([
            self.register_tables(normalized_query),
            'spark.sql("""{}""").write.mode("overwrite").option("compression", "gzip").json("{}")'
            .format(query, output_path)
        ])

        while self.is_running(code):
            app.logger.info(
                'The same query is being running already... waiting for completion'
            )
            if self.b_async:
                return (False, output_path)
            time.sleep(5)

        if self.refresh or not file_exists('{}/_SUCCESS'.format(output_path)):
            self.execute_code(code)
            if self.b_async:
                return (False, output_path)
        else:
            app.logger.info('Query results are found, not executing anything')

        return (True, output_path)

    def wait_for_statement(self):
        """
        Wait until Livy statement finishes running for any reason.
        """
        start = time.time()
        ready = False
        while not ready and time.time(
        ) - start < self.config.statement_wait_timeout:
            time.sleep(1)
            r = requests.get('{}/sessions/{}/statements/{}'.format(\
                    self.livy_url, current_user.livy_session.livy_id, self.statement['id']))
            r.raise_for_status()
            self.statement = r.json()
            output = self.statement.pop('output', None)
            if self.statement['state'] in ['error', 'cancelled', 'available']:
                if output is not None:
                    if output['status'] == 'error':
                        error = output['evalue']
                        if 'traceback' in output:
                            error += '\n' + ''.join(output['traceback'])
                        raise StatementError(error)
                    elif output['status'] == 'ok':
                        app.logger.info('Statement has completed')
                    else:
                        raise Exception(
                            'Unknown statement status: {}'.format(output))
                ready = True
        if not ready:
            raise Exception('Timeout waiting for statement to finish')

    def register_table(self, dataset):
        """
        Returns Scala code that registers Parquet files as table if it's not registered yet
        """
        if dataset.source_type == 'parquet':
            reader = 'spark.read.parquet("{}")'.format(dataset.source_url)

        elif dataset.source_type == 'csv':
            reader = 'spark.read.option("header", "true").option("escape","\\"").csv("{}")'.format(
                dataset.source_url)

        elif dataset.source_type == 'json':
            reader = 'spark.read.json("{}")'.format(dataset.source_url)

        elif dataset.source_type == 'redshift':
            url_parts = dataset.source_url.split('/')
            cluster_name = url_parts[2].split('.')[0]
            dbtable = url_parts[4]
            ssm = SSM()
            jdbc_url = '/'.join(url_parts[:4]) + '?' + urlencode({
                'user': ssm.get_parameter(
                    '/terraform/redshift/{0}/username'.format(cluster_name)),
                'password': ssm.get_parameter(
                    '/terraform/redshift/{0}/password'.format(cluster_name))
            })
            reader = 'spark.read.format("jdbc").option("url", "{jdbc_url}").option("dbtable", "{dbtable}").load()'.format(
                **locals())

        elif dataset.source_type == 'glue':
            reader = 'spark.sql("SELECT * FROM {}")'.format(dataset.source_url)

        else:
            raise Exception('Unsupported table format: {}'.format(
                dataset.source_type))

        code = 'if (!spark.catalog.tableExists("{table}")) {reader}.createOrReplaceTempView("{table}")'.format(
            table=dataset.name, reader=reader)
        if self.refresh:
            code += ' else spark.catalog.refreshTable("{}")'.format(
                dataset.name)
        return code

    def extract_tables(self, query):
        """
        Extracts all table names found in a SQL query
        """
        table_lists = re.findall(r'(?:from|join)\s+(\w+(?:,\s*\w+)*)', query,
                                 re.IGNORECASE)
        tables = [
            table for table_list in table_lists
            for table in re.split(r'[\s,]+', table_list)
        ]
        if len(tables) == 0:
            raise StatementError('Can\'t find any tables in query')
        ds_query = Dataset.query.filter(Dataset.name.in_(tables))
        datasets = ds_query.join(Role.datasets).filter(
            Role.users.contains(current_user)).union(
                ds_query.filter(Dataset.anonymized == True)).all()
        not_accessible = set(tables) - set([d.name for d in datasets])
        if len(not_accessible) > 0:
            raise StatementError(
                'The following tables are not accessible: {}'.format(
                    ','.join(not_accessible)))
        return datasets

    def register_tables(self, query):
        """
        Returns Scala code that registers all tables required for running a SQL query
        """
        return '\n'.join([
            self.register_table(table) for table in self.extract_tables(query)
        ])

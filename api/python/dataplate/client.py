import os
import requests
import tempfile
import logging
import boto3
import time
import json
from shutil import copyfileobj
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)


class DataPlate:
    """
    Initializes Data Access API client.

    Parameters
    -----------
    access_key : str (optional)
        Your own private key that can be obtained through DataPlate Data Access Portal. Default value is taken from the
        `DA_KEY` environment variable.

    dataplate_uri : str (optional)
        DataPlate Portal URI. If not specified, the value is taken from the `DA_URI` environment variable.
    """
    def __init__(self, access_key=None, dataplate_uri=None):
        if dataplate_uri is None:
            if not 'DA_URI' in os.environ:
                raise ValueError(
                    'Can\'t find DA_URI environment variable, dataplate_uri parameter is not provided either!'
                )
            dataplate_uri = os.environ['DA_URI']

        if access_key is None:
            if not 'DA_KEY' in os.environ:
                raise ValueError(
                    'Can\'t find DA_KEY environment variable, access_key parameter is not provided either!'
                )
            access_key = os.environ['DA_KEY']

        self.access_key = access_key
        self.session = requests.session()
        retry = Retry(total=5,
                      read=5,
                      connect=5,
                      backoff_factor=0.3,
                      status_forcelist=(500, 502, 504))
        adapter = HTTPAdapter(max_retries=retry)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        self.base_url = '/'.join(dataplate_uri.split('/')[0:3])

    def _set_proxy_if_needed(self, proxy):
        os.environ.pop('HTTP_PROXY', None)
        try:
            self.session.head('{}/version'.format(self.base_url))
        except requests.exceptions.ConnectionError:
            self.session.proxies = {'http': proxy}
            self.session.head('{}/version'.format(self.base_url))

    def _get_list_of_files(self, s3_client, bucket, prefix, suffix='json.gz'):
        next_token = ''
        base_kwargs = {
            'Bucket': bucket,
            'Prefix': prefix,
        }
        keys = []
        while next_token is not None:
            kwargs = base_kwargs.copy()
            if next_token != '':
                kwargs.update({'ContinuationToken': next_token})
            results = s3_client.list_objects_v2(**kwargs)
            contents = results.get('Contents')
            for i in contents:
                k = i.get('Key')
                if k[-1] != '/' and k.endswith(suffix):
                    keys.append(k)
            next_token = results.get('NextContinuationToken')
        logging.info('Got the following files: {}'.format(keys))

        return keys

    def _read_file(self, s3_client, bucket, key):
        kwargs = {'Bucket': bucket, 'Key': key}
        return s3_client.get_object(**kwargs)['Body']

    def _download_files_as_one(self, s3_client, bucket, keys, output_file):
        with open(output_file, 'wb') as out:
            for key in keys:
                fh = self._read_file(s3_client, bucket, key)
                while True:
                    chunk = fh.read(8192)
                    out.write(chunk)
                    if len(chunk) <= 0:
                        break

    def _files_to_df(self, bucket, prefix, **kwargs):
        import pandas as pd
        with tempfile.NamedTemporaryFile(suffix='.gz') as t:
            output_file = t.name
            s3 = boto3.client('s3')
            files = self._get_list_of_files(s3, bucket, prefix)
            self._download_files_as_one(s3, bucket, files, output_file)
            with open(output_file, 'rb') as fh:
                return pd.read_json(fh, compression='gzip', lines=True, **kwargs)

    def query(self,
              query,
              output_file,
              refresh=False,
              async_m=None,
              request_timeout=None,
              es_index_type=None,
              bucket_suffixes=None,
              bucket_filter=None):
        """
        Executes remote SQL query, and saves results to the specified file.

        Parameters
        ----------
        query : str
            SQL query supported by Apache Spark
        output_file : str
            Full path to the file where results will be saved (results are represented by JSON records separated by the newline)
        refresh : boolean
            Whether to use force running query even cached results already exist (default: False)
        async_m : int
            How many minutes should the client poll the server.
        request_timeout : int/tuple
            requests timeout parameter for a single request.
            https://requests.readthedocs.io/en/master/user/advanced/#timeouts
        es_index_type: str
            elasticSearch option - add change dataset index/type for the allowed cluster [e.g.: index1/type1,index2/type2] ,to search for all types in index ignore the type name (default: None)
        bucket_suffixes: str
            bucket option - bucket path suffix added to your dataset path name, [e.g.: MyPathSuffix1,MyPathSuffix2] (default: None)
        bucket_filter: str
            bucket option - include files in the bucket with file names matching the pattern (default: None)
        """
        headers = {'X-Access-Key': self.access_key}
        params = {}
        if refresh:
            params['refresh'] = '1'
        if async_m:
            timeout = time.time() + async_m * 60
            params['async'] = '1'
        if es_index_type:
            params['es_index_type'] = es_index_type
        if bucket_suffixes:
            params['bucket_suffixes'] = bucket_suffixes
        if bucket_filter:
            params['bucket_filter'] = bucket_filter

        retries = 5
        while True:
            if async_m and timeout < time.time():
                raise Exception('Timeout waiting for query.')
            try:
                logging.info('Sending query...')
                r = self.session.post(\
                        '{}/api/query'.format(self.base_url), params=params, data=query,
                        headers=headers, stream=True, allow_redirects=False, timeout=request_timeout)

                if r.status_code != 200:
                    if r.status_code == 302:
                        raise Exception(
                            'Bad Access Key! Get your access key at: {}'.format(
                                self.base_url))
                    if r.status_code == 206:
                        logging.info('Query is processing, waiting a bit...')
                        time.sleep(5)
                        continue
                    raise Exception(
                        'Bad HTTP exit status returned from the API: {}. Error was: {}'.
                        format(r.status_code, r.text))

                logging.info('Got query result, writing to file.')
                with open(output_file, 'wb') as fh:
                    copyfileobj(r.raw, fh)
                logging.info('Done writing to file.')
                break
            except (requests.exceptions.ConnectionError,
                    requests.exceptions.ReadTimeout) as e:
                logging.exception('Got ConnectionError/ReadTimeout exception.')
                retries -= 1
                if retries <= 0:
                    raise e
                logging.info('Retrying request.')
                continue

    def query_to_df(self,
                    query,
                    refresh=False,
                    async_m=None,
                    request_timeout=None,
                    es_index_type=None,
                    bucket_suffixes=None,
                    bucket_filter=None,
                    **kwargs):
        """
        Executes remote SQL query, and returns Pandas dataframe.
        Use with care as all the content is materialized.

        Parameters
        ----------
        query : str
            SQL query supported by Apache Spark
        refresh : boolean
            Whether to use force running query even cached results already exist (default: False)
        async_m : int
            How many minutes should the client poll the server.
        request_timeout : int/tuple
            requests timeout parameter for a single request.
            https://requests.readthedocs.io/en/master/user/advanced/#timeouts
        es_index_type: str
            elasticSearch option - add change dataset index/type for the allowed cluster [e.g.: index1/type1,index2/type2] ,to search for all types in index ignore the type name (default: None)
        bucket_suffixes: str
            bucket option - bucket path suffix added to your dataset path name, [e.g.: MyPathSuffix1,MyPathSuffix2] (default: None)
        bucket_filter: str
            bucket option - include files in the bucket with file names matching the pattern (default: None)
        **kwargs : params
            Arbitrary parameters to pass to `pandas.read_json()` method

        Returns
        -------
        Pandas dataframe.
        """
        import pandas as pd
        with tempfile.NamedTemporaryFile(suffix='.gz') as t:
            output_file = t.name
            self.query(query, output_file, refresh, async_m, request_timeout, es_index_type, bucket_suffixes, bucket_filter)
            with open(output_file, 'rb') as fh:
                return pd.read_json(fh, compression='gzip', lines=True, **kwargs)


    def execute_pyspark_toFile(self,
                         code,
                         output_file,
                         refresh=True,
                         retries = 1,
                         async_m=None,
                         request_timeout=None,
                         **kwargs):
        """
        Executes remote pyspark code, and saves results to the specified file - use only if the code specify writes to a target file.

        Parameters
        ----------
        code : str
            Code supported by Apache Spark (pyspark code)
        output_file : str
            Full path to the file where results will be saved (results are represented by JSON records separated by the newline)
        refresh : boolean
            Whether to use force running query even cached results already exist (default: True)
        async_m : int
            How many minutes should the client poll the server.
        request_timeout : int/tuple
            requests timeout parameter for a single request.
            https://requests.readthedocs.io/en/master/user/advanced/#timeouts
        """
        headers = {'X-Access-Key': self.access_key}
        params = {}
        if refresh:
            params['refresh'] = '1'
        if async_m:
            timeout = time.time() + async_m * 60
            params['async'] = '1'

        while True:
            if async_m and timeout < time.time():
                raise Exception('Timeout waiting for code.')
            try:
                logging.info('Sending spark code...')
                r = self.session.post( \
                    '{}/api/pyspark_code'.format(self.base_url), params=params, data=code,
                    headers=headers, stream=True, allow_redirects=False, timeout=request_timeout)

                if r.status_code != 200:
                    if r.status_code == 302:
                        raise Exception(
                            'Bad Access Key! Get your access key at: {}'.format(
                                self.base_url))
                    if r.status_code == 206:
                        logging.info('Pyspark code is processing, waiting a bit...')
                        time.sleep(5)
                        continue
                    raise Exception(
                        'Bad HTTP exit status returned from the API: {}. Error was: {}'.
                            format(r.status_code, r.text))

                logging.info('Got pyspark code result, writing to file.')
                with open(output_file, 'wb') as fh:
                    copyfileobj(r.raw, fh)
                logging.info('Done writing to file.')
                break
            except (requests.exceptions.ConnectionError,
                    requests.exceptions.ReadTimeout) as e:
                logging.exception('Got ConnectionError/ReadTimeout exception.')
                retries -= 1
                if retries <= 0:
                    raise e
                logging.info('Retrying request.')
                continue

    def execute_pyspark_toJson(self,
                         code,
                         retries = 1,
                         async_m=None,
                         request_timeout=None,
                         **kwargs):

        """
        Executes remote pyspark code, and output the result as Json.

        Parameters
        ----------
        code : str
            Code supported by Apache Spark (pyspark code)
        async_m : int
            How many minutes should the client poll the server.
        request_timeout : int/tuple
            requests timeout parameter for a single request.
            https://requests.readthedocs.io/en/master/user/advanced/#timeouts
        """

        headers = {'X-Access-Key': self.access_key}
        params = {}
        refresh = True
        if refresh:
            params['refresh'] = '1'
        if async_m:
            timeout = time.time() + async_m * 60
            params['async'] = '1'

        while True:
            if async_m and timeout < time.time():
                raise Exception('Timeout waiting for code.')
            try:
                logging.info('Sending pyspark code...')
                r = self.session.post( \
                    '{}/api/pyspark_code_toJson'.format(self.base_url), params=params, data=code,
                    headers=headers, stream=True, allow_redirects=False, timeout=request_timeout)

                if r.status_code != 200:
                    if r.status_code == 302:
                        raise Exception(
                            'Bad Access Key! Get your access key at: {}'.format(
                                self.base_url))
                    if r.status_code == 206:
                        logging.info('Pyspark code is processing, waiting a bit...')
                        time.sleep(5)
                        continue
                    raise Exception(
                        'Bad HTTP exit status returned from the API: {}. Error was: {}'.
                            format(r.status_code, r.text))

                logging.info('Got pyspark code result, dump json response')
                # logging.info(str(r.text))
                if r.text:
                    rJson = json.loads(r.text)
                    return json.dumps(rJson.get('text/plain'))
                else:
                    logging.exception('Could not find proper output, please check your code')
                # return r.text
                # logging.info('Done writing to file.')
                break
            except (requests.exceptions.ConnectionError,
                    requests.exceptions.ReadTimeout) as e:
                logging.exception('Got ConnectionError/ReadTimeout exception.')
                retries -= 1
                if retries <= 0:
                    raise e
                logging.info('Retrying request.')
                continue
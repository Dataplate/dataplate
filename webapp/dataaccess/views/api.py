import time

from flask import Blueprint, jsonify, abort, request, Response
from flask_login import login_required

from ..app import app
from ..models import *
from ..livy import LivyClient, StatementError
from ..stats import statsd
from ..filesystem import list_files, read_file
from ..audit import log_action

api = Blueprint('api', __name__, url_prefix='/api')


@api.route('/user_names')
@login_required
def user_names():
    return jsonify([u.username for u in User.query.all()])


@api.route('/role_names')
@login_required
def role_names():
    return jsonify([r.name for r in Role.query.all()])


@api.route('/dataset_names')
@login_required
def dataset_names():
    return jsonify([d.name for d in Dataset.query.all()])


@api.route('/query', methods=['POST'])
@login_required
def query():
    query = request.get_data(as_text=True)
    refresh = request.args.get('refresh', None)
    b_async = request.args.get('b_async', None)

    log_action('query', query)
    try:
        start_time = time.time()
        livy = LivyClient(refresh=refresh, b_async=b_async)
        done, output_folder = livy.execute_query(query)
        app.logger.info("Query execution finished")
        statsd.timing('query_time', int(time.time() - start_time))

        def stream_results():
            # Concatenate, and send generated files:
            total_bytes = 0
            start_time = time.time()
            files = list(list_files(output_folder, suffix='.json.gz'))
            app.logger.info("Amount of files in output: {}".format(len(files)))
            for output_file in files:
                fh = read_file(output_file)
                while True:
                    chunk = fh.read(8192)
                    app.logger.info("chunk size: {}".format(len(chunk)))
                    yield chunk
                    bytes_sent = len(chunk)
                    total_bytes += bytes_sent
                    if bytes_sent <= 0:
                        break
            statsd.timing('transfer_time', int(time.time() - start_time))
            app.logger.info("Total bytes sent: {}".format(total_bytes))
            statsd.increment('total_bytes', total_bytes)

        if done:
            response = Response(stream_results(), mimetype='application/json')
            response.headers['Content-Encoding'] = 'gzip'
            app.logger.info("File Sent")
        else:
            response = Response("Query is processing...", mimetype='text/plain', status=206)
            app.logger.info("Query is processing...")

    except Exception as e:
        app.logger.exception('Error processing query')
        statsd.increment('errors', 1)
        response = Response(
            str(e),
            mimetype='text/plain',
            status=422 if isinstance(e, StatementError) else 500)

    return response

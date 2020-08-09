from datadog.dogstatsd.base import DogStatsd

from .app import app

statsd = DogStatsd(
    namespace='dataplate.data.dataaccess',
    constant_tags=[],
    host=app.config['STATSD_HOST'],
    port=8125)

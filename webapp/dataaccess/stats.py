from datadog.dogstatsd.base import DogStatsd

from .app import app


class DummyStatsd(object):
    def timing(self, *args, **kwargs):
        pass

    def increment(self, *args, **kwargs):
        pass


if 'STATSD_HOST' in app.config:
    statsd = DogStatsd(namespace=app.config.get('STATSD_NAMESPACE',
                                                'dataplate.dataaccess'),
                       constant_tags=[],
                       host=app.config['STATSD_HOST'],
                       port=int(app.config.get('STATSD_PORT', '8125')))
else:
    statsd = DummyStatsd()

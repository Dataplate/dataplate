import os


class Config:
    VERSION = 'dev'

    ENV = os.environ.get('ENV', 'dev')

    DB_ENDP = os.environ['DB_ENDP']
    DB_NAME = os.environ['DB_NAME']
    DB_USER = os.environ['DB_USER']
    DB_PASS = os.environ['DB_PASS']
    SECRET_KEY = os.environ['SECRET_KEY']

    SQLALCHEMY_DATABASE_URI = 'postgresql+psycopg2://{user}:{pw}@{url}/{db}'.format(
        user=DB_USER, pw=DB_PASS, url=DB_ENDP, db=DB_NAME)
    if 'SQLALCHEMY_ECHO' in os.environ:
        SQLALCHEMY_ECHO = True
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    OUTPUT_PATH = os.environ.get('OUTPUT_PATH', None)
    STATSD_HOST = os.environ.get('STATSD_HOST', '127.0.0.1')

    PREFERRED_URL_SCHEME = os.environ.get('PREFERRED_URL_SCHEME', None)

    PANOPTICON_URL = 'http://ppp.eu-west-1-dev-vpc-data.eu-west-1.rnd.here.internal' \
            if ENV == 'dev' else 'http://pp.eu-west-1-prod-data.eu-west-1.prd.here.internal'


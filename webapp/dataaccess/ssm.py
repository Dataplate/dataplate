import boto3
from botocore.exceptions import ClientError


class SSM(object):
    _cache = {}

    def __init__(self):
        self.client = boto3.client('ssm')

    def get_parameter(self, name):
        if not name in SSM._cache:
            try:
                SSM._cache[name] = self.client.get_parameter(
                    Name=name, WithDecryption=True)['Parameter']['Value']
            except ClientError as e:
                if e.response['Error']['Code'] != 'ParameterNotFound':
                    raise
                SSM._cache[name] = 'SSM Parameter Not Found'
        return SSM._cache[name]

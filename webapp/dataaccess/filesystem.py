import boto3
from botocore.exceptions import ClientError


def file_exists(path):
    """
    Check whether specified path exists on the target filesystem.

    Parameters
    ----------
    path : str
        Full path to a file/folder on the target file system.
    """
    s3 = boto3.client('s3')
    kwargs = {
        'Bucket': path.split('/')[2],
        'Key': '/'.join(path.split('/')[3:])
    }
    try:
        s3.head_object(**kwargs)
        return True
    except ClientError as e:
        if e.response['Error']['Code'] == '404':
            return False
        raise e


def list_files(path, suffix='', recursively=True):
    """
    List files under specified path.

    Parameters
    ----------
    path : str
        Full path to the folder on target file system.
    suffix : str
        Filter results that end with this suffix
    recursively : boolean
        Whether to only list first level or all levels recursively (default: True)

    Returns
    -------
    Generated paths for the found files
    """
    s3 = boto3.client('s3')
    if not recursively and not path.endswith('/'):
        path += '/'
    kwargs = {
        'Bucket': path.split('/')[2],
        'Prefix': '/'.join(path.split('/')[3:]),
    }
    if not recursively:
        kwargs['Delimiter'] = '/'
    while True:
        resp = s3.list_objects_v2(**kwargs)
        if 'Contents' in resp:
            for obj in resp['Contents']:
                key = obj['Key']
                if key.endswith(suffix):
                    yield 's3://{}/{}'.format(kwargs['Bucket'], key)
        elif 'CommonPrefixes' in resp:
            for obj in resp['CommonPrefixes']:
                prefix = obj['Prefix']
                if prefix.endswith(suffix):
                    yield 's3://{}/{}'.format(kwargs['Bucket'], prefix)
        try:
            kwargs['ContinuationToken'] = resp['NextContinuationToken']
        except KeyError:
            break


def read_file(path):
    """
    Reads file on a target file system.

    Parameters
    ----------
    path : str
        Path on a target file system.

    Returns
    -------
    Stream for the file contents.
    """
    s3 = boto3.client('s3')
    kwargs = {
        'Bucket': path.split('/')[2],
        'Key': '/'.join(path.split('/')[3:])
    }
    return s3.get_object(**kwargs)['Body']

DataPlate - Python Data Access API
===================================

## Installation
pip install dataplate

## Usage
First:

Install [DataPlate Portal Web service](./../webapp/README.md) and navigate to "API Documentation" for usage instructions

**More details:**

DataPlate() constructor accepts the following parameters:

env - Environment to retrieve the Data from ('dev' or 'prd').
access_key - Alternative method for supplying your access key.
dataplate_ur - Alternative method for supplying DataPlate Portal URI.

Get the access key from Dataplate Web-service portal (Nagivateto private access key):

<img src="https://user-images.githubusercontent.com/69418989/102617781-61d61880-4142-11eb-9df1-1695e9d5217d.png" width="50%" height="50%">

This example shows how to run a query, and return results as Pandas DataFrame object:

```
from dataplate.client import DataPlate

dataplate = DataPlate()
df = dataplate.query_to_df('''
SELECT * FROM myTable WHERE `date`='20200218' AND hour=12
''')
```
For more instructions, please refer to the [DataPlate Github](https://github.com/Dataplate)
DataPlate - Data Access Portal
=================================

Web service and API that provides audited access to Data sets.


## Deployment

 Deployed as standard ECS service.

## Schema Evolution

 1. Modify `models.py`
 2. Run: `make migrate`

## Running Locally
Use venv:
```
python3 -mvenv venv
source venv/bin/activate
pip install -r requirements.txt
```

Login to AWS
```
. aprofile rnd
. arole rnd User <MFA Code>
$(aws ecr get-login --no-include-email --region eu-west-1)
```
Install `stunnel` by `brew install stunnel`
Create a config file anywhere you please:
```
[dev]
client=yes
accept=127.0.0.1:8888
connect=squid-proxy.eu-west-1-dev-vpc-rnd.aws.in.dataaccess.com:443
```
Run `stunnel` as follows: `stunnel <config_file>`

Note: To kill `stunnel` just kill its process `ps -ef | grep stunnel` and then 
`kill <pid>`.

Update proxy credentials environment variables by:
`export PROXY_USER=<your_user_name>`
`export PROXY_PASS=<your_url_encoded_password>`

Please note that special characters in the password should be url encoded (% notation)
for example the character '@' is '%40'.

Run `make run`

## Windows
install LDAP for windows , go to libexec directory and double click the entry StartLDAP.cmd which immediately starts the LDAP Server.
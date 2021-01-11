DataPlate - Data Access Portal
=================================

A Web platform and API that provides monitoring & audited access to Data sets on S3/Parquet/Glue/CSVs/Redshift and more,
utilizing the power of AWS EMR spark.

You can install this web-service locally or remotely (on EC2 machine or on EMR Master node or Sagemaker machine)

Before installation :

* If you intend to install the platform on a remote machine: Make sure you have access to your machine via ssh (ask your devops to enable ssh tunneling or allow your VPN to access all needed machine ports)
* Make sure your AWS EMR (or Azure) has Livy enabled (we recommend EMR 5.3.1+)
![alt text](./dataaccess/static/img/livy_EMR_comp.png?raw=true)
* Make sure you have "docker" and "docker-compose" installed on your target web-server machine (in case of the recommended docker installation):
  
  Install docker on AWS instance (connect via ssh to the machine):
    ```bash
    sudo yum update -y
    sudo amazon-linux-extras install docker
    sudo curl -L https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m) -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
    docker-compose version
    sudo service docker start
    sudo usermod -a -G docker ec2-user (NOTE: ec2-user can be “hadoop” for emr)
    sudo docker info
    # Now wait a minute for the machine to reboot and connect again (ssh)
    sudo groupadd docker
    sudo usermod -a -G docker ${USER}
    sudo chkconfig docker on
    Logout from the machine ($ exit)
    Login again
  ```

## Installation

1. git clone https://github.com/Dataplate/dataplate.git (or copy the webapp code to a local folder on the target machine)
2. cd ./dataplate/webapp (make sure the docker-compose.yml is located there)
3. Now choose **docker-compose** or **venv** option bellow (we recommend docker-compose)
5. After the installation go to http://YOUR-IP:5000 (you can change the port in the docker-compose.yml)
6. In the web platform Navigate to the System Configuration and add your Livy URL (usually on port 8998) and set Output Path to an S3 path
<img src="https://user-images.githubusercontent.com/69418989/102617755-584cb080-4142-11eb-9744-0e7336b81ddf.png" width="50%" height="50%">
7. First time connect to the system using the user: demo@dataplate.io , password: demo , after first login you can add/remove/edit users manually or 
connect your LDAP by specifying DA_LOGIN_BACKEND=ldap in the docker-compose.yml or when create&run you DB via venv 
   
### Using docker-compose

**This is the recommended option !**
 
(you can alter the parameters ,such as DA_LOGIN_BACKEND=ldap for ldap integration or ports in the docker-compose.yml)

```bash
$ cd YOUR_WEBAPP_FOLDER_WITH_docker-compose.yml
$ chmod +x entrypoint.sh
$ sudo service docker start (make sure docker is running)
$ which docker-compose (find where the command is located if you need to use "sudo", usually the output is /usr/local/bin/docker-compose)
$ sudo systemctl restart docker

Forground run (see the run logs):
--------------
$ sudo /usr/local/bin/docker-compose -f docker-compose.yml up --build

Background run (you can access the run logs later via "docker-compose logs -f")
--------------
$ sudo TMPDIR=$(pwd) /usr/local/bin/docker-compose -f docker-compose.yml up -d --build

Errors Notes: In case you get "INTERNAL ERROR: cannot create temporary directory!", then run (specify tmp folder for the docker image):
TMPDIR=$(pwd) docker-compose -f docker-compose.yml up -d --build
```

Open your browser at http://localhost:5000 and use demo@dataplate.io / demo combination for logging in.

### Using venv

**This option is useful for debugging.**

First, you must have PostgreSQL up and running. This can be achieved easily using Docker:

```bash
docker run --rm -ti -e POSTGRES_USER=da -e POSTGRES_PASSWORD=da -e POSTGRES_DB=da -p 5432:5432 postgres:12.4
```

**Prepare the virtual environment:**

Note:
Before the pip install ,in case of MAC, make sure that you have postgresql (brew install postgresql) for pg_config executable
and have openssl installed and run:
_$ export LDFLAGS="-L/usr/local/opt/openssl/lib" and 
$ export CPPFLAGS="-I/usr/local/opt/openssl/include"_
```bash
python3 -mvenv venv
source venv/bin/activate
pip install -r requirements.txt
```

**Create database schema:**

DA_LOGIN_BACKEND parameter options: demo/ldap, specify manual user management "demo" or using ldap to manage users and groups "ldap"
```bash
DA_SECRET_KEY=BcmbPqfA6os9-5kdajQPUA \
DA_SQLALCHEMY_DATABASE_URI=postgresql://da:da@localhost/da \
DA_LOGIN_BACKEND=demo \
FLASK_APP=dataaccess.app \
flask db upgrade
```

**Run the application:**

DA_LOGIN_BACKEND parameter options: demo/ldap, specify manual user management "demo" or using ldap to manage users and groups "ldap"

```bash
DA_SECRET_KEY=BcmbPqfA6os9-5kdajQPUA \
DA_SQLALCHEMY_DATABASE_URI=postgresql://da:da@localhost/da \
DA_LOGIN_BACKEND=demo \
FLASK_APP=dataaccess.app \
flask run
```

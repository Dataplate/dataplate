![TBackground-rectSmallNoslogen](https://user-images.githubusercontent.com/69418989/102619767-a1523400-4145-11eb-8855-2c292daf16b2.png)
========================

Dataplate is a monitoring and another security layer that enable data-scientists to do data exploration easier utilize hybrid approach (using AWS EMR spark scaling while research on your local machine),

This approach enable to preserving safe data research using [Differential Privacy](https://en.wikipedia.org/wiki/Differential_privacy) that enable to monitor data access, while provide the necessary research freedom.

The platform comprises of a webPlatform to monitor & define data access roles and a pypi (pip) library to install locally.

The Web Server is a bridge between your Jupyter/python code and your Livy component of AWS EMR-master/Livy-machine/SageMaker-machine utilizing Apache Livy protocols

## Installation

You can install the dataplate web-service locally or remotely (on EC2 machine or on EMR Master node or Sagemaker machine)

Before installation :

* If you intend to install the platform on a remote machine: Make sure you have access to your machine via ssh (ask your devops to enable ssh tunneling or allow your VPN to access all needed machine ports)
* Make sure your EMR has Livy enabled (we recommend EMR 5.3.1+)

1. Install the [DataPlate web server](webapp/README.md) on your machine
2. In your Local Jupyter (lab/notebook) use [DataPlate python package](api/README.md)

## Projects

[Data Access Portal Web service](webapp/README.md)   

[Data Access API](api/README.md)   

## Architecture
![alt text](./webapp/dataaccess/static/img/DataplateArch_v1.png?raw=true)
![TBackground-rectSmallNoslogen](https://user-images.githubusercontent.com/69418989/102619767-a1523400-4145-11eb-8855-2c292daf16b2.png)
========================

**This is our open-source solution for Data Access only**

**For our full Saas solution visit our website: https://dataplate.io**

**Why do you need DataPlate ?**

Data-scientists/analysts love notebooks and love using it locally, to easily try various models and algorithms without messing the production.

However, there are times that the data is too big and we need clusters to process data (we love spark).

So, we use notebooks on the cloud, although it might have connection & kernel & auto-complete issues.

We then process the data and still download some data to our local machine for comfortable research.

But wait! the data can contain private data and this process might cause a data breach :-o
 
So, you can use your devops team to define policies,roles and users ,but they're always busy and you'd like more control over your data team.

 
**What is it?**

DataPlate will enable you to continue the same local-remote (hybrid) research while monitoring data access and easily define who can access what, via an easy to use web service ,that is a bridge between your local IDE/Notebooks and your remote cluster.

**see the [Architecture](#Architecture) diagram**

This approach enable safer data access using [Differential Privacy](https://en.wikipedia.org/wiki/Differential_privacy) that enable to monitor data access, while provide the necessary research freedom.

The platform comprises of a web-service to monitor & define data access roles and a pypi (pip) library to install on your notebook/IDE.

Our Web Service is a bridge between your Jupyter/python local/remote notebook and your remote Cluster (like: Amazon EMR, Azure Cluster)

### Benefits for Data-Scientists and Analysts

We enable a hybrid approach for data exploration 

Use your favorite local/remote notebooks and the scale of a remote computing cluster (AWS/Azure).

All from the same notebook/IDE ,while every data access is monitored and recorded for safe data access, which also enable easy code sharing with your team

### Benefits for Security-Operations Engineers

Managing Data access is complicated! it requires to define different roles and policies in multiple platforms of data (e.g AWS accounts) and requires log monitoring

DataPlate data access is simple! one place to monitor and define it all and using the same LDAP/ActiveDirectory users and groups of your organization

**Security Benefits:**

* Full LDAP integration for users and groups (using the username/email to query the audit log of accessing data)
* High security control granularity, that comply to the given permission role defined in the system
* This security layer prevent direct browsing capabilities ,like s3 browser to list\view\delete\move files
* Access only to the relevant and needed data in a table-like formation
* Deep investigation capabilities in case of a data-breach

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

# Architecture
![alt text](./webapp/dataaccess/static/img/DataplateArch_v2.png?raw=true)
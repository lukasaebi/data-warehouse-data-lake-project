# Deploying AWS Lambda Functions with Container Images

**Important Documentation**:
* Understand key Lambda concepts: https://docs.aws.amazon.com/lambda/latest/dg/gettingstarted-concepts.html#gettingstarted-concepts-dp
* Deploy Python Lambda functions with container images: https://docs.aws.amazon.com/lambda/latest/dg/python-image.html#python-image-instructions
* Use Lambda environment variables to configure values in code: https://docs.aws.amazon.com/lambda/latest/dg/configuration-envvars.html
* Manage Lambda function versions: https://docs.aws.amazon.com/lambda/latest/dg/configuration-versions.html
* Managing Lambda dependencies with layers: https://docs.aws.amazon.com/lambda/latest/dg/chapter-layers.html

____

This document contains step-by-step instructions on how to deploy AWS Lambda functions using docker images.

> Attention: Ubuntu WSL2 is assumed as OS. If you use MacOS, Windows, or any other Linux distribution, commands could differ.

Please execute the following steps one by one. If you already have a resource or programm installed, skip to the next step.

### 1. Install WSL2


### 2 Install Docker on WSL2


### 3. Install the AWS CLI
To install the AWS CLI open your Ubuntu terminal by pressing the Windows key and typing 'Ubuntu'. Then copy, paste, and execute the following command into the terminal:
```bash
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install
```
The execution of this command could take some minutes, since the AWS CLI is quite a large package.

#### 3.1 Check if AWS CLI is installed properly
```bash
aws --version
```
This should return something similar to this:
```bash
aws-cli/2.18.15 Python/3.12.6 Linux/5.15.133.1-microsoft-standard-WSL2 exe/x86_64.ubuntu.22
```

### 4. Configure your AWS Credentials
Next, you have to configure the credentials of your AWS account so that you can actually use the CLI on your account resources (Lambda Functions, Databases, etc.).

For this, you have to start your preferred AWS Learner Lab under `https://awsacademy.instructure.com/courses/`. Under Modules > Learner Lab click on `Start Lab` in the top right corner. Then, click on `AWS Details` and on the `Show` button next to `AWS CLI`. These are your account-specific credentials. 
```txt
[default]
aws_access_key_id=1234567890
aws_secret_access_key=1234567890
aws_session_token=1234567890
```
Copy the whole thing and paste it into a file under ~/.aws/credentials. You can do this with:
```bash
nano ~/.aws/credentials
```
Then, press `Ctrl V`, `Enter`, `Ctrl X`, `Enter`.

To check whether everything has worked as expected, execute:
```bash
cat ~/.aws/credentials
```
This should lists the content of the file.

> Unfortunately this step of copying your AWS Credentials must be executed EVERY TIME your restart a lab session. The reason for this is that we have educational accounts and our secrets (the one's you copied) change with every restart. With real AWS accounts, this has to be done just once.

# 5. 
# Setting Up the Infrastructure

<details>
<summary>Deploying AWS Lambda Functions with Container Images</summary>

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
Follow this guide for installing WSL2: https://www.windowscentral.com/how-install-wsl2-windows-10
When the installation is finished, you can press the window button and type 'Ubuntu' to open your Linux terminal.

### 2 Install Docker
To install Docker follow this documentation: https://docs.docker.com/desktop/wsl/
It will install Docker Desktop on Windows using WSL2 as its backend. The part from 'Enabling Docker support in WSL 2 distros' is not needed.

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
bash update_aws_credentials.sh
```
Follow the instructions in the command line.

To check whether everything has worked as expected, execute:
```bash
cat ~/.aws/credentials
```
This lists the content of the file you just edited.

> Unfortunately this step of copying your AWS Credentials must be executed EVERY TIME your restart a lab session. The reason for this is that we have educational accounts and our secrets (the one's you copied) change with every restart. With real AWS accounts, this has to be done just once.

### 5. Create Directory with you Lambda Function logic
Create your own lambda function logic by creating a directory in `lambda_functions`, on the same level as this README. Name it after your API, you will reuse the name in the next step. Bare minimum setup you need to have for this is:
* **Dockerfile** containing all the dependencies of your Lambda function. Copy the `Dockerfile.template` in your directory, rename it to just `Dockerfile` and potentially add additional steps.
* **Python file** containing the execution logic of you Lambda function.
    * Attention: The filename and the function name containing the logic must be filled in the CMD command in the Dockerfile.
* **requirements.txt** containing the dependencies needed to run your python file

### 6. Create or Update your Lambda Function
To create or update Lambda functios run the following command from the root of the project (i.e. the `data-warehouse-data-lake-project` directory):
```bash
bash lambda_functions/create_or_update_lambda_function.sh <LAMBDA_DIR> <LAMBDA_FUNCTION_NAME> <AWS_ECR_REPOSITORY> (<DOCKER_IMAGE_NAME>)
```
The values within the <> should be replaced by your actual values.

Parameters:
* **LAMBDA_DIR**: The path to the directory of your lambda function from the `lambda_functions/create_or_update_lambda_function.sh` file. I.e. if your lambda function resides in `lambda_functions/some_api/some_lambda_function` you should pass `some_api/some_lambda_function`.
* **LAMBDA_FUNCTION_NAME**: Name of your lambda function in AWS.
* **AWS_ECR_REPOSITORY** (Optional): This is the repository name in your container registry. The repository will be created when you run the `lambda_functions/create_or_update_lambda_function.sh` script. Normally, it makes sense to have a repository per docker image. Therefore, it takes on the value of `LAMBDA_FUNCTION_NAME` by default. If there is no legit reason to use another name, don't provide this parameter.
* **DOCKER_IMAGE_NAME** (Optional): Name that your docker image should have. Doesn't really matter, but choose something meaningful like <name-of-lambda-function>. If not set, defaults to `LAMBDA_FUNCTION_NAME`.

> Deprecated: **AWS_ACCOUNT_ID** is NOT needed anymore! Was needed in an earlier version.
</details>

<details>
<summary>Creating Schedules for Lambda Functions</summary>
Creating regular schedules for lambda functions consists of three different steps.

1. **Event Rules** define the interval with which the function should be scheduled.
2. **Permissions** define the actions that can be executed at the specified interval in the event rules.
3. **Targets** connect the rule and the permission to the desired Lambda function.

The bash script at `lambda_functions/setup_lambda_functions_schedule.sh` goes through all these steps sequentially and implements the following:

1. Creates event rule for scheduling some lambda function to run daily 9:05 AM UTC in November and December (rule is called `DailyLambdaTrigger`).
2. Permission created to invoke the Lambda function with the schedule defined in step 1.
3. Specifies the lambda function that should be triggered with the rule from step 1.

To schedule your Lambda function run:
```bash
bash lambda_functions/setup_lambda_function_schedule.sh <FUNCTION_NAME>
```

The script contains the following logic, represented with pseudo-python code.

```python
if event_rule exists:
    skip
else:
    create event_rule()

if permission for function_name exists:
    skip
else:
    add_permissions_to_function()

if target for function_name exists:
    skip
else:
    define_target_function()
```
</details>
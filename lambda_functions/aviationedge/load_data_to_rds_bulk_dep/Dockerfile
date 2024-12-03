# Base image for Python 3.11 AWS Lambda
FROM public.ecr.aws/lambda/python:3.11

# Upgrade pip to the latest version
RUN pip install --upgrade pip

# Copy requirements.txt and install dependencies
COPY requirements.txt ${LAMBDA_TASK_ROOT}/
RUN pip install -r ${LAMBDA_TASK_ROOT}/requirements.txt

# Copy the application code and configuration files
COPY aviations3_to_rds.py ${LAMBDA_TASK_ROOT}/
COPY config.yaml ${LAMBDA_TASK_ROOT}/

# Set the default handler for the Lambda function
CMD ["aviations3_to_rds.main"]
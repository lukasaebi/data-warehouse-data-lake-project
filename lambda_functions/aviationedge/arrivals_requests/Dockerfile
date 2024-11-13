# Dockerfile for Parent Lambda
FROM public.ecr.aws/lambda/python:3.12

# Copy requirements.txt
COPY requirements.txt ${LAMBDA_TASK_ROOT}

# Install the specified packages
RUN pip install -r requirements.txt

# Copy the parent Lambda function
COPY parent_arrivals_lambda.py ${LAMBDA_TASK_ROOT}

# Set the CMD to the parent lambda handler
CMD ["parent_arrivals_lambda.lambda_handler"]
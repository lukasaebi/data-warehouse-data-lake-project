# Dockerfile for Lambda Function
FROM public.ecr.aws/lambda/python:3.12

# Copy requirements.txt
COPY requirements.txt ${LAMBDA_TASK_ROOT}

# Install the specified packages
RUN pip install -r requirements.txt

# Copy function code
COPY process_s3_to_rds.py ${LAMBDA_TASK_ROOT}

# Set CMD to Lambda handler
CMD ["process_s3_to_rds.lambda_handler"]


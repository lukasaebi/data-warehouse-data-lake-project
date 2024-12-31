# Dockerfile for Zurich Lambda Function
FROM public.ecr.aws/lambda/python:3.12

# Copy requirements.txt
COPY requirements.txt ${LAMBDA_TASK_ROOT}

# Install the specified packages
RUN pip install -r requirements.txt

# Copy function code and config file for Zurich
COPY zurich_departure_lambda.py ${LAMBDA_TASK_ROOT}
COPY config.yaml ${LAMBDA_TASK_ROOT}

# Set CMD to Zurich's lambda handler
CMD ["zurich_departure_lambda.lambda_handler"]


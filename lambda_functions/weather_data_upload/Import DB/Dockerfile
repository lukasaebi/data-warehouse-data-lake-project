FROM public.ecr.aws/lambda/python:3.12

# Copy requirements.txt
COPY requirements.txt ${LAMBDA_TASK_ROOT}

# Install the specified packages
RUN pip install -r requirements.txt

# Copy function code
COPY import_s3_to_postgres.py ${LAMBDA_TASK_ROOT}


COPY config.json ${LAMBDA_TASK_ROOT}


# Set the CMD to your handler (could also be done as a parameter override outside of the Dockerfile)
CMD [ "import_s3_to_postgres.lambda_handler" ]
# Stage 1
FROM public.ecr.aws/lambda/python:3.11

# Copy requirements.txt
COPY requirements.txt ${LAMBDA_TASK_ROOT}

# Install the specified packages
RUN pip install -r requirements.txt

# Copy function code
COPY aviations3_to_rds_daily.py ${LAMBDA_TASK_ROOT}

# Copy config file
COPY config.yaml ${LAMBDA_TASK_ROOT}

# Set the CMD to your handler
CMD [ "aviations3_to_rds_daily.lambda_handler" ]
# Use the AWS Lambda Python runtime base image
FROM public.ecr.aws/lambda/python:3.12

# Copy the requirements file
COPY requirements.txt /var/task/

# Install Python dependencies using pip
RUN pip install --no-cache-dir -r requirements.txt

# Copy the function code
COPY aviations3_to_rds.py /var/task/

# Set the CMD to the Lambda function handler
CMD ["aviations3_to_rds.lambda_handler"]
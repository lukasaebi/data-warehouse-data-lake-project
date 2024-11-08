#!/bin/bash

# Prerequisites:
# 1. AWS CLI must be installed and configured
# 2. Docker must be installed
# 3. FUNCTION_NAME must be the name of the file without the extension

set -e

# Arguments
LAMBDA_DIR=$1
LAMBDA_FUNCTION_NAME=$2
ECR_REPOSITORY_NAME=${3:-$LAMBDA_FUNCTION_NAME}
DOCKER_IMAGE_NAME=${4:-$LAMBDA_FUNCTION_NAME}

# Retrieve AWS Account ID
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

# Build the Docker image
echo "Building the Docker image..."
docker build --platform linux/amd64 -t $DOCKER_IMAGE_NAME $LAMBDA_DIR
echo "Docker image built."

# Authenticate to Amazon ECR (Container Registry)
echo "Authenticating to Amazon ECR..."
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin $AWS_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com
echo "Authenticated to Amazon ECR with username=AWS & password-stdin=$AWS_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com."

# Create Repository in Amazon ECR IF NOT EXISTS
echo "Creating repository in Amazon ECR if it does not exist..."
if aws ecr describe-repositories --repository-names "$ECR_REPOSITORY_NAME" > /dev/null 2>&1; then
    echo "Repository $ECR_REPOSITORY_NAME already exists."
else
    echo "Repository $ECR_REPOSITORY_NAME does not exist. Creating repository..."
    aws ecr create-repository --repository-name "$DOCKER_IMAGE_NAME"
    echo "Repository $DOCKER_IMAGE_NAME created."
fi

# Tag the Docker image
echo "Tagging the Docker image..."
docker tag $DOCKER_IMAGE_NAME:latest $AWS_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/$ECR_REPOSITORY_NAME:latest

# Push the Docker image to Amazon ECR
echo "Pushing the Docker image $DOCKER_IMAGE_NAME to Amazon ECR..."
docker push $AWS_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/$ECR_REPOSITORY_NAME:latest
echo "Docker image $DOCKER_IMAGE_NAME successfully pushed to Amazon ECR."

# Create or Update the Lambda Function
if aws lambda get-function --function-name $LAMBDA_FUNCTION_NAME > /dev/null 2>&1; then
  echo "Lambda function $LAMBDA_FUNCTION_NAME already exists. Updating the Lambda function..."
  aws lambda update-function-code \
    --function-name $LAMBDA_FUNCTION_NAME \
    --image-uri $AWS_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/$ECR_REPOSITORY_NAME:latest \
    --publish \
    --no-cli-pager
  echo "Lambda function $LAMBDA_FUNCTION_NAME successfully updated."
else
  echo "Lambda function $LAMBDA_FUNCTION_NAME does not exist yet. Creating the Lambda function..."
  aws lambda create-function \
    --function-name $LAMBDA_FUNCTION_NAME \
    --package-type Image \
    --code ImageUri=$AWS_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/$ECR_REPOSITORY_NAME:latest \
    --role arn:aws:iam::$AWS_ACCOUNT_ID:role/LabRole \
    --no-cli-pager
  echo "Lambda function $LAMBDA_FUNCTION_NAME successfully created."
fi

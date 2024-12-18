#!/bin/bash

# Prerequisites:
# 1. AWS CLI must be installed and configured
# 2. Docker must be installed
# 3. FUNCTION_NAME must be the name of the file without the extension

set -e

# Arguments
LAMBDA_DIR=$1
LAMBDA_FUNCTION_NAME=$2
AWS_ACCOUNT_ID=$3
AWS_ECR_REPOSITORY=$4
DOCKER_IMAGE_NAME=${5:-$LAMBDA_FUNCTION_NAME}

# Build the Docker image
docker build --platform linux/amd64 -t $DOCKER_IMAGE_NAME $LAMBDA_DIR

# Authenticate to Amazon ECR (Container Registry)
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin $AWS_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com

# Create Repository in Amazon ECR IF NOT EXISTS
aws ecr describe-repositories --repository-names $AWS_ECR_REPOSITORY > /dev/null 2>&1 || aws ecr create-repository --repository-name $DOCKER_IMAGE_NAME

# Tag the Docker image
docker tag $DOCKER_IMAGE_NAME:latest $AWS_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/$AWS_ECR_REPOSITORY:latest

# Push the Docker image to Amazon ECR
docker push $AWS_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/$AWS_ECR_REPOSITORY:latest

# Define the AWS region
AWS_REGION="us-east-1"

# Create or Update the Lambda Function
if aws lambda get-function --function-name $LAMBDA_FUNCTION_NAME --region $AWS_REGION > /dev/null 2>&1; then
  # Update existing Lambda function
  aws lambda update-function-code \
    --function-name $LAMBDA_FUNCTION_NAME \
    --image-uri $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$AWS_ECR_REPOSITORY:latest \
    --publish \
    --region $AWS_REGION
else
  # Create new Lambda function
  aws lambda create-function \
    --function-name $LAMBDA_FUNCTION_NAME \
    --package-type Image \
    --code ImageUri=$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$AWS_ECR_REPOSITORY:latest \
    --role arn:aws:iam::$AWS_ACCOUNT_ID:role/LabRole \
    --region $AWS_REGION
fi

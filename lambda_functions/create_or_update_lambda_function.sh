#!/bin/bash

set -e

# Arguments
LAMBDA_DIR=$1
LAMBDA_FUNCTION_NAME=$2
TIMEOUT=${3:-60}
ECR_REPOSITORY_NAME=${4:-$LAMBDA_FUNCTION_NAME}
DOCKER_IMAGE_NAME=${5:-$LAMBDA_FUNCTION_NAME}

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
echo "Creating repository $ECR_REPOSITORY_NAME in Amazon ECR if it does not exist..."
if aws ecr describe-repositories --repository-names "$ECR_REPOSITORY_NAME" > /dev/null 2>&1; then
    echo "Repository $ECR_REPOSITORY_NAME already exists."
else
    echo "Repository $ECR_REPOSITORY_NAME does not exist. Creating repository..."
    aws ecr create-repository \
      --repository-name "$ECR_REPOSITORY_NAME" \
      --no-cli-pager
    echo "Repository $ECR_REPOSITORY_NAME created."
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

# Path to the .env file
ENV_FILE="$LAMBDA_DIR/.env"

# Check if the .env file exists
if [ ! -f "$ENV_FILE" ]; then
    echo "WARNING: .env file not found! Environment variables cannot be uploaded!" \
    "To upload environment variables, create a .env file in the Lambda function directory."
else
    echo "Using .env file at: $ENV_FILE"

    # Convert the file to Unix line endings in case it has DOS line endings
    dos2unix "$ENV_FILE" 2>/dev/null

    # Build the Variables string for the AWS CLI command
    env_vars_string="Variables={"

    # Read each line in the .env file and append to env_vars_string
    while IFS='=' read -r key value || [ -n "$key" ]; do
        # Skip empty lines and comments
        if [ -n "$key" ] && [[ ! "$key" =~ ^# ]]; then
            env_vars_string+="$key=$value,"
        fi
    done < "$ENV_FILE"

    # Remove the trailing comma and close the curly brace
    env_vars_string="${env_vars_string%,}}"

    # Update Lambda function environment variables with retry logic
    echo "Updating Lambda function environment variables..."
    retry_count=0
    max_retries=6
    success=false

    set +e
    while [ $retry_count -lt $max_retries ]; do
        if [[ -f "$LAMBDA_DIR/lambda_config.json" ]]; then
            echo "sample_config.json exists in $LAMBDA_DIR. Configuration will be updated using it."
            if aws lambda update-function-configuration \
                --cli-input-json "file://$LAMBDA_DIR/lambda_config.json" \
                --environment "$env_vars_string" \
                --no-cli-pager > /dev/null 2>&1; then
                success=true
                break
            else
                echo "Failed to update environment variables. Lambda function not ready yet. Retrying in 5 seconds..."
                ((retry_count++))
                sleep 10
            fi
        else
            echo "sample_config.json does not exist in $LAMBDA_DIR. Configuration will not be updated."
            if aws lambda update-function-configuration \
                --function-name "$LAMBDA_FUNCTION_NAME" \
                --environment "$env_vars_string" \
                --no-cli-pager > /dev/null 2>&1; then
                success=true
                break
            else
                echo "Failed to update environment variables. Lambda function not ready yet. Retrying in 5 seconds..."
                ((retry_count++))
                sleep 10
            fi
        fi
    done

    set -e
    if [ "$success" = true ]; then
        echo "Lambda function environment variables successfully updated."
    else
        echo "ERROR: Failed to update Lambda function environment variables after multiple attempts."
    fi
fi

echo "All steps completed."

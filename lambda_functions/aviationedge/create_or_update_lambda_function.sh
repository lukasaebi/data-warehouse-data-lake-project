#!/bin/bash

# Prerequisites:
# 1. AWS CLI must be installed and configured
# 2. Docker must be installed
# 3. FUNCTION_NAME must be the name of the file without the extension


# Load global environment variables: For account / repo / apikey 
source .env

AWS_REGION="us-east-1"

# Function to create or update a Lambda function
create_or_update_lambda() {
    LAMBDA_DIR=$1
    CONFIG_FILE="$LAMBDA_DIR/lambda_config.json"
    ENV_FILE="$LAMBDA_DIR/.env"

    # Load environment variables for the Lambda function (API_KEY)
    if [[ -f "$ENV_FILE" ]]; then
        source "$ENV_FILE"
    fi

    # Load configuration from lambda_config.json
    LAMBDA_FUNCTION_NAME=$(jq -r '.FunctionName' "$CONFIG_FILE")
    TIMEOUT=$(jq -r '.Timeout' "$CONFIG_FILE")
    MEMORY_SIZE=$(jq -r '.MemorySize' "$CONFIG_FILE")

    # Define Docker image name and ECR repository
    DOCKER_IMAGE_NAME="${LAMBDA_FUNCTION_NAME}"
    ECR_REPOSITORY="${AWS_ECR_REPOSITORY_PREFIX}-${LAMBDA_FUNCTION_NAME}"

    # Build Docker image
    docker build --platform linux/amd64 -t "$DOCKER_IMAGE_NAME" "$LAMBDA_DIR"

    # Authenticate to Amazon ECR
    aws ecr get-login-password --region "$AWS_REGION" | docker login --username AWS --password-stdin "$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com"

    # Create ECR repository if it does not exist
    aws ecr describe-repositories --repository-names "$ECR_REPOSITORY" > /dev/null 2>&1 || aws ecr create-repository --repository-name "$ECR_REPOSITORY"

    # Tag and push the Docker image to Amazon ECR
    docker tag "$DOCKER_IMAGE_NAME:latest" "$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_REPOSITORY:latest"
    docker push "$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_REPOSITORY:latest"

    # Check if the Lambda function exists and create or update accordingly
    if aws lambda get-function --function-name "$LAMBDA_FUNCTION_NAME" --region "$AWS_REGION" > /dev/null 2>&1; then
        # Update existing Lambda function
        aws lambda update-function-code \
            --function-name "$LAMBDA_FUNCTION_NAME" \
            --image-uri "$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_REPOSITORY:latest" \
            --publish \
            --region "$AWS_REGION"
    else
        # Create new Lambda function
        aws lambda create-function \
            --function-name "$LAMBDA_FUNCTION_NAME" \
            --package-type Image \
            --code ImageUri="$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_REPOSITORY:latest" \
            --role "arn:aws:iam::$AWS_ACCOUNT_ID:role/LabRole" \
            --timeout "$TIMEOUT" \
            --memory-size "$MEMORY_SIZE" \
            --environment Variables="{API_KEY=${API_KEY}}" \
            --region "$AWS_REGION"
    fi
}

# Iterate over each city-specific Lambda directory in arrivals and departures
for LAMBDA_DIR in lambda_functions/aviationedge/arrivals_requests/* lambda_functions/aviationedge/departures_requests/*; do
    if [[ -d "$LAMBDA_DIR" ]]; then
        echo "Processing Lambda in directory: $LAMBDA_DIR"
        create_or_update_lambda "$LAMBDA_DIR"
    fi
done


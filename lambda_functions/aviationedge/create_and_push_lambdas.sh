#!/bin/bash

# Set AWS details
AWS_REGION="us-east-1"
AWS_ACCOUNT_ID="892760117705"
ROLE_ARN="arn:aws:iam::$AWS_ACCOUNT_ID:role/LabRole"
API_KEY=$(cat .env | grep API_KEY | cut -d '=' -f2) # Extract API_KEY from .env file

# List of cities
CITIES=("amsterdam" "dublin" "frankfurt" "lisbon" "london1" "london2" "madrid" "moscow" "paris" "rome" "vienna" "zurich")

# Base directory of the script
BASE_DIR="/home/carlo13/hslu/data-warehouse-data-lake-project/lambda_functions/aviationedge"

# Function to process each city
process_city() {
  CITY=$1
  ARRIVAL_LAMBDA_DIR="$BASE_DIR/arrivals_requests/${CITY}_arrival_lambda"
  DEPARTURE_LAMBDA_DIR="$BASE_DIR/departures_requests/${CITY}_departure_lambda"
  ARRIVAL_REPO_NAME="${CITY}-arrival-lambda-repo"
  DEPARTURE_REPO_NAME="${CITY}-departure-lambda-repo"

  # ARRIVAL LAMBDA
  echo "Processing arrival Lambda for city: $CITY"
  if [[ -d "$ARRIVAL_LAMBDA_DIR" ]]; then
    cd "$ARRIVAL_LAMBDA_DIR" || exit 1

    # Build Docker image for arrival Lambda
    docker build -t "$ARRIVAL_REPO_NAME" .

    # Tag and push to ECR for arrival Lambda
    docker tag "${ARRIVAL_REPO_NAME}:latest" "$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/${ARRIVAL_REPO_NAME}:latest"
    aws ecr get-login-password --region "$AWS_REGION" | docker login --username AWS --password-stdin "$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com"
    aws ecr describe-repositories --repository-names "$ARRIVAL_REPO_NAME" > /dev/null 2>&1 || aws ecr create-repository --repository-name "$ARRIVAL_REPO_NAME"
    docker push "$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/${ARRIVAL_REPO_NAME}:latest"

    # Create or update arrival Lambda
    if aws lambda get-function --function-name "${CITY}_arrival_lambda" --region "$AWS_REGION" > /dev/null 2>&1; then
      echo "Updating arrival Lambda for city: $CITY"
      aws lambda update-function-code --function-name "${CITY}_arrival_lambda" --image-uri "$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/${ARRIVAL_REPO_NAME}:latest" --region "$AWS_REGION"
      aws lambda update-function-configuration --function-name "${CITY}_arrival_lambda" --timeout 840 --memory-size 512 --environment Variables="{API_KEY=${API_KEY}}" --region "$AWS_REGION"
    else
      echo "Creating arrival Lambda for city: $CITY"
      aws lambda create-function \
        --function-name "${CITY}_arrival_lambda" \
        --package-type Image \
        --code ImageUri="$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/${ARRIVAL_REPO_NAME}:latest" \
        --role "$ROLE_ARN" \
        --timeout 840 \
        --memory-size 512 \
        --environment Variables="{API_KEY=${API_KEY}}" \
        --region "$AWS_REGION"
    fi

    cd - || exit 1
  else
    echo "Arrival directory for $CITY not found. Skipping..."
  fi

  # DEPARTURE LAMBDA
  echo "Processing departure Lambda for city: $CITY"
  if [[ -d "$DEPARTURE_LAMBDA_DIR" ]]; then
    cd "$DEPARTURE_LAMBDA_DIR" || exit 1

    # Build Docker image for departure Lambda
    docker build -t "$DEPARTURE_REPO_NAME" .

    # Tag and push to ECR for departure Lambda
    docker tag "${DEPARTURE_REPO_NAME}:latest" "$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/${DEPARTURE_REPO_NAME}:latest"
    aws ecr get-login-password --region "$AWS_REGION" | docker login --username AWS --password-stdin "$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com"
    aws ecr describe-repositories --repository-names "$DEPARTURE_REPO_NAME" > /dev/null 2>&1 || aws ecr create-repository --repository-name "$DEPARTURE_REPO_NAME"
    docker push "$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/${DEPARTURE_REPO_NAME}:latest"

    # Create or update departure Lambda
    if aws lambda get-function --function-name "${CITY}_departure_lambda" --region "$AWS_REGION" > /dev/null 2>&1; then
      echo "Updating departure Lambda for city: $CITY"
      aws lambda update-function-code --function-name "${CITY}_departure_lambda" --image-uri "$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/${DEPARTURE_REPO_NAME}:latest" --region "$AWS_REGION"
      aws lambda update-function-configuration --function-name "${CITY}_departure_lambda" --timeout 840 --memory-size 512 --environment Variables="{API_KEY=${API_KEY}}" --region "$AWS_REGION"
    else
      echo "Creating departure Lambda for city: $CITY"
      aws lambda create-function \
        --function-name "${CITY}_departure_lambda" \
        --package-type Image \
        --code ImageUri="$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/${DEPARTURE_REPO_NAME}:latest" \
        --role "$ROLE_ARN" \
        --timeout 840 \
        --memory-size 512 \
        --environment Variables="{API_KEY=${API_KEY}}" \
        --region "$AWS_REGION"
    fi

    cd - || exit 1
  else
    echo "Departure directory for $CITY not found. Skipping..."
  fi
}

# Process each city
for CITY in "${CITIES[@]}"; do
  process_city "$CITY"
done

echo "All Lambdas processed successfully."


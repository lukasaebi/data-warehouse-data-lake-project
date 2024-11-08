#!/bin/bash

set -e

BUCKET_NAME=$1

# Catch case where user not providing bucket name
if [ -z "$BUCKET_NAME" ]; then
    echo "Please provide a name for the S3 bucket"
    exit 1
# Catch underscores in bucket name
elif [[ $BUCKET_NAME == *"_"* ]]; then
    echo "Bucket names must not contain underscores!"
    exit 1
fi

echo "Creating a new S3 bucket with name: $BUCKET_NAME"

aws s3api create-bucket \
    --bucket "$BUCKET_NAME" \
    --region us-east-1

# Run with: bash path/to/create_bucket.sh <bucket-name>
#!/bin/bash

set -e

# Catch case where user not providing bucket name
if [ -z "$1" ]; then
    echo "Please provide a name for the S3 bucket"
    exit 1
# Catch underscores in bucket name
elif [[ $1 == *"_"* ]]; then
    echo "Bucket names must not contain underscores!"
    exit 1
fi

echo "Delete S3 bucket with name: $1"

aws s3api delete-bucket \
    --bucket "$1" \
    --region us-east-1

# Run with: bash path/to/delete_bucket.sh <bucket-name>
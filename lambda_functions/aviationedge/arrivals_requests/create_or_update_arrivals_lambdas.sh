#!/bin/bash

# Load environment variables from the .env file for API_KEY
source .env

# London_Part1
cd london1_arrival_lambda
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 871770651017.dkr.ecr.us-east-1.amazonaws.com
docker build -t aviation-arrivals-lambda-repo:london1 .
docker tag aviation-arrivals-lambda-repo:london1 871770651017.dkr.ecr.us-east-1.amazonaws.com/aviation-arrivals-lambda-repo:london1
docker push 871770651017.dkr.ecr.us-east-1.amazonaws.com/aviation-arrivals-lambda-repo:london1
# Check if the function exists
if aws lambda get-function --function-name london1_arrival_lambda > /dev/null 2>&1; then
    echo "Function london1_arrival_lambda already exists. Updating code only."
else
    # Create the function if it doesn't exist
    aws lambda create-function \
      --function-name london1_arrival_lambda \
      --package-type Image \
      --code ImageUri=871770651017.dkr.ecr.us-east-1.amazonaws.com/aviation-arrivals-lambda-repo:london1 \
      --role arn:aws:iam::871770651017:role/LabRole \
      --timeout 900 \
      --memory-size 512 \
      --environment Variables="{API_KEY=${API_KEY}}" \
      --region us-east-1
    # Wait for creation to complete
    sleep 10
fi

aws lambda update-function-code --function-name london1_arrival_lambda --image-uri 871770651017.dkr.ecr.us-east-1.amazonaws.com/aviation-arrivals-lambda-repo:london1

# Return to base directory
cd ..

# London_Part2
cd london2_arrival_lambda
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 871770651017.dkr.ecr.us-east-1.amazonaws.com
docker build -t aviation-arrivals-lambda-repo:london2 .
docker tag aviation-arrivals-lambda-repo:london2 871770651017.dkr.ecr.us-east-1.amazonaws.com/aviation-arrivals-lambda-repo:london2
docker push 871770651017.dkr.ecr.us-east-1.amazonaws.com/aviation-arrivals-lambda-repo:london2

# Check if the function exists
if aws lambda get-function --function-name london2_arrival_lambda > /dev/null 2>&1; then
    echo "Function london2_arrival_lambda already exists. Updating code only."
else
    aws lambda create-function \
      --function-name london2_arrival_lambda \
      --package-type Image \
      --code ImageUri=871770651017.dkr.ecr.us-east-1.amazonaws.com/aviation-arrivals-lambda-repo:london2 \
      --role arn:aws:iam::871770651017:role/LabRole \
      --timeout 900 \
      --memory-size 512 \
      --environment Variables="{API_KEY=${API_KEY}}" \
      --region us-east-1
    sleep 10
fi

aws lambda update-function-code --function-name london2_arrival_lambda --image-uri 871770651017.dkr.ecr.us-east-1.amazonaws.com/aviation-arrivals-lambda-repo:london2
cd ..


# Paris
cd paris_arrival_lambda
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 871770651017.dkr.ecr.us-east-1.amazonaws.com
docker build -t aviation-arrivals-lambda-repo:paris .
docker tag aviation-arrivals-lambda-repo:paris 871770651017.dkr.ecr.us-east-1.amazonaws.com/aviation-arrivals-lambda-repo:paris
docker push 871770651017.dkr.ecr.us-east-1.amazonaws.com/aviation-arrivals-lambda-repo:paris

if aws lambda get-function --function-name paris_arrival_lambda > /dev/null 2>&1; then
    echo "Function paris_arrival_lambda already exists. Updating code only."
else
    aws lambda create-function \
      --function-name paris_arrival_lambda \
      --package-type Image \
      --code ImageUri=871770651017.dkr.ecr.us-east-1.amazonaws.com/aviation-arrivals-lambda-repo:paris \
      --role arn:aws:iam::871770651017:role/LabRole \
      --timeout 900 \
      --memory-size 512 \
      --environment Variables="{API_KEY=${API_KEY}}" \
      --region us-east-1
    sleep 10
fi

aws lambda update-function-code --function-name paris_arrival_lambda --image-uri 871770651017.dkr.ecr.us-east-1.amazonaws.com/aviation-arrivals-lambda-repo:paris
cd ..


# Amsterdam
cd amsterdam_arrival_lambda
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 871770651017.dkr.ecr.us-east-1.amazonaws.com
docker build -t aviation-arrivals-lambda-repo:amsterdam .
docker tag aviation-arrivals-lambda-repo:amsterdam 871770651017.dkr.ecr.us-east-1.amazonaws.com/aviation-arrivals-lambda-repo:amsterdam
docker push 871770651017.dkr.ecr.us-east-1.amazonaws.com/aviation-arrivals-lambda-repo:amsterdam

if aws lambda get-function --function-name amsterdam_arrival_lambda > /dev/null 2>&1; then
    echo "Function amsterdam_arrival_lambda already exists. Updating code only."
else
    aws lambda create-function \
      --function-name amsterdam_arrival_lambda \
      --package-type Image \
      --code ImageUri=871770651017.dkr.ecr.us-east-1.amazonaws.com/aviation-arrivals-lambda-repo:amsterdam \
      --role arn:aws:iam::871770651017:role/LabRole \
      --timeout 900 \
      --memory-size 512 \
      --environment Variables="{API_KEY=${API_KEY}}" \
      --region us-east-1
    sleep 10
fi

aws lambda update-function-code --function-name amsterdam_arrival_lambda --image-uri 871770651017.dkr.ecr.us-east-1.amazonaws.com/aviation-arrivals-lambda-repo:amsterdam
cd ..


# Dublin
cd dublin_arrival_lambda
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 871770651017.dkr.ecr.us-east-1.amazonaws.com
docker build -t aviation-arrivals-lambda-repo:dublin .
docker tag aviation-arrivals-lambda-repo:dublin 871770651017.dkr.ecr.us-east-1.amazonaws.com/aviation-arrivals-lambda-repo:dublin
docker push 871770651017.dkr.ecr.us-east-1.amazonaws.com/aviation-arrivals-lambda-repo:dublin

if aws lambda get-function --function-name dublin_arrival_lambda > /dev/null 2>&1; then
    echo "Function dublin_arrival_lambda already exists. Updating code only."
else
    aws lambda create-function \
      --function-name dublin_arrival_lambda \
      --package-type Image \
      --code ImageUri=871770651017.dkr.ecr.us-east-1.amazonaws.com/aviation-arrivals-lambda-repo:dublin \
      --role arn:aws:iam::871770651017:role/LabRole \
      --timeout 900 \
      --memory-size 512 \
      --environment Variables="{API_KEY=${API_KEY}}" \
      --region us-east-1
    sleep 10
fi

aws lambda update-function-code --function-name dublin_arrival_lambda --image-uri 871770651017.dkr.ecr.us-east-1.amazonaws.com/aviation-arrivals-lambda-repo:dublin
cd ..


# Frankfurt
cd frankfurt_arrival_lambda
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 871770651017.dkr.ecr.us-east-1.amazonaws.com
docker build -t aviation-arrivals-lambda-repo:frankfurt .
docker tag aviation-arrivals-lambda-repo:frankfurt 871770651017.dkr.ecr.us-east-1.amazonaws.com/aviation-arrivals-lambda-repo:frankfurt
docker push 871770651017.dkr.ecr.us-east-1.amazonaws.com/aviation-arrivals-lambda-repo:frankfurt

if aws lambda get-function --function-name frankfurt_arrival_lambda > /dev/null 2>&1; then
    echo "Function frankfurt_arrival_lambda already exists. Updating code only."
else
    aws lambda create-function \
      --function-name frankfurt_arrival_lambda \
      --package-type Image \
      --code ImageUri=871770651017.dkr.ecr.us-east-1.amazonaws.com/aviation-arrivals-lambda-repo:frankfurt \
      --role arn:aws:iam::871770651017:role/LabRole \
      --timeout 900 \
      --memory-size 512 \
      --environment Variables="{API_KEY=${API_KEY}}" \
      --region us-east-1
    sleep 10
fi

aws lambda update-function-code --function-name frankfurt_arrival_lambda --image-uri 871770651017.dkr.ecr.us-east-1.amazonaws.com/aviation-arrivals-lambda-repo:frankfurt
cd ..


# Lisbon
cd lisbon_arrival_lambda
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 871770651017.dkr.ecr.us-east-1.amazonaws.com
docker build -t aviation-arrivals-lambda-repo:lisbon .
docker tag aviation-arrivals-lambda-repo:lisbon 871770651017.dkr.ecr.us-east-1.amazonaws.com/aviation-arrivals-lambda-repo:lisbon
docker push 871770651017.dkr.ecr.us-east-1.amazonaws.com/aviation-arrivals-lambda-repo:lisbon

if aws lambda get-function --function-name lisbon_arrival_lambda > /dev/null 2>&1; then
    echo "Function lisbon_arrival_lambda already exists. Updating code only."
else
    aws lambda create-function \
      --function-name lisbon_arrival_lambda \
      --package-type Image \
      --code ImageUri=871770651017.dkr.ecr.us-east-1.amazonaws.com/aviation-arrivals-lambda-repo:lisbon \
      --role arn:aws:iam::871770651017:role/LabRole \
      --timeout 900 \
      --memory-size 512 \
      --environment Variables="{API_KEY=${API_KEY}}" \
      --region us-east-1
    sleep 10
fi

aws lambda update-function-code --function-name lisbon_arrival_lambda --image-uri 871770651017.dkr.ecr.us-east-1.amazonaws.com/aviation-arrivals-lambda-repo:lisbon
cd ..


# Madrid
cd madrid_arrival_lambda
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 871770651017.dkr.ecr.us-east-1.amazonaws.com
docker build -t aviation-arrivals-lambda-repo:madrid .
docker tag aviation-arrivals-lambda-repo:madrid 871770651017.dkr.ecr.us-east-1.amazonaws.com/aviation-arrivals-lambda-repo:madrid
docker push 871770651017.dkr.ecr.us-east-1.amazonaws.com/aviation-arrivals-lambda-repo:madrid

if aws lambda get-function --function-name madrid_arrival_lambda > /dev/null 2>&1; then
    echo "Function madrid_arrival_lambda already exists. Updating code only."
else
    aws lambda create-function \
      --function-name madrid_arrival_lambda \
      --package-type Image \
      --code ImageUri=871770651017.dkr.ecr.us-east-1.amazonaws.com/aviation-arrivals-lambda-repo:madrid \
      --role arn:aws:iam::871770651017:role/LabRole \
      --timeout 900 \
      --memory-size 512 \
      --environment Variables="{API_KEY=${API_KEY}}" \
      --region us-east-1
    sleep 10
fi

aws lambda update-function-code --function-name madrid_arrival_lambda --image-uri 871770651017.dkr.ecr.us-east-1.amazonaws.com/aviation-arrivals-lambda-repo:madrid
cd ..


# Moscow
cd moscow_arrival_lambda
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 871770651017.dkr.ecr.us-east-1.amazonaws.com
docker build -t aviation-arrivals-lambda-repo:moscow .
docker tag aviation-arrivals-lambda-repo:moscow 871770651017.dkr.ecr.us-east-1.amazonaws.com/aviation-arrivals-lambda-repo:moscow
docker push 871770651017.dkr.ecr.us-east-1.amazonaws.com/aviation-arrivals-lambda-repo:moscow

# Check if the function exists
if aws lambda get-function --function-name moscow_arrival_lambda > /dev/null 2>&1; then
    echo "Function moscow_arrival_lambda already exists. Updating code only."
else
    aws lambda create-function \
      --function-name moscow_arrival_lambda \
      --package-type Image \
      --code ImageUri=871770651017.dkr.ecr.us-east-1.amazonaws.com/aviation-arrivals-lambda-repo:moscow \
      --role arn:aws:iam::871770651017:role/LabRole \
      --timeout 900 \
      --memory-size 512 \
      --environment Variables="{API_KEY=${API_KEY}}" \
      --region us-east-1
    sleep 10
fi

aws lambda update-function-code --function-name moscow_arrival_lambda --image-uri 871770651017.dkr.ecr.us-east-1.amazonaws.com/aviation-arrivals-lambda-repo:moscow
cd ..


# Zurich
cd zurich_arrival_lambda
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 871770651017.dkr.ecr.us-east-1.amazonaws.com
docker build -t aviation-arrivals-lambda-repo:zurich .
docker tag aviation-arrivals-lambda-repo:zurich 871770651017.dkr.ecr.us-east-1.amazonaws.com/aviation-arrivals-lambda-repo:zurich
docker push 871770651017.dkr.ecr.us-east-1.amazonaws.com/aviation-arrivals-lambda-repo:zurich

# Check if the function exists
if aws lambda get-function --function-name zurich_arrival_lambda > /dev/null 2>&1; then
    echo "Function zurich_arrival_lambda already exists. Updating code only."
else
    aws lambda create-function \
      --function-name zurich_arrival_lambda \
      --package-type Image \
      --code ImageUri=871770651017.dkr.ecr.us-east-1.amazonaws.com/aviation-arrivals-lambda-repo:zurich \
      --role arn:aws:iam::871770651017:role/LabRole \
      --timeout 900 \
      --memory-size 512 \
      --environment Variables="{API_KEY=${API_KEY}}" \
      --region us-east-1
    sleep 10
fi

aws lambda update-function-code --function-name zurich_arrival_lambda --image-uri 871770651017.dkr.ecr.us-east-1.amazonaws.com/aviation-arrivals-lambda-repo:zurich
cd ..


# Vienna
cd vienna_arrival_lambda
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 871770651017.dkr.ecr.us-east-1.amazonaws.com
docker build -t aviation-arrivals-lambda-repo:vienna .
docker tag aviation-arrivals-lambda-repo:vienna 871770651017.dkr.ecr.us-east-1.amazonaws.com/aviation-arrivals-lambda-repo:vienna
docker push 871770651017.dkr.ecr.us-east-1.amazonaws.com/aviation-arrivals-lambda-repo:vienna

# Check if the function exists
if aws lambda get-function --function-name vienna_arrival_lambda > /dev/null 2>&1; then
    echo "Function vienna_arrival_lambda already exists. Updating code only."
else
    aws lambda create-function \
      --function-name vienna_arrival_lambda \
      --package-type Image \
      --code ImageUri=871770651017.dkr.ecr.us-east-1.amazonaws.com/aviation-arrivals-lambda-repo:vienna \
      --role arn:aws:iam::871770651017:role/LabRole \
      --timeout 900 \
      --memory-size 512 \
      --environment Variables="{API_KEY=${API_KEY}}" \
      --region us-east-1
    sleep 10
fi

aws lambda update-function-code --function-name vienna_arrival_lambda --image-uri 871770651017.dkr.ecr.us-east-1.amazonaws.com/aviation-arrivals-lambda-repo:vienna
cd ..


# sh lambda_functions/aviationedge/create_or_update_lambda_function.sh lambda_functions/aviationedge/airport_requests aviationairportlambda 871770651017 aviation-edge-lambda-repo
# aws lambda invoke --function-name aviationairportlambda response.json
# nano ~/.aws/credentials
# export AWS_ACCESS_KEY_ID=
# export AWS_SESSION_TOKEN=
# export AWS_SECRET_ACCESS_KEY=

# sh lambda_functions/aviationedge/create_or_update_lambda_function.sh lambda_functions/aviationedge/departures_requests aviationdepartureslambda 871770651017 aviation-departures-lambda-repo
# aws lambda invoke --function-name aviationdepartureslambda response.json


# sh lambda_functions/aviationedge/create_or_update_lambda_function.sh lambda_functions/aviationedge/arrivals_requests aviationarrivalslambda 871770651017 aviation-arrivals-lambda-repo
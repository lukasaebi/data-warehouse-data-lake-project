#!/bin/bash

echo "Invoking Parent Departures Lambda..."
aws lambda invoke \
    --function-name parent_departures_lambda \
    --payload '{}' \
    /dev/null && echo "Parent Departures Lambda invoked successfully."

echo "Invoking Parent Arrivals Lambda..."
aws lambda invoke \
    --function-name parent_arrivals_lambda \
    --payload '{}' \
    /dev/null && echo "Parent Arrivals Lambda invoked successfully."

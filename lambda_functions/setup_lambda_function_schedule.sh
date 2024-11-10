#!/bin/bash

set -e

FUNCTION_NAME=$1

ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

### Create Event Rule for Lambda Function to schedule daily at 09:05 AM UTC in November and December

# Check if "DailyLambdaTrigger" rule exists (if exists -> rule_exists=1)
rule_exists=$(aws events list-rules --query "length(Rules[?Name=='DailyLambdaTrigger'])" --output text)

if [ "$rule_exists" -gt 0 ]; then
    echo "Event Rule DailyLambdaTrigger exists. Not creating again..."
else
    echo "Creating Event Rule 'DailyLambdaTrigger'..."
    aws events put-rule \
        --name DailyLambdaTrigger \
        --schedule-expression "cron(5 9 * 11,12 ? *)" \
        --description "Triggers Lambda daily at 9:05 AM UTC in November and December" \
        --no-cli-pager # not cli output
    echo "Event Rule 'DailyLambdaTrigger' successfully created."
fi

### Give Permission to Event Rule to Invoke Lambda Function

if aws lambda get-policy --function-name $FUNCTION_NAME > /dev/null 2>&1; then # if command returns something
    echo "There already exists a policy for $FUNCTION_NAME."
else # if fails
    echo "Creating new policy 'DailyTriggerPermission' for $FUNCTION_NAME..."
    aws lambda add-permission \
        --function-name $FUNCTION_NAME \
        --statement-id DailyTriggerPermission \
        --action 'lambda:InvokeFunction' \
        --principal events.amazonaws.com \
        --source-arn arn:aws:events:us-east-1:$ACCOUNT_ID:rule/DailyLambdaTrigger \
        --no-cli-pager
    echo "New policy 'DailyTriggerPermission' successfully created for $FUNCTION_NAME."
fi

### Add Lambda Function as Target to Event Rule

# Check if FUNCTION_NAME is in any of the ARNs of the targets
target_exists=$(aws events list-targets-by-rule \
    --rule DailyLambdaTrigger \
    --query "Targets[?contains(Arn, ':function:$FUNCTION_NAME')] | length(@)" \
    --output text)

if [ "$target_exists" -gt 0 ]; then
    echo "Lambda function '$FUNCTION_NAME' is already a target for DailyLambdaTrigger. No new target creating."
else
    echo "Adding Lambda function $FUNCTION_NAME as a new target for DailyLambdaTrigger."
    
    # Get the count of targets for unique ID assignment
    TARGET_COUNT=$(aws events list-targets-by-rule \
        --rule DailyLambdaTrigger \
        --query 'Targets | length(@)' \
        --output text)
    NEW_ID=$((TARGET_COUNT + 1))

    # Add the new target
    aws events put-targets \
        --rule DailyLambdaTrigger \
        --targets "Id"="$NEW_ID","Arn"="arn:aws:lambda:us-east-1:$ACCOUNT_ID:function:$FUNCTION_NAME" \
        --no-cli-pager

    echo "Lambda function $FUNCTION_NAME added as a target."
fi

echo "Lambda function $FUNCTION_NAME is scheduled to run daily at 9:05 AM UTC in November and December"

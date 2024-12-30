#!/bin/bash

set -e

FUNCTION_NAME=$1
EVENT_RULE_NAME=$2
SCHEDULE_EXPRESSION=$3

ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

### Create Event Rule for Lambda Function to schedule daily at 10:00 AM UTC in November and December

# Check if "$EVENT_RULE_NAME" rule exists (if exists -> rule_exists=1)
rule_exists=$(aws events list-rules --query "length(Rules[?Name=='$EVENT_RULE_NAME'])" --output text)

if [ "$rule_exists" -gt 0 ]; then
    echo "Event Rule $EVENT_RULE_NAME exists. Not creating again..."
else
    echo "Creating Event Rule '$EVENT_RULE_NAME'..."
    aws events put-rule \
        --name $EVENT_RULE_NAME \
        --schedule-expression "$SCHEDULE_EXPRESSION" \
        --no-cli-pager # not cli output
    echo "Event Rule '$EVENT_RULE_NAME' successfully created."
fi

### Give Permission to Event Rule to Invoke Lambda Function

if aws lambda get-policy --function-name $FUNCTION_NAME > /dev/null 2>&1; then # if command returns something
    echo "There already exists a policy for $FUNCTION_NAME."
else # if fails
    STATEMENT_ID="${EVENT_RULE_NAME}Permission"
    echo "Creating new policy '$STATEMENT_ID' for $FUNCTION_NAME..."
    aws lambda add-permission \
        --function-name $FUNCTION_NAME \
        --statement-id $STATEMENT_ID \
        --action 'lambda:InvokeFunction' \
        --principal events.amazonaws.com \
        --source-arn arn:aws:events:us-east-1:$ACCOUNT_ID:rule/$EVENT_RULE_NAME \
        --no-cli-pager
    echo "New policy '$STATEMENT_ID' successfully created for $FUNCTION_NAME."
fi

### Add Lambda Function as Target to Event Rule

# Check if FUNCTION_NAME is in any of the ARNs of the targets
target_exists=$(aws events list-targets-by-rule \
    --rule $EVENT_RULE_NAME \
    --query "Targets[?contains(Arn, ':function:$FUNCTION_NAME')] | length(@)" \
    --output text)

if [ "$target_exists" -gt 0 ]; then
    echo "Lambda function '$FUNCTION_NAME' is already a target for $EVENT_RULE_NAME. No new target creating."
else
    echo "Adding Lambda function $FUNCTION_NAME as a new target for $EVENT_RULE_NAME."
    
    # Get the count of targets for unique ID assignment
    TARGET_COUNT=$(aws events list-targets-by-rule \
        --rule $EVENT_RULE_NAME \
        --query 'Targets | length(@)' \
        --output text)
    NEW_ID=$((TARGET_COUNT + 1))

    # Add the new target
    aws events put-targets \
        --rule $EVENT_RULE_NAME \
        --targets "Id"="$NEW_ID","Arn"="arn:aws:lambda:us-east-1:$ACCOUNT_ID:function:$FUNCTION_NAME" \
        --no-cli-pager

    echo "Lambda function $FUNCTION_NAME added as a target."
fi

echo "Lambda function $FUNCTION_NAME has been successfully scheduled."

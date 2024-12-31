"""
Differences to file in root directory: 
- unique rule for each function --> maintaining each function
- offset arguments to run scripts sequently
        ./setup_eventbridge.sh zurich_arrival_lambda 5
        ./setup_eventbridge.sh vienna_arrival_lambda 15
        ......

"""

#!/bin/bash

set -e

if [ -z "$1" ]; then
    echo "Usage: ./setup_eventbridge.sh <FUNCTION_NAME> <START_MINUTE>"
    exit 1
fi

FUNCTION_NAME=$1
START_MINUTE=${2:-5}  # Default to 5 if not provided

# Get AWS account ID
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

RULE_NAME="${FUNCTION_NAME}_DailyTrigger"

# Create Event Rule
rule_exists=$(aws events list-rules --query "length(Rules[?Name=='$RULE_NAME'])" --output text)

if [ "$rule_exists" -gt 0 ]; then
    echo "Event Rule $RULE_NAME exists. Not creating again..."
else
    echo "Creating Event Rule '$RULE_NAME'..."
    aws events put-rule \
        --name $RULE_NAME \
        --schedule-expression "cron(${START_MINUTE} 9 * * ? *)" \
        --description "Triggers $FUNCTION_NAME daily at 9:${START_MINUTE} AM UTC" \
        --no-cli-pager
    echo "Event Rule '$RULE_NAME' successfully created."
fi

# Grant Permissions
if aws lambda get-policy --function-name $FUNCTION_NAME > /dev/null 2>&1; then
    echo "There already exists a policy for $FUNCTION_NAME."
else
    echo "Creating new policy '${FUNCTION_NAME}_DailyTriggerPermission' for $FUNCTION_NAME..."
    aws lambda add-permission \
        --function-name $FUNCTION_NAME \
        --statement-id "${FUNCTION_NAME}_DailyTriggerPermission" \
        --action 'lambda:InvokeFunction' \
        --principal events.amazonaws.com \
        --source-arn arn:aws:events:us-east-1:$ACCOUNT_ID:rule/$RULE_NAME \
        --no-cli-pager
    echo "New policy '${FUNCTION_NAME}_DailyTriggerPermission' successfully created for $FUNCTION_NAME."
fi

# Add Target
target_exists=$(aws events list-targets-by-rule \
    --rule $RULE_NAME \
    --query "Targets[?contains(Arn, ':function:$FUNCTION_NAME')] | length(@)" \
    --output text)

if [ "$target_exists" -gt 0 ]; then
    echo "Lambda function '$FUNCTION_NAME' is already a target for $RULE_NAME. No new target created."
else
    echo "Adding Lambda function $FUNCTION_NAME as a new target for $RULE_NAME."

    TARGET_COUNT=$(aws events list-targets-by-rule \
        --rule $RULE_NAME \
        --query 'Targets | length(@)' \
        --output text)
    NEW_ID=$((TARGET_COUNT + 1))

    aws events put-targets \
        --rule $RULE_NAME \
        --targets "Id"="$NEW_ID","Arn"="arn:aws:lambda:us-east-1:$ACCOUNT_ID:function:$FUNCTION_NAME" \
        --no-cli-pager

    echo "Lambda function $FUNCTION_NAME added as a target."
fi

echo "Lambda function $FUNCTION_NAME is scheduled to run daily at 9:${START_MINUTE} AM UTC."

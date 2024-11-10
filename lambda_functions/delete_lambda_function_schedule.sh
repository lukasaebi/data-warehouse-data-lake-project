#!/bin/bash

set -e

FUNCTION_NAME=$1

# Set your rule and Lambda function names
RULE_NAME="DailyLambdaTrigger"
PERMISSION_NAME="DailyTriggerPermission"

# Step 1: Remove all targets from the rule
echo "Removing targets from rule $RULE_NAME for function $FUNCTION_NAME..."
aws events remove-targets \
    --rule "$RULE_NAME" \
    --ids $(aws events list-targets-by-rule \
                --rule "$RULE_NAME" \
                --query "Targets[?contains(Arn, ':function:$FUNCTION_NAME')].Id" \
                --output text) \
    --no-cli-pager
echo "All targets removed from rule $RULE_NAME for function $FUNCTION_NAME."

# Step 2: Remove all permissions associated with the Lambda function for EventBridge
echo "Removing permission $PERMISSION_NAME from Lambda function $FUNCTION_NAME..."
aws lambda remove-permission --function-name "$FUNCTION_NAME" --statement-id $PERMISSION_NAME
echo "Permission $PERMISSION_NAME from Lambda function $FUNCTION_NAME removed."

# Step 3: Delete the EventBridge rule
echo "Trying to delete rule $RULE_NAME..."
if aws events delete-rule --name "$RULE_NAME" > /dev/null 2>&1; then
    echo "Rule $RULE_NAME successfully deleted."
    echo "Cleanup complete. Targets, permissions, and rules have been deleted."
else
    echo "Failed to delete rule $RULE_NAME. Rule can't be deleted since it still has targets."
    echo "Cleanup complete. Targets and permissions have been deleted."
fi

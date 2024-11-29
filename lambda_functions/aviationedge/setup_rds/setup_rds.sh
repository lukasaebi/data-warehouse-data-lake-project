#!/bin/bash

set -e

# Load environment variables from .env file
export $(grep -v '^#' .env | xargs)

# Validate that necessary environment variables are set
validate_env_vars() {
    REQUIRED_VARS=("DB_INSTANCE_IDENTIFIER" "DB_INSTANCE_CLASS" "ENGINE" "ALLOCATED_STORAGE" 
                   "BACKUP_RETENTION_PERIOD" "MAX_STORAGE_THRESHOLD" "RDS_PASSWORD" 
                   "AWS_REGION" "RDS_USER" "SECURITY_GROUP_ID")
    for var in "${REQUIRED_VARS[@]}"; do
        if [ -z "${!var}" ]; then
            echo "Error: $var is not set. Please check your .env file."
            exit 1
        fi
    done
}

# Logging function
log() {
    echo "$(date +'%Y-%m-%d %H:%M:%S') - $1"
}

# Create the RDS instance
create_rds_instance() {
    log "Creating RDS instance '$DB_INSTANCE_IDENTIFIER'..."
    aws rds create-db-instance \
        --db-instance-identifier "$DB_INSTANCE_IDENTIFIER" \
        --db-instance-class "$DB_INSTANCE_CLASS" \
        --engine "$ENGINE" \
        --allocated-storage "$ALLOCATED_STORAGE" \
        --master-username "$RDS_USER" \
        --master-user-password "$RDS_PASSWORD" \
        --backup-retention-period "$BACKUP_RETENTION_PERIOD" \
        --no-multi-az \
        --vpc-security-group-ids "$SECURITY_GROUP_ID" \
        --availability-zone "$(aws ec2 describe-availability-zones --region $AWS_REGION --query 'AvailabilityZones[0].ZoneName' --output text)" \
        --publicly-accessible \
        --storage-type gp2 \
        --storage-autoscaling-enabled \
        --max-allocated-storage "$MAX_STORAGE_THRESHOLD"
}

# Wait for the RDS instance to be available
wait_for_rds() {
    log "Waiting for RDS instance to become available..."
    aws rds wait db-instance-available --db-instance-identifier "$DB_INSTANCE_IDENTIFIER"
}

# Fetch the RDS endpoint
fetch_rds_endpoint() {
    log "Fetching RDS endpoint..."
    DB_ENDPOINT=$(aws rds describe-db-instances \
        --db-instance-identifier "$DB_INSTANCE_IDENTIFIER" \
        --query "DBInstances[0].Endpoint.Address" \
        --output text)
    log "RDS instance '$DB_INSTANCE_IDENTIFIER' is available at endpoint: $DB_ENDPOINT"
}

# Execute the script
validate_env_vars
create_rds_instance
wait_for_rds
fetch_rds_endpoint
log "RDS setup complete."

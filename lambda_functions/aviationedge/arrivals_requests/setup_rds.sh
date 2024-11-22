#!/bin/bash

set -e
# Load environment variables from .env file
export $(grep -v '^#' .env | xargs)

DB_INSTANCE_IDENTIFIER="aviation-data-rds"
DB_INSTANCE_CLASS="db.t3.micro"
ENGINE="mysql"
ALLOCATED_STORAGE=20
MASTER_USERNAME="admin"
MASTER_PASSWORD=$RDS_PASSWORD
BACKUP_RETENTION_PERIOD=7
VPC_SECURITY_GROUP_ID=$SECURITY_GROUP_ID
AVAILABILITY_ZONE="us-east-1a"

echo "Creating RDS instance '$DB_INSTANCE_IDENTIFIER'..."

# Create the RDS instance
aws rds create-db-instance \
    --db-instance-identifier $DB_INSTANCE_IDENTIFIER \
    --db-instance-class $DB_INSTANCE_CLASS \
    --engine $ENGINE \
    --allocated-storage $ALLOCATED_STORAGE \
    --master-username $MASTER_USERNAME \
    --master-user-password $MASTER_PASSWORD \
    --backup-retention-period $BACKUP_RETENTION_PERIOD \
    --vpc-security-group-ids $VPC_SECURITY_GROUP_ID \
    --availability-zone $AVAILABILITY_ZONE \
    --publicly-accessible

echo "Waiting for RDS instance to become available..."
aws rds wait db-instance-available --db-instance-identifier $DB_INSTANCE_IDENTIFIER

echo "Fetching RDS endpoint..."
DB_ENDPOINT=$(aws rds describe-db-instances \
    --db-instance-identifier $DB_INSTANCE_IDENTIFIER \
    --query "DBInstances[0].Endpoint.Address" \
    --output text)

echo "RDS instance '$DB_INSTANCE_IDENTIFIER' is available at endpoint: $DB_ENDPOINT"

echo "Creating database schema..."
aws rds-data execute-statement \
    --sql "CREATE TABLE IF NOT EXISTS arrivals (
        id SERIAL PRIMARY KEY,
        ar_type VARCHAR(20),
        ar_status VARCHAR(20),
        dep_iata VARCHAR(10),
        dep_delay INT,
        dep_scheduledTime TIMESTAMP,
        dep_estimatedTime TIMESTAMP,
        dep_actualTime TIMESTAMP,
        ar_iata VARCHAR(10),
        ar_delay INT,
        ar_scheduledTime TIMESTAMP,
        ar_estimatedTime TIMESTAMP,
        ar_actualTime TIMESTAMP,
        airline_name VARCHAR(100),
        airline_iata VARCHAR(10),
        airline_icao VARCHAR(10),
        flight_number VARCHAR(20),
        flight_iata VARCHAR(20),
        flight_icao VARCHAR(20)
    );"

echo "Database setup is complete. Endpoint: $DB_ENDPOINT"

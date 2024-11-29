import psycopg2
import boto3
import json
import os
from datetime import datetime

# Load environment variables
RDS_HOST = os.getenv("RDS_HOST")
RDS_USER = os.getenv("RDS_USER")
RDS_PASSWORD = os.getenv("RDS_PASSWORD")
RDS_DBNAME = os.getenv("RDS_DBNAME", "postgres")
S3_BUCKET = os.getenv("S3_BUCKET", "aviations3")

def connect_to_rds():
    """Connect to the RDS instance."""
    try:
        return psycopg2.connect(
            host=RDS_HOST,
            user=RDS_USER,
            password=RDS_PASSWORD,
            dbname=RDS_DBNAME,
            port=5432  # Default PostgreSQL port
        )
    except Exception as e:
        print({"statusCode": 500, "message": f"Error connecting to RDS: {str(e)}"})
        raise

def parse_timestamp(timestamp):
    """Parse the timestamp to a PostgreSQL-compatible format."""
    if timestamp:
        try:
            return datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%S.%f")
        except ValueError:
            return datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%S")
    return None

def insert_data_to_rds(data, table_name):
    """Insert JSON data into the specified PostgreSQL table."""
    connection = connect_to_rds()
    try:
        with connection.cursor() as cursor:
            sql = f"""
            INSERT INTO {table_name} (
                ar_type, ar_status, dep_iata, dep_delay, dep_scheduledTime, dep_estimatedTime, dep_actualTime,
                ar_iata, ar_delay, ar_scheduledTime, ar_estimatedTime, ar_actualTime,
                airline_name, airline_iata, airline_icao, flight_number, flight_iata, flight_icao
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """

            for record in data:
                values = (
                    record.get("type"),
                    record.get("status"),
                    record.get("departure", {}).get("iataCode"),
                    record.get("departure", {}).get("delay"),
                    parse_timestamp(record.get("departure", {}).get("scheduledTime")),
                    parse_timestamp(record.get("departure", {}).get("estimatedTime")),
                    parse_timestamp(record.get("departure", {}).get("actualTime")),
                    record.get("arrival", {}).get("iataCode"),
                    record.get("arrival", {}).get("delay"),
                    parse_timestamp(record.get("arrival", {}).get("scheduledTime")),
                    parse_timestamp(record.get("arrival", {}).get("estimatedTime")),
                    parse_timestamp(record.get("arrival", {}).get("actualTime")),
                    record.get("airline", {}).get("name"),
                    record.get("airline", {}).get("iataCode"),
                    record.get("airline", {}).get("icaoCode"),
                    record.get("flight", {}).get("number"),
                    record.get("flight", {}).get("iataNumber"),
                    record.get("flight", {}).get("icaoNumber")
                )
                cursor.execute(sql, values)
        connection.commit()
        print(f"Data successfully inserted into {table_name}.")
    finally:
        connection.close()

def fetch_data_from_s3(bucket, key):
    """Fetch JSON data from S3."""
    s3 = boto3.client("s3")
    response = s3.get_object(Bucket=bucket, Key=key)
    data = response["Body"].read().decode("utf-8")
    return json.loads(data)

def process_file(bucket, key):
    """Process a single file from S3 and insert data into the corresponding PostgreSQL table."""
    data = fetch_data_from_s3(bucket, key)
    if "arrivals" in key:
        insert_data_to_rds(data, "arrivals")
    elif "departures" in key:
        insert_data_to_rds(data, "departures")
    else:
        print(f"Unknown file type for key: {key}. Skipping...")

def lambda_handler(event, context):
    """Main Lambda handler."""
    bucket = event["bucket_name"]
    key = event["key"]
    process_file(bucket, key)
    return {"statusCode": 200, "body": "Data transfer to RDS completed successfully!"}

import boto3
import pymysql
import json
import os
from datetime import datetime

# S3 and RDS clients
s3_client = boto3.client('s3')

def connect_to_rds():
    return pymysql.connect(
        host=os.getenv("RDS_HOST"),
        user=os.getenv("RDS_USER"),
        password=os.getenv("RDS_PASSWORD"),
        database=os.getenv("RDS_DB"),
        cursorclass=pymysql.cursors.DictCursor
    )

def process_data_to_rds(data, connection):
    with connection.cursor() as cursor:
        for record in data:
            sql = """
                INSERT INTO arrivals (
                    ar_type, ar_status, dep_iata, dep_delay, dep_scheduledTime, dep_estimatedTime, dep_actualTime,
                    ar_iata, ar_delay, ar_scheduledTime, ar_estimatedTime, ar_actualTime,
                    airline_name, airline_iata, airline_icao, flight_number, flight_iata, flight_icao
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
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

def parse_timestamp(timestamp):
    if timestamp:
        return datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%S.%f")
    return None

def lambda_handler(event, context):
    bucket_name = event['bucket_name']
    key = event['key']
    
    response = s3_client.get_object(Bucket=bucket_name, Key=key)
    file_content = response['Body'].read().decode('utf-8')
    data = json.loads(file_content)

    connection = connect_to_rds()
    try:
        process_data_to_rds(data, connection)
        print(f"Data from {key} successfully loaded into RDS.")
    except Exception as e:
        print(f"Error processing data: {e}")
    finally:
        connection.close()

    return {"statusCode": 200, "body": "Data successfully loaded into RDS."}

import psycopg2
import boto3
import json
import os
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables from .env file
load_dotenv()

# Fetch database connection details from .env file
RDS_HOST = os.getenv("RDS_HOST")
RDS_USER = os.getenv("RDS_USER")
RDS_PASSWORD = os.getenv("RDS_PASSWORD")
RDS_DBNAME = os.getenv("RDS_DBNAME", "aviation")
S3_BUCKET = os.getenv("S3_BUCKET", "aviations3")

# Function to connect to the RDS database
def connect_to_rds():
    try:
        return psycopg2.connect(
            host=RDS_HOST,
            user=RDS_USER,
            password=RDS_PASSWORD,
            dbname=RDS_DBNAME,
            port=5432,
        )
    except Exception as e:
        print({"statusCode": 500, "message": f"Error connecting to RDS: {str(e)}"})
        raise

# Function to fetch data from S3
def fetch_data_from_s3(bucket, key):
    s3 = boto3.client("s3")
    response = s3.get_object(Bucket=bucket, Key=key)
    return json.loads(response["Body"].read().decode("utf-8"))

# Function to insert data into RDS
def insert_data_to_rds(data):
    connection = connect_to_rds()
    try:
        with connection.cursor() as cursor:
            sql = """
                INSERT INTO arrivals (
                    flight_number, flight_iata_number, type, status,
                    departure_iata, departure_delay, departure_scheduled_time, departure_actual_time,
                    arrival_iata, arrival_scheduled_time, arrival_actual_time,
                    airline_name, airline_iata
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """

            # Insert only records without codeshared information
            for record in data:
                if "codeshared" in record:
                    # Skip records with codeshared information
                    continue

                values = (
                    record.get("flight", {}).get("number"),
                    record.get("flight", {}).get("iataNumber"),
                    record.get("type"),
                    record.get("status"),
                    record.get("departure", {}).get("iataCode"),
                    record.get("departure", {}).get("delay"),
                    parse_timestamp(record.get("departure", {}).get("scheduledTime")),
                    parse_timestamp(record.get("departure", {}).get("actualTime")),
                    record.get("arrival", {}).get("iataCode"),
                    parse_timestamp(record.get("arrival", {}).get("scheduledTime")),
                    parse_timestamp(record.get("arrival", {}).get("actualTime")),
                    record.get("airline", {}).get("name"),
                    record.get("airline", {}).get("iataCode"),
                )
                cursor.execute(sql, values)

        connection.commit()
        print("Data successfully inserted into the 'arrivals' table without codeshared flights.")
    finally:
        connection.close()

# Function to parse timestamp
def parse_timestamp(timestamp):
    if timestamp:
        try:
            return datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%S.%f")
        except ValueError:
            return datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%S")
    return None

# Main function
def main():
    file_key = "arrivals/Paris/CDG_2024-11-19_to_2024-11-20.json"
    data = fetch_data_from_s3(S3_BUCKET, file_key)
    insert_data_to_rds(data)

if __name__ == "__main__":
    main()


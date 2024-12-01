import os
import json
import logging
from contextlib import contextmanager
from datetime import datetime
from io import StringIO
from pathlib import Path
import boto3
import pandas as pd
import psycopg2
from psycopg2.extensions import connection
from dotenv import load_dotenv
from tqdm import tqdm
import yaml

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()
S3_BUCKET = os.getenv("S3_BUCKET", "aviations3")
DB_PASSWORD = os.getenv("RDS_PASSWORD")

# Boto3 S3 client
s3_client = boto3.client("s3")

# Configurations
class Config:
    def __init__(self, config_path):
        with open(config_path, "r") as f:
            config = yaml.safe_load(f)
            self.host = config["host"]
            self.user = config["user"]
            self.port = config["port"]
            self.dbname = config["dbname"]
            self.base_path = config["base_path"]
            self.bucket_name = config["bucket_name"]

    @classmethod
    def from_yaml(cls, path: Path) -> "Config":
        return cls(path)

# Context manager for DB connections
@contextmanager
def make_db_connection(config: Config, db_password: str) -> connection:
    """
    Creates and manages a database connection.
    """
    conn = None
    try:
        conn = psycopg2.connect(
            host=config.host,
            user=config.user,
            password=db_password,
            port=config.port,
            dbname=config.dbname,
        )
        yield conn
    except Exception as e:
        logger.error(f"Database connection error: {e}")
        raise
    finally:
        if conn:
            conn.close()

# List files from S3 with batching by size
def list_s3_files_by_size(bucket_name: str, prefix: str, size_threshold: int) -> list[list[str]]:
    """
    List JSON files in an S3 bucket under a given prefix and batch them by cumulative size.
    """
    paginator = s3_client.get_paginator("list_objects_v2")
    files = []
    for page in paginator.paginate(Bucket=bucket_name, Prefix=prefix):
        files.extend(
            {"Key": content["Key"], "Size": content["Size"]}
            for content in page.get("Contents", [])
            if content["Key"].endswith(".json")
        )

    # Group files into batches by size
    batches = []
    current_batch = []
    current_batch_size = 0

    for file in files:
        if current_batch_size + file["Size"] > size_threshold:
            # Append the current batch and start a new one
            batches.append(current_batch)
            current_batch = []
            current_batch_size = 0

        current_batch.append(file["Key"])
        current_batch_size += file["Size"]

    # Add any remaining files to the last batch
    if current_batch:
        batches.append(current_batch)

    return batches

# Download a file from S3
def download_s3_file(bucket_name: str, key: str, output_path: Path) -> None:
    """
    Downloads a file from S3 to a specified path.
    """
    s3_client.download_file(bucket_name, key, str(output_path))

# Create a table if not exists
def create_table(conn: connection):
    """
    Ensures the table exists before inserting data.
    """
    with conn.cursor() as cur:
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS arrivals (
                id SERIAL PRIMARY KEY,
                flight_number VARCHAR(20),
                flight_iata_number VARCHAR(20),
                type VARCHAR(20),
                status VARCHAR(20),
                departure_iata VARCHAR(10),
                departure_delay INT,
                departure_scheduled_time TIMESTAMP,
                departure_actual_time TIMESTAMP,
                arrival_iata VARCHAR(10),
                arrival_scheduled_time TIMESTAMP,
                arrival_actual_time TIMESTAMP,
                airline_name VARCHAR(100),
                airline_iata VARCHAR(10)
            )
            """
        )
        conn.commit()

# Bulk insert data into the table
def insert_bulk_data_from_dataframe(conn: connection, df: pd.DataFrame):
    """
    Inserts data from a DataFrame into the database using COPY.
    """
    csv_buffer = StringIO()
    df.to_csv(csv_buffer, index=False, header=False)
    csv_buffer.seek(0)

    with conn.cursor() as cur:
        cur.copy_expert(
            """
            COPY arrivals (
                flight_number, flight_iata_number, type, status,
                departure_iata, departure_delay, departure_scheduled_time, departure_actual_time,
                arrival_iata, arrival_scheduled_time, arrival_actual_time,
                airline_name, airline_iata
            ) FROM STDIN WITH CSV
            """,
            csv_buffer,
        )
    conn.commit()

# Parse timestamp
def parse_timestamp(timestamp):
    if timestamp:
        try:
            # Replace 't' with 'T' to match ISO 8601 format
            timestamp = timestamp.replace('t', 'T')
            return datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%S.%f")
        except ValueError as e:
            logger.error(f"Error parsing timestamp {timestamp}: {e}")
            return None
    return None


# Create a pandas DataFrame from S3 JSON files
def create_dataframe_from_s3_files(filepaths: list[str], bucket_name: str) -> pd.DataFrame:
    """
    Reads multiple JSON files from S3 and creates a consolidated pandas DataFrame.
    """
    rows = []
    for filepath in filepaths:
        download_s3_file(bucket_name, filepath, Path("/tmp/temp.json"))
        try:
            with open("/tmp/temp.json", "r") as f:
                data = json.load(f)
                
            # Check if the file contains an error key
            if isinstance(data, dict) and data.get("error"):
                logger.warning(f"Skipping file due to error: {data['error']}")
                continue
                
            for record in data:
                if "codeshared" in record:
                    logger.info(f"Skipping codeshared flight: {record.get('codeshared')}")
                    continue  # Skip codeshared flights
                rows.append(
                    {
                        "flight_number": record.get("flight", {}).get("number"),
                        "flight_iata_number": record.get("flight", {}).get("iataNumber"),
                        "type": record.get("type"),
                        "status": record.get("status"),
                        "departure_iata": record.get("departure", {}).get("iataCode"),
                        "departure_delay": record.get("departure", {}).get("delay"),
                        "departure_scheduled_time": parse_timestamp(record.get("departure", {}).get("scheduledTime")),
                        "departure_actual_time": parse_timestamp(record.get("departure", {}).get("actualTime")),
                        "arrival_iata": record.get("arrival", {}).get("iataCode"),
                        "arrival_scheduled_time": parse_timestamp(record.get("arrival", {}).get("scheduledTime")),
                        "arrival_actual_time": parse_timestamp(record.get("arrival", {}).get("actualTime")),
                        "airline_name": record.get("airline", {}).get("name"),
                        "airline_iata": record.get("airline", {}).get("iataCode"),
                    }
                )
        except Exception as e:
            logger.error(f"Error processing file {filepath}: {e}")
        finally:
            # Cleanup temporary file
            try:
                os.remove("/tmp/temp.json")
            except OSError as e:
                logger.warning(f"Error deleting temporary file: {e}")

    return pd.DataFrame(rows)



# Main function
def main(event, context):
    """
    Lambda handler function. Accepts AWS event and context objects.
    """
    config = Config.from_yaml(Path("config.yaml"))
    size_threshold = 300 * 1024 * 1024  # 300 MB

    with make_db_connection(config, DB_PASSWORD) as conn:
        create_table(conn)

        batches = list_s3_files_by_size(config.bucket_name, config.base_path, size_threshold)
        logger.info(f"Found {len(batches)} batches to process.")

        for i, batch in enumerate(tqdm(batches), start=1):
            df = create_dataframe_from_s3_files(batch, config.bucket_name)
            insert_bulk_data_from_dataframe(conn, df)
            logger.info(f"Inserted batch {i} into database.")

    logger.info("All files processed and data loaded.")

def test_with_single_file():
    config = Config.from_yaml(Path("config.yaml"))
    filepaths = ["arrivals/Lisbon/LIS_2023-12-01.json"]
    
    logger.info(f"Testing with file: {filepaths[0]}")
    
    df = create_dataframe_from_s3_files(filepaths, config.bucket_name)
    
    if df.empty:
        logger.warning("No rows were extracted from the file.")
    else:
        logger.info(f"DataFrame created with {len(df)} rows:")
        logger.info(df.head())



if __name__ == "__main__":
    test_with_single_file()


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
import yaml
from pydantic import BaseModel

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()
DB_PASSWORD = os.getenv("RDS_PASSWORD")

# Boto3 S3 client
s3_client = boto3.client("s3")

# Configurations
class Config(BaseModel):
    cities: list[str]
    host: str
    user: str
    port: int
    dbname: str
    bucket_name: str
    base_path: str

    @classmethod
    def from_yaml(cls, path: Path) -> "Config":
        with open(path, "r") as f:
            config = yaml.safe_load(f)
        return Config(**config)

# Context manager for DB connections
@contextmanager
def make_db_connection(config: Config, db_password: str) -> connection:
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

# List files from S3
def list_s3_files(bucket_name: str, prefix: str) -> list[str]:
    paginator = s3_client.get_paginator("list_objects_v2")
    files = []
    for page in paginator.paginate(Bucket=bucket_name, Prefix=prefix):
        files.extend(
            content["Key"] for content in page.get("Contents", [])
            if content["Key"].endswith(".json")
        )
    return sorted(files)

# Download a file from S3
def download_s3_file(bucket_name: str, key: str, output_path: Path) -> None:
    s3_client.download_file(bucket_name, key, str(output_path))

# Bulk insert data into the departures table
def insert_bulk_data_from_dataframe(conn: connection, df: pd.DataFrame):
    csv_buffer = StringIO()
    df.to_csv(csv_buffer, index=False, header=False)
    csv_buffer.seek(0)

    with conn.cursor() as cur:
        cur.copy_expert(
            """
            COPY departures (
                flight_number, flight_iata_number, type, status,
                departure_iata, departure_delay, departure_scheduled_time, departure_actual_time,
                arrival_iata, arrival_scheduled_time, arrival_estimated_time,
                airline_name, airline_iata
            ) FROM STDIN WITH CSV;
            """,
            csv_buffer,
        )
    conn.commit()

# Create DataFrame from S3 JSON files
def create_dataframe_from_s3_files(filepaths: list[str], bucket_name: str) -> pd.DataFrame:
    rows = []
    for filepath in filepaths:
        download_s3_file(bucket_name, filepath, Path("/tmp/temp.json"))
        try:
            with open("/tmp/temp.json", "r") as f:
                data = json.load(f)

            for record in data:
                if "codeshared" in record:
                    continue  # Skip codeshared flights

                # Parse `departure_actual_time`
                departure_actual_time = parse_timestamp(record.get("departure", {}).get("actualTime"))
                if not departure_actual_time:
                    continue  # Skip rows with null `departure_actual_time`

                # Limit processing to departures between 06:00 and 09:00
                if not (6 <= departure_actual_time.hour < 9):
                    continue  

                # Use the delay from the data
                departure_delay = int(float(record.get("departure", {}).get("delay", 0) or 0))

                rows.append({
                    "flight_number": record.get("flight", {}).get("number"),
                    "flight_iata_number": record.get("flight", {}).get("iataNumber"),
                    "type": record.get("type"),
                    "status": record.get("status"),
                    "departure_iata": record.get("departure", {}).get("iataCode"),
                    "departure_delay": departure_delay,
                    "departure_scheduled_time": parse_timestamp(record.get("departure", {}).get("scheduledTime")),
                    "departure_actual_time": departure_actual_time,
                    "arrival_iata": record.get("arrival", {}).get("iataCode"),
                    "arrival_scheduled_time": parse_timestamp(record.get("arrival", {}).get("scheduledTime")),
                    "arrival_estimated_time": parse_timestamp(record.get("arrival", {}).get("estimatedTime")),
                    "airline_name": record.get("airline", {}).get("name"),
                    "airline_iata": record.get("airline", {}).get("iataCode"),
                })
        except Exception as e:
            logger.error(f"Error processing file {filepath}: {e}")
        finally:
            try:
                os.remove("/tmp/temp.json")
            except OSError as e:
                logger.warning(f"Error deleting temporary file: {e}")

    return pd.DataFrame(rows)

# Parse timestamp
def parse_timestamp(timestamp):
    if timestamp:
        try:
            timestamp = timestamp.replace('t', 'T')
            return datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%S.%f")
        except ValueError as e:
            logger.error(f"Error parsing timestamp {timestamp}: {e}")
            return None
    return None

# Lambda handler function
def lambda_handler(event, context):
    config = Config.from_yaml(Path(__file__).absolute().parent / "config.yaml")
    db_password = os.environ["RDS_PASSWORD"]

    date = datetime.now().strftime("%Y-%m-%d")
    logger.info(f"Processing files from `{date}` for each city.")

    with make_db_connection(config, db_password) as conn:
        for city in config.cities:
            prefix = f"{config.base_path}/{city}/"
            all_files = list_s3_files(config.bucket_name, prefix)
            daily_files = [f for f in all_files if f"_{date}.json" in f]

            if daily_files:
                logger.info(f"Found {len(daily_files)} files for {city}.")
                df = create_dataframe_from_s3_files(daily_files, config.bucket_name)
                logger.info(f"DataFrame for {city} created with {len(df)} rows.")
                if not df.empty:
                    insert_bulk_data_from_dataframe(conn, df)
                    logger.info(f"Data for `{city}` successfully inserted into the database.")
            else:
                logger.info(f"No new files found for {city}.")

    logger.info("All data processed and uploaded.")

if __name__ == "__main__":
    lambda_handler(None, None)



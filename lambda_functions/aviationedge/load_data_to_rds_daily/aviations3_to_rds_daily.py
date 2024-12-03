import json
import logging
import os
from contextlib import contextmanager
from datetime import datetime
from io import StringIO
from pathlib import Path

import boto3
import pandas as pd
import psycopg2
import yaml
from psycopg2.extensions import connection
from pydantic import BaseModel

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

s3_client = boto3.client("s3")


class Config(BaseModel):
    cities: list[str]
    host: str
    user: str
    port: int
    dbname: str
    bucket_name: str
    base_path_arrivals: str
    base_path_departures: str

    @classmethod
    def from_yaml(cls, path: Path) -> "Config":
        with open(path, "r") as f:
            config = yaml.safe_load(f)
            return Config(**config)


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
        logger.error(f"Database connection error: {str(e)}")
        raise
    finally:
        if conn is not None:
            conn.close()


def list_s3_files(bucket_name: str, prefix: str) -> list[str]:
    """
    List JSON files in an S3 bucket under a specific prefix.
    """
    paginator = s3_client.get_paginator("list_objects_v2")
    files = []
    for page in paginator.paginate(Bucket=bucket_name, Prefix=prefix):
        files.extend([content["Key"] for content in page.get("Contents", []) if content["Key"].endswith(".json")])
    return sorted(files)


def download_s3_file(bucket_name: str, key: str, output_path: Path | str) -> None:
    """
    Download a file from S3 to a local path.
    """
    s3_client.download_file(bucket_name, key, output_path)


def create_dataframe_from_s3_files(filepaths: list[str], bucket_name: str) -> pd.DataFrame:
    """
    Creates a pandas DataFrame from a list of filepaths pointing to JSON files.
    """
    rows = []
    for filepath in filepaths:
        download_s3_file(bucket_name, filepath, "/tmp/temp.json")
        try:
            with open("/tmp/temp.json", "r") as f:
                data = json.load(f)
            for record in data:
                # Skip if arrival_actual_time is missing
                arrival_actual_time = record.get("arrival", {}).get("actualTime")
                if not arrival_actual_time:
                    continue

                arrival_scheduled_time = record.get("arrival", {}).get("scheduledTime")
                arrival_delay = None
                if arrival_scheduled_time:
                    arrival_delay = (
                        datetime.fromisoformat(arrival_actual_time) - datetime.fromisoformat(arrival_scheduled_time)
                    ).total_seconds() // 60

                rows.append(
                    {
                        "flight_number": record.get("flight", {}).get("number"),
                        "arrival_scheduled_time": arrival_scheduled_time,
                        "arrival_actual_time": arrival_actual_time,
                        "arrival_delay": arrival_delay,
                        "departure_iata": record.get("departure", {}).get("iataCode"),
                        "arrival_iata": record.get("arrival", {}).get("iataCode"),
                        "airline_name": record.get("airline", {}).get("name"),
                        "airline_iata": record.get("airline", {}).get("iataCode"),
                    }
                )
        except Exception as e:
            logger.error(f"Error processing file {filepath}: {str(e)}")
    return pd.DataFrame(rows)


def insert_bulk_data_from_dataframe(conn, df: pd.DataFrame) -> None:
    """
    Insert data from a DataFrame into the database.
    """
    csv_buffer = StringIO()
    df.to_csv(csv_buffer, index=False, header=True)
    csv_buffer.seek(0)

    with conn.cursor() as cur:
        cur.copy_expert(
            """
            COPY arrivals (
                flight_number, arrival_scheduled_time, arrival_actual_time, arrival_delay,
                departure_iata, arrival_iata, airline_name, airline_iata
            )
            FROM STDIN WITH CSV HEADER
            """,
            csv_buffer,
        )
    conn.commit()


def lambda_handler(event, context):
    config = Config.from_yaml(Path(__file__).absolute().parent / "config.yaml")
    db_password = os.environ["DB_PASSWORD"]
    date = datetime.now().strftime("%Y-%m-%d")

    with make_db_connection(config, db_password) as conn:
        for base_path in [config.base_path_arrivals, config.base_path_departures]:
            for city in config.cities:
                prefix = f"{base_path}/{city}/"
                filepaths = [
                    key for key in list_s3_files(config.bucket_name, prefix) if date in key
                ]
                if filepaths:
                    logger.info(f"Found {len(filepaths)} files for {city} in {base_path}.")
                    df = create_dataframe_from_s3_files(filepaths, config.bucket_name)
                    if not df.empty:
                        insert_bulk_data_from_dataframe(conn, df)
                        logger.info(f"Inserted data for {city} from {base_path}.")
                    else:
                        logger.warning(f"No data extracted for {city} from {base_path}.")


if __name__ == "__main__":
    lambda_handler(None, None)

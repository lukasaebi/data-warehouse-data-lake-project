import argparse
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
    base_path: str

    @classmethod
    def from_yaml(cls, path: Path) -> "Config":
        with open(path, "r") as f:
            config = yaml.safe_load(f)
            return Config(**config)


@contextmanager
def make_db_connection(config: dict, db_password: str) -> connection:
    """
    Context manager to handle database connection and ensure cleanup.
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
        print({"statusCode": 500, "message": f"Error connecting to RDS: {str(e)}"})
        raise
    finally:
        if conn is not None:
            conn.close()


@contextmanager
def error_handler(conn):
    """
    A context manager to handle database transactions with error handling.
    """
    with conn.cursor() as cur:
        try:
            yield cur
            conn.commit()
        except Exception as e:
            conn.rollback()
            print({"statusCode": 500, "message": f"Database error: {str(e)}"})
            raise


def list_s3_files(bucket_name: str, prefix: str) -> list[str]:
    """
    List files in an S3 bucket under a specific prefix.

    Args:
        bucket_name (str): The name of the S3 bucket.
        prefix (str): The prefix to filter files by.

    Returns:
        list[str]: A list of file keys
    """
    paginator = s3_client.get_paginator("list_objects_v2")
    files = []
    for page in paginator.paginate(Bucket=bucket_name, Prefix=prefix):
        files.extend([content["Key"] for content in page.get("Contents", []) if content["Key"].endswith(".json")])
    return sorted(files)


def download_s3_file(bucket_name: str, key: str, output_path: Path | str) -> None:
    """
    Download a file from S3 to a local path.

    Args:
        bucket_name (str): The name of the S3 bucket.
        key (str): The key of the file in the bucket.
        output_path (Path | str): The path to save the file to.
    """
    s3_client.download_file(bucket_name, key, output_path)


def insert_bulk_data_from_dataframe(conn, df: pd.DataFrame) -> None:
    """
    Insert daily traffic data for a single city using a DataFrame.
    """
    csv_buffer = StringIO()
    df.to_csv(csv_buffer, index=False, header=True)
    csv_buffer.seek(0)

    with conn.cursor() as cur:
        cur.copy_expert(
            """
            COPY road_traffic (date, city, road, length, speed, freeflow, jamfactor)
            FROM STDIN WITH CSV HEADER
            """,
            csv_buffer,
        )
    conn.commit()


def create_bulk_df(filepaths: list[str], bucket_name: str) -> None:
    """
    Creates a `pd.DataFrame` from a list of filepaths pointing to .json files.

    Args:
        filepaths (list[str]): A list of filepaths pointing to .json files.
    """
    total_data = []
    for filepath in filepaths:
        download_s3_file(bucket_name, filepath, "/tmp/temp.json")  # important: lambda can only save to /tmp dir
        with open("/tmp/temp.json", "r") as f:
            data = json.load(f)

        city = filepath.split("/")[-1].split("_")[0]
        date = filepath.split("/")[-1].split("_")[1].replace("--", ":")

        filtered_data = [
            (
                datetime.fromisoformat(date),
                city,
                road["location"].get("description", None),
                road["location"]["length"],
                road["currentFlow"]["speed"],
                road["currentFlow"]["freeFlow"],
                road["currentFlow"]["jamFactor"],
            )
            for road in data
        ]
        total_data.extend(filtered_data)
    return pd.DataFrame(total_data, columns=["date", "city", "road", "length", "speed", "freeflow", "jamfactor"])


def lambda_handler(event, context):
    config = Config.from_yaml(Path(__file__).absolute().parent / "config.yaml")
    db_password = os.environ["DB_PASSWORD"]
    date = datetime.now().strftime("%Y-%m-%d")
    logger.info(f"Data to upload from `{date}`.")

    with make_db_connection(config, db_password) as conn:
        total_filepaths = list_s3_files(config.bucket_name, config.base_path)
        filepaths = [path for path in total_filepaths if f"{date}" in path]  # filter for year and month
        if filepaths:
            logger.info(f"Number of files to upload: {len(filepaths)}")
            df = create_bulk_df(filepaths, config.bucket_name)
            logger.info(f"Dataframe to upload created with shape {df.shape}...")
            insert_bulk_data_from_dataframe(conn, df)
            logger.info("Data successfully inserted into Database.")
            return {
                "statusCode": 200,
                "body": json.dumps(f"Data for `{date}` uploaded to Database successfully."),
            }
        return {"statusCode": 404, "body": json.dumps(f"No data found for {date}. No data uploaded.")}


if __name__ == "__main__":
    lambda_handler(None, None)

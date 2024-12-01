import argparse
import json
import logging
import os
from contextlib import contextmanager
from datetime import datetime
from io import StringIO
from itertools import islice
from pathlib import Path

import boto3
import pandas as pd
import psycopg2
import yaml
from psycopg2.extensions import connection
from pydantic import BaseModel
from tqdm import tqdm

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

s3_client = boto3.client("s3")


class Config(BaseModel):
    cities: list[str]
    host: str
    user: str
    port: int
    dbname: str
    step_size: int
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


def create_table(conn: connection) -> None:
    """
    Create table if it does not exist. Ensures changes are committed.
    """
    with error_handler(conn) as cur:
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS road_traffic (
                id SERIAL PRIMARY KEY,
                date TIMESTAMP,
                city VARCHAR(255),
                road VARCHAR(255),
                length FLOAT,
                speed FLOAT,
                freeflow FLOAT,
                jamfactor FLOAT
            )
            """
        )


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


def delete_table(conn: connection) -> None:
    """
    Delete table if it exists. Ensures changes are committed.
    """
    with error_handler(conn) as cur:
        cur.execute("DROP TABLE IF EXISTS road_traffic")
        conn.commit()


def save_dataframe(path: Path, df: pd.DataFrame) -> None:
    """
    Save a `pd.DataFrame` to a CSV file.

    Args:
        path (Path): The path to save the CSV file.
        df (pd.DataFrame): The DataFrame to save.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)


def lambda_handler(event, context):
    config = Config.from_yaml(Path(__file__).absolute().parent / "config.yaml")
    db_password = os.environ["DB_PASSWORD"]
    drop_table = event.get("drop_table", None)
    step = config.step_size
    year = event.get("year", None)
    month = event.get("month", None)
    logger.info(f"Data to upload from year `{year}` and month `{month}`.")

    with make_db_connection(config, db_password) as conn:
        if drop_table:
            logger.info("Deleting table...")
            delete_table(conn)
            logger.info("Table deleted.")
        create_table(conn)
        total_filepaths = list_s3_files(config.bucket_name, config.base_path)
        filepaths = [path for path in total_filepaths if f"{year}-{month}" in path]  # filter for year and month
        logger.info(f"Number of files to upload: {len(filepaths)}")
        logger.info(f"Files will be uploaded in batches of size {step}.")
        for i in tqdm(range(0, len(filepaths), step), desc="Uploading data to RDS..."):
            filepath_batch = list(islice(filepaths, i, i + step))
            df = create_bulk_df(filepath_batch, config.bucket_name)
            logger.info(f"Iter {i}: Dataframe created.")
            insert_bulk_data_from_dataframe(conn, df)
            logger.info(f"Iter {i}: Data inserted into Database.")

    return {
        "statusCode": 200,
        "body": json.dumps(f"Data for year `{year}` and month `{month}` uploaded to Database successfully."),
    }


def arg_parser():
    parser = argparse.ArgumentParser(description="Load data to RDS.")
    parser.add_argument("--drop-table", action="store_true", help="Drop the table before loading data.")
    parser.add_argument("--year", type=str, help="Year to load data for.")
    parser.add_argument("--month", type=str, help="Month to load data for.")
    return parser.parse_args()


if __name__ == "__main__":
    args = arg_parser()
    event = args.__dict__
    lambda_handler(event, None)

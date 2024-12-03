import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

RDS_HOST = os.getenv("RDS_HOST")
RDS_USER = os.getenv("RDS_USER")
RDS_PASSWORD = os.getenv("RDS_PASSWORD")

# First: connect to default "postgres" database to create the "aviation" database
try:
    conn = psycopg2.connect(
        host=RDS_HOST,
        user=RDS_USER,
        password=RDS_PASSWORD,
        port=5432,
        dbname="postgres",
    )
    conn.autocommit = True

    cursor = conn.cursor()

    # Query to create the "aviation" database if it doesn't exist
    cursor.execute("SELECT 1 FROM pg_database WHERE datname = 'aviation';")
    if not cursor.fetchone():
        cursor.execute("CREATE DATABASE aviation;")
        print("Database 'aviation' has been created successfully.")
    else:
        print("Database 'aviation' already exists.")

except Exception as e:
    print({"statusCode": 500, "message": f"Error connecting to RDS or creating database: {str(e)}"})

finally:
    if "cursor" in locals():
        cursor.close()
    if "conn" in locals():
        conn.close()

# Then: create "arrivals" table
try:
    conn = psycopg2.connect(
        host=RDS_HOST,
        user=RDS_USER,
        password=RDS_PASSWORD,
        port=5432,
        dbname="aviation",
    )
    conn.autocommit = True

    cursor = conn.cursor()

    # Create the arrivals table with the latest schema
    cursor.execute(
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
            arrival_delay INT,
            airline_name VARCHAR(100),
            airline_iata VARCHAR(10),
            CONSTRAINT unique_flight UNIQUE (flight_number, arrival_scheduled_time, arrival_actual_time)
        );
        """
    )
    print("Table 'arrivals' created successfully with the latest constraints.")

except Exception as e:
    print({"statusCode": 500, "message": f"Error creating table: {str(e)}"})

finally:
    if "cursor" in locals():
        cursor.close()
    if "conn" in locals():
        conn.close()



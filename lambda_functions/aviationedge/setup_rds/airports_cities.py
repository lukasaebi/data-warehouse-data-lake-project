import psycopg2
import os
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

RDS_HOST = os.getenv("RDS_HOST")
RDS_USER = os.getenv("RDS_USER")
RDS_PASSWORD = os.getenv("RDS_PASSWORD")

# Create a connection to the RDS instance
try:
    conn = psycopg2.connect(
        host=RDS_HOST,
        user=RDS_USER,
        password=RDS_PASSWORD,
        port=5432,
        dbname="master",
    )
    conn.autocommit = True

    cursor = conn.cursor()

    # Create the "airports" table with the appropriate schema
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS airports (
            id SERIAL PRIMARY KEY,
            city_name VARCHAR(50),
            gmt_offset VARCHAR(10),
            code_iata_airport VARCHAR(10),
            code_iata_city VARCHAR(10),
            code_icao_airport VARCHAR(10),
            code_iso2_country VARCHAR(5),
            latitude DECIMAL(10, 6),
            longitude DECIMAL(10, 6),
            name_airport VARCHAR(100),
            name_country VARCHAR(100),
            phone VARCHAR(50),
            timezone VARCHAR(50)
        );
        """
    )
    print("Table 'airports' created successfully.")

    # Load the JSON data from the local file
    with open('lambda_functions/aviationedge/setup_rds/airport_per_city.json', 'r') as file:
        data = json.load(file)

    # Loop through each city and insert data into the airports table
    for city_name, airports in data.items():
        for airport in airports:
            insert_query = """
                INSERT INTO airports (
                    city_name,
                    gmt_offset,
                    code_iata_airport,
                    code_iata_city,
                    code_icao_airport,
                    code_iso2_country,
                    latitude,
                    longitude,
                    name_airport,
                    name_country,
                    phone,
                    timezone
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """

            values = (
                city_name,
                airport.get("GMT"),
                airport.get("codeIataAirport"),
                airport.get("codeIataCity"),
                airport.get("codeIcaoAirport"),
                airport.get("codeIso2Country"),
                airport.get("latitudeAirport"),
                airport.get("longitudeAirport"),
                airport.get("nameAirport"),
                airport.get("nameCountry"),
                airport.get("phone"),
                airport.get("timezone"),
            )

            # Execute the insertion query
            cursor.execute(insert_query, values)

    # Commit the transaction to the database
    conn.commit()
    print("Data inserted successfully.")

except Exception as e:
    print({"statusCode": 500, "message": f"Error creating table or inserting data: {str(e)}"})

finally:
    if "cursor" in locals():
        cursor.close()
    if "conn" in locals():
        conn.close()

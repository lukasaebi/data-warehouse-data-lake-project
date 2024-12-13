import psycopg2
import yaml
import os
from dotenv import load_dotenv

load_dotenv()

def load_config(config_path="config.yaml"):
    """
    Loads database configuration from a YAML file.
    """
    with open(config_path, "r") as file:
        config = yaml.safe_load(file)
    return config

def refresh_materialized_views(views, db_config):
    """
    Refreshes a list of materialized views in a PostgreSQL database.
    """
    try:
        db_password = os.getenv("DB_PASSWORD")
        if not db_password:
            raise ValueError("Database password not found in .env file.")

        conn = psycopg2.connect(
            host=db_config["host"],
            database=db_config["dbname"],
            user=db_config["user"],
            password=db_password,
            port=db_config.get("port", 5432)
        )

        cursor = conn.cursor()

        for view in views:
            try:
                # Refresh each materialized view
                refresh_query = f"REFRESH MATERIALIZED VIEW {view};"
                cursor.execute(refresh_query)
                print(f"Materialized view '{view}' refreshed successfully.")
            except Exception as view_error:
                print(f"Error refreshing view '{view}': {view_error}")

        conn.commit()

    except Exception as e:
        print(f"Error connecting to the database: {e}")

    finally:
        if 'conn' in locals() and conn:
            cursor.close()
            conn.close()

if __name__ == "__main__":
    config = load_config("config.yaml")
    db_config = config["database"]

    # List of materialized views to refresh
    materialized_views = [
        "flights_departures"
    ]

    refresh_materialized_views(materialized_views, db_config)

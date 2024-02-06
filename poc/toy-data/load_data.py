import pandas as pd
import asyncio
import asyncpg
from google.cloud.sql.connector import Connector
from dotenv import load_dotenv
import os

load_dotenv()

# Download and save the dataset in a Pandas dataframe.
DATASET_URL='https://github.com/GoogleCloudPlatform/python-docs-samples/raw/main/cloud-sql/postgres/pgvector/data/retail_toy_dataset.csv'
pd.set_option('display.max_columns', None)
df = pd.read_csv(DATASET_URL)
df = df.loc[:, ['product_id', 'product_name', 'description', 'list_price']]
df = df.dropna()

async def main():
    # GCP info
    project_id = os.getenv('GCP_PROJECT_ID')
    region = os.getenv('GCP_REGION')
    instance_name = os.getenv('SQL_INSTANCE_ID')

    # Cloud SQL info
    database_user = os.getenv('SQL_DB_USER')
    database_password = os.getenv('SQL_PASSWORD')
    database_name = "toy-data"

    # Save the Pandas dataframe in a PostgreSQL table.
    loop = asyncio.get_running_loop()
    async with Connector(loop=loop) as connector:
        # Create connection to Cloud SQL database
        conn: asyncpg.Connection = await connector.connect_async(
            f"{project_id}:{region}:{instance_name}",  # Cloud SQL instance connection name
            "asyncpg",
            user=f"{database_user}",
            password=f"{database_password}",
            db=f"{database_name}"
        )

        # Create the `products` table.
        await conn.execute("""CREATE TABLE IF NOT EXISTS products(
                                product_id VARCHAR(1024) PRIMARY KEY,
                                product_name TEXT,
                                description TEXT,
                                list_price NUMERIC)""")

        # Copy the dataframe to the `products` table.
        tuples = list(df.itertuples(index=False))

        await conn.copy_records_to_table('products', records=tuples, columns=list(df), timeout=10)
        await conn.close()


# Run the SQL commands now.
# asyncio.run(main()) # type: ignore
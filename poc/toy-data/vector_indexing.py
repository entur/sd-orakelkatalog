from dotenv import load_dotenv
import os

load_dotenv()

project_id = os.getenv('GCP_PROJECT_ID')
region = os.getenv('GCP_REGION')
instance_name = os.getenv('SQL_INSTANCE_ID')

# Cloud SQL info
database_user = os.getenv('SQL_DB_USER')
database_password = os.getenv('SQL_PASSWORD')
database_name = "toy-data"

# @markdown Create an HNSW index on the `product_embeddings` table:
m =  24 # @param {type:"integer"}
ef_construction = 100  # @param {type:"integer"}
operator = "vector_cosine_ops"  # @param ["vector_cosine_ops", "vector_l2_ops", "vector_ip_ops"]

# Quick input validations.
assert m, "⚠️ Please input a valid value for m."
assert ef_construction, "⚠️ Please input a valid value for ef_construction."
assert operator, "⚠️ Please input a valid value for operator."

from pgvector.asyncpg import register_vector
import asyncio
import asyncpg
from google.cloud.sql.connector import Connector


async def main():
    loop = asyncio.get_running_loop()
    async with Connector(loop=loop) as connector:
        # Create connection to Cloud SQL database.
        conn: asyncpg.Connection = await connector.connect_async(
            f"{project_id}:{region}:{instance_name}",  # Cloud SQL instance connection name
            "asyncpg",
            user=f"{database_user}",
            password=f"{database_password}",
            db=f"{database_name}",
        )

        await register_vector(conn)

        # Create an HNSW index on the `product_embeddings` table.
        await conn.execute(
            f"""CREATE INDEX ON product_embeddings
              USING hnsw(embedding {operator})
              WITH (m = {m}, ef_construction = {ef_construction})
            """
        )

        await conn.close()


# Run the SQL commands now.
asyncio.run(main())  # type: ignore

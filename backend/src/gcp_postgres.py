import os
from google.cloud.sql.connector import Connector
import asyncpg
import asyncio

from src.gcp_secret import get_secret
from pgvector.asyncpg import register_vector

similarity_threshold = 0.3
num_matches = 7

project_id = os.environ.get('GCP_PG_PROJECT')
project_region = os.environ.get('GCP_PG_REGION')

db_instance = get_secret('PGINSTANCES')
db_user = get_secret("PGUSER")
db_pass = get_secret("PGPASSWORD")


async def match_datasets(query, db_name):
    """Do text search for FDK datasets"""

    connection_name = f"{project_id}:{project_region}:{db_instance}"
    loop = asyncio.get_running_loop()
    matches = []

    async with Connector(loop=loop) as connector:
        # Create connection to Cloud SQL database.
        conn: asyncpg.Connection = await connector.connect_async(
            connection_name,
            "asyncpg",
            user=f"{db_user}",
            password=f"{db_pass}",
            db=f"{db_name}",
        )

        await register_vector(conn)
        results = await conn.fetch("""
                     WITH vector_matches AS (
                             SELECT id,
                                    1 - (embedding <=> $1) AS similarity
                             FROM dataset_embeddings
                             WHERE 1 - (embedding <=> $1) > $2
                             ORDER BY similarity DESC
                             LIMIT $3
                     )
                     SELECT id,
                            summary
                     FROM datasets
                     WHERE id IN (SELECT id FROM vector_matches)
                     """,
                                   query, similarity_threshold, num_matches)

        for r in results:
            # Collect the description for all the matched similar toy products.
            matches.append(r["summary"])

        return matches


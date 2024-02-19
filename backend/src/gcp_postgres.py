# Samples based on GoogleCloudPlatform/python-docs-samples/cloud-sql/postgres/sqlalchemy/app.py

import os
from google.cloud.sql.connector import Connector, IPTypes
import asyncpg
import asyncio

import sqlalchemy
from sqlalchemy.ext.asyncio import create_async_engine, AsyncEngine, AsyncSession
from src.gcp_secret import get_secret
from pgvector.asyncpg import register_vector

similarity_threshold = 0.5
num_matches = 5

project_id = os.environ.get('GCP_PG_PROJECT')
project_region = os.environ.get('GCP_PG_REGION')

db_instance = get_secret('PGINSTANCES')
db_user = get_secret("PGUSER")
db_pass = get_secret("PGPASSWORD")
db_name = "fdk-v1"


def connect_with_connector() -> sqlalchemy.ext.asyncio.AsyncEngine:
    """
    Initializes a connection pool for a Cloud SQL instance of Postgres.

    Uses the Cloud SQL Python Connector package.
    """


    connection_name = f"{project_id}:{project_region}:{db_instance}"
    ip_type = IPTypes.PRIVATE if os.environ.get("PRIVATE_IP") else IPTypes.PUBLIC

    loop = asyncio.get_running_loop()
    # initialize Cloud SQL Python Connector object
    connector = Connector()

    async def getconn() -> asyncpg.Connection:
        conn: asyncpg.Connection = connector.connect(
            connection_name,
            "asyncpg",
            user=db_user,
            password=db_pass,
            db=db_name,
            ip_type=ip_type,
        )
        return conn

    # The Cloud SQL Python Connector can be used with SQLAlchemy
    # using the 'creator' argument to 'create_engine'
    pool = create_async_engine(
        "postgresql+asyncpg://",
        async_creator=getconn,
        echo=True,
        future=True
    )

    return pool


async def match_datasets(db: AsyncEngine, query):
    """Do text search for FDK datasets"""
    async with AsyncSession(db) as conn:

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

        return results


async def match_datasets(query):
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


from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_google_vertexai import VertexAIEmbeddings
from google.cloud import aiplatform
from google.cloud.sql.connector import Connector
from pgvector.asyncpg import register_vector
import pandas as pd
import asyncio
import asyncpg
import numpy as np
from etl import transform
from dotenv import load_dotenv
import os

load_dotenv()


# GCP info
project_id = os.getenv('GCP_PROJECT_ID')
region = os.getenv('GCP_REGION')
instance_name = os.getenv('SQL_INSTANCE_ID')

# Cloud SQL info
database_user = os.getenv('SQL_DB_USER')
database_password = os.getenv('SQL_PASSWORD')
database_name = "fdk-v3"

# Indexing info
m = 24
ef_construction = 100
operator = "vector_cosine_ops"


def readDatasets():
    return transform()


def make_embeddings(df):
    print("Starter uthenting av text-embeddings")
    text_splitter = RecursiveCharacterTextSplitter(
        separators = [".", "\n"],
        chunk_size = 500,
        chunk_overlap  = 0,
        length_function = len,
    )
    chunked = []

    for index, row in df.iterrows():
        id = row['id']
        summary = row['summary']
        splits = text_splitter.create_documents([summary])
        for s in splits:
            r = {'id': id, 'content': s.page_content}
            chunked.append(r)

    aiplatform.init(project=f"{project_id}", location=f"{region}")
    embeddings_service = VertexAIEmbeddings(model_name="textembedding-gecko-multilingual@001")

    batch_size = 5
    for i in range(0, len(chunked), batch_size):
        request = [x['content'] for x in chunked[i: i + batch_size]]
        response = embeddings_service.embed_documents(request)
        for x, e in zip(chunked[i : i + batch_size], response):
            x["embedding"] = e

    dataset_embeddings = pd.DataFrame(chunked)
    print(dataset_embeddings.head())
    return dataset_embeddings


async def write_embeddings(dataset_embeddings):
    print(f"Laster opp embeddings til {database_name}")
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

        await conn.execute("CREATE EXTENSION IF NOT EXISTS vector")
        await register_vector(conn)

        await conn.execute("DROP TABLE IF EXISTS dataset_embeddings")

        # Create the `dataset_embeddings` table to store vector embeddings.
        await conn.execute(
            """CREATE TABLE dataset_embeddings(
                                id VARCHAR(200) NOT NULL REFERENCES datasets(id),
                                content TEXT,
                                embedding vector(768))"""
        )

        # Store all the generated embeddings back into the database.
        for index, row in dataset_embeddings.iterrows():
            await conn.execute(
                "INSERT INTO dataset_embeddings (id, content, embedding) VALUES ($1, $2, $3)",
                row["id"],
                row["content"],
                np.array(row["embedding"]),
            )

        # Create an HNSW index on the `dataset_embeddings` table.
        print("Oppretter index for raskere søk")
        await conn.execute(
            f"""CREATE INDEX ON dataset_embeddings
              USING hnsw(embedding {operator})
              WITH (m = {m}, ef_construction = {ef_construction})
            """
        )

        await conn.close()

# Main sequence
#df_datasets, df_distributions = readDatasets()
#dataset_embeddings = make_embeddings(df_datasets)
#asyncio.run(writeGCP(dataset_embeddings))  # type: ignore

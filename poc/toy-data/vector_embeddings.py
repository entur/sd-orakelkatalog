from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings import VertexAIEmbeddings
from google.cloud import aiplatform
from google.cloud.sql.connector import Connector
from pgvector.asyncpg import register_vector
import pandas as pd
import asyncio
import asyncpg
import numpy as np
from dotenv import load_dotenv
import os

# Download and save the dataset in a Pandas dataframe.
DATASET_URL='https://github.com/GoogleCloudPlatform/python-docs-samples/raw/main/cloud-sql/postgres/pgvector/data/retail_toy_dataset.csv'
pd.set_option('display.max_columns', None)
df = pd.read_csv(DATASET_URL)
df = df.loc[:, ['product_id', 'product_name', 'description', 'list_price']]
df = df.dropna()

load_dotenv()

project_id = os.getenv('GCP_PROJECT_ID')
region = os.getenv('GCP_REGION')
instance_name = os.getenv('SQL_INSTANCE_ID')

# Cloud SQL info
database_user = os.getenv('SQL_DB_USER')
database_password = os.getenv('SQL_PASSWORD')
database_name = "toy-data"

text_splitter = RecursiveCharacterTextSplitter(
    separators = [".", "\n"],
    chunk_size = 500,
    chunk_overlap  = 0,
    length_function = len,
)
chunked = []

for index, row in df.iterrows():
    product_id = row['product_id']
    desc = row['description']
    splits = text_splitter.create_documents([desc])
    for s in splits:
        r = { 'product_id': product_id, 'content': s.page_content }
        chunked.append(r)


aiplatform.init(project=f"{project_id}", location=f"{region}")
embeddings_service = VertexAIEmbeddings()

batch_size = 5
for i in range(0, len(chunked), batch_size):
    request = [x['content'] for x in chunked[i: i + batch_size]]
    response = embeddings_service.embed_documents(request)
    for x, e in zip(chunked[i : i + batch_size], response):
        x["embedding"] = e

product_embeddings = pd.DataFrame(chunked)
print(product_embeddings.head())


async def writeGCP():
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

        await conn.execute("DROP TABLE IF EXISTS product_embeddings")
        # Create the `product_embeddings` table to store vector embeddings.
        await conn.execute(
            """CREATE TABLE product_embeddings(
                                product_id VARCHAR(1024) NOT NULL REFERENCES products(product_id),
                                content TEXT,
                                embedding vector(768))"""
        )

        # Store all the generated embeddings back into the database.
        for index, row in product_embeddings.iterrows():
            await conn.execute(
                "INSERT INTO product_embeddings (product_id, content, embedding) VALUES ($1, $2, $3)",
                row["product_id"],
                row["content"],
                np.array(row["embedding"]),
            )

        await conn.close()

# asyncio.run(writeGCP())  # type: ignore



from langchain.chains.summarize import load_summarize_chain
from langchain.docstore.document import Document
from langchain_google_vertexai import VertexAIEmbeddings, VertexAI
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from google.cloud.sql.connector import Connector
from pgvector.asyncpg import register_vector
from google.cloud import aiplatform
import pandas as pd
import asyncio
import asyncpg
from dotenv import load_dotenv
import os

load_dotenv()

# USER QUERY
user_query = "Jeg trenger data om tilskudd til poteter"

# GCP info
project_id = os.getenv('GCP_PROJECT_ID')
region = os.getenv('GCP_REGION')
instance_name = os.getenv('SQL_INSTANCE_ID')

# Cloud SQL info
database_user = os.getenv('SQL_DB_USER')
database_password = os.getenv('SQL_PASSWORD')
database_name = "fdk-v1"

# Query info
num_matches = 10
similarity_threshold = 0.5

aiplatform.init(project=f"{project_id}", location=f"{region}")

# Generate vector embedding for the user query.
embeddings_service = VertexAIEmbeddings(model_name="textembedding-gecko-multilingual@001")
qe = embeddings_service.embed_query(user_query)

matches = []


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

        # Use cosine similarity search to find the top five products
        # that are most closely related to the input query.

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
                                   qe, similarity_threshold, num_matches)

        if len(results) == 0:
            print("Dessverre fant vi ikke noe matchende datasett.")

        for r in results:
            # Collect the description for all the matched similar toy products.
            matches.append(r["summary"])

        await conn.close()

asyncio.run(main())

llm = VertexAI()

map_prompt_template = """
        

              You will be given a detailed description of a published dataset in norwegian.
              This description is enclosed in triple backticks (```).
              Using this description only, extract the title of the dataset,
              the category and its most useful features.

              ```{text}```
              SUMMARY:
              """
map_prompt = PromptTemplate(template=map_prompt_template, input_variables=["text"])

combine_prompt_template = """
                You will be given a detailed description of different datasets in norwegian
                enclosed in triple backticks (```) and a question enclosed in
                double backticks(``).
                Select one dataset that is most relevant to answer the question.
                Using that selected dataset description, answer the following
                question in as much detail as possible.
                You should only use the information in the description.
                Your answer should include the title of the dataset, the price of
                the toy and its features. 
                Your answer should be less than 200 words.
                If no datasets are given, assume there are no datasets matching the
                question and give a satisfying explanation to the user.
                Give the answer in Norwegian.

                Description:
                ```{text}```


                Question:
                ``{user_query}``


                Answer:
                """

combine_prompt = PromptTemplate(template=combine_prompt_template, input_variables=["text", "user_query"])

docs = [Document(page_content=t) for t in matches]
chain = load_summarize_chain(llm,
                             chain_type="map_reduce",
                             map_prompt=map_prompt,
                             combine_prompt=combine_prompt)
answer = chain.invoke({
    'input_documents': docs,
    'user_query': user_query,
}, return_only_outputs=True)

print(f"QUESTION: {user_query}")
print(f"ANSWER: {answer['output_text']}")

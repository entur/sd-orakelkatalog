from langchain.chains.summarize import load_summarize_chain
from langchain.docstore.document import Document
from langchain_google_vertexai import VertexAIEmbeddings, VertexAI
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from IPython.display import display, Markdown
from google.cloud.sql.connector import Connector
from pgvector.asyncpg import register_vector
from google.cloud import aiplatform
import pandas as pd
import asyncio
import asyncpg
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

# Query info
min_price = 10
max_price = 100
num_matches = 10
similarity_threshold = 0.5
user_query = "Do you have any toys for babies under 12 months?"

aiplatform.init(project=f"{project_id}", location=f"{region}")

# Generate vector embedding for the user query.
embeddings_service = VertexAIEmbeddings()
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
                             SELECT product_id, 
                                    1 - (embedding <=> $1) AS similarity
                             FROM product_embeddings
                             WHERE 1 - (embedding <=> $1) > $2
                             ORDER BY similarity DESC
                             LIMIT $3
                     )
                     SELECT product_name, 
                            list_price, 
                            description 
                     FROM products
                     WHERE product_id IN (SELECT product_id FROM vector_matches)
                     """,
                                   qe, similarity_threshold, num_matches)

        if len(results) == 0:
            print("Unfortunately, we do not have a toy for this.")

        for r in results:
            # Collect the description for all the matched similar toy products.
            matches.append(
                f"""The name of the toy is {r["product_name"]}.
                          The price of the toy is ${round(r["list_price"], 2)}.
                          Its description is below:
                          {r["description"]}."""
            )

        await conn.close()

asyncio.run(main())
print(matches[0])

llm = VertexAI()

map_prompt_template = """
              You will be given a detailed description of a toy product.
              This description is enclosed in triple backticks (```).
              Using this description only, extract the name of the toy,
              the price of the toy and its features.

              ```{text}```
              SUMMARY:
              """
map_prompt = PromptTemplate(template=map_prompt_template, input_variables=["text"])

combine_prompt_template = """
                You will be given a detailed description different toy products
                enclosed in triple backticks (```) and a question enclosed in
                double backticks(``).
                Select one toy that is most relevant to answer the question.
                Using that selected toy description, answer the following
                question in as much detail as possible.
                You should only use the information in the description.
                Your answer should include the name of the toy, the price of
                the toy and its features. 
                Your answer should be less than 200 words.
                If no toys are given, assume there are no toys matching the question and give a satisfying
                explanation to the user.
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

print(answer["output_text"])

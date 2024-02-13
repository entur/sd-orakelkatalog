from langchain_google_vertexai import VertexAIEmbeddings, VertexAI
from langchain.chains.summarize import load_summarize_chain
from langchain.prompts import PromptTemplate
from src.gcp_vertex_prompts import map_prompt_template, combine_prompt_template
from google.cloud import aiplatform
import os


aiplatform.init(project=f"{os.environ.get('GCP_PROJECT')}", location=f"{os.environ.get('GCP_REGION')}")

embeddings_service = VertexAIEmbeddings(model_name="textembedding-gecko-multilingual@001")
llm = VertexAI(model_name="text-bison", max_output_tokens=1000)

map_prompt = PromptTemplate(template=map_prompt_template, input_variables=["text"])
combine_prompt = PromptTemplate(template=combine_prompt_template, input_variables=["text", "user_query"])
chain = load_summarize_chain(llm, chain_type="map_reduce", map_prompt=map_prompt, combine_prompt=combine_prompt)


def embedding(query):
    return embeddings_service.embed_query(query)


def invoke(docs, query):
    return chain.invoke({
        'input_documents': docs,
        'user_query': query,
    }, return_only_outputs=True)

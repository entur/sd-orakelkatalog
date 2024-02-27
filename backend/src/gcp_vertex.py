from langchain_google_vertexai import VertexAIEmbeddings, VertexAI
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from src.gcp_vertex_prompts import dataset_prompt_template_v3, dataset_prompt_template_v2, dataset_prompt_template_v1, keyword_generation_prompt
from google.cloud import aiplatform
import os


aiplatform.init(project=f"{os.environ.get('GCP_PROJECT')}", location=f"{os.environ.get('GCP_REGION')}")

embeddings_service = VertexAIEmbeddings(model_name="textembedding-gecko-multilingual@001")
llm = VertexAI(model_name="text-bison@002", max_output_tokens=1000, top_k=1)

dataset_prompt_v3 = PromptTemplate(template=dataset_prompt_template_v3, input_variables=["text", "user_query"])
dataset_prompt_v2 = PromptTemplate(template=dataset_prompt_template_v2, input_variables=["text", "user_query"])
dataset_prompt_v1 = PromptTemplate(template=dataset_prompt_template_v1, input_variables=["text", "user_query"])
keyword_prompt = PromptTemplate(template=keyword_generation_prompt, input_variables=["query"])
dataset_chain_v3 = LLMChain(llm=llm, prompt=dataset_prompt_v3)
dataset_chain_v2 = LLMChain(llm=llm, prompt=dataset_prompt_v2)
dataset_chain_v1 = LLMChain(llm=llm, prompt=dataset_prompt_v1)
chain_keyword = LLMChain(llm=llm, prompt=keyword_prompt)


def embedding(query):
    return embeddings_service.embed_query(query)


async def gen_keywords(query):
    return await chain_keyword.ainvoke({
        'query': query
    }, return_only_outputs=True)


async def invoke(docs, query, version):
    if version == "fdk-v1":
        chain = dataset_chain_v1
    elif version == "fdk-v2":
        chain = dataset_chain_v2
    elif version == "fdk-v3":
        chain = dataset_chain_v3
    else:
        return

    return await chain.ainvoke({
        'text': docs,
        'user_query': query,
    }, return_only_outputs=True)

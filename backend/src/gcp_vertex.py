from langchain_google_vertexai import VertexAIEmbeddings, VertexAI
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from src.gcp_vertex_prompts import combine_prompt_template_v1, combine_prompt_template_v2, keyword_generation_prompt
from google.cloud import aiplatform
import os


aiplatform.init(project=f"{os.environ.get('GCP_PROJECT')}", location=f"{os.environ.get('GCP_REGION')}")

embeddings_service = VertexAIEmbeddings(model_name="textembedding-gecko-multilingual@001")
llm = VertexAI(model_name="text-bison@002", max_output_tokens=1000, top_k=1)

combine_prompt_v1 = PromptTemplate(template=combine_prompt_template_v1, input_variables=["text", "user_query"])
combine_prompt_v2 = PromptTemplate(template=combine_prompt_template_v2, input_variables=["text", "user_query"])
keyword_prompt = PromptTemplate(template=keyword_generation_prompt, input_variables=["query"])
chain_v1 = LLMChain(llm=llm, prompt=combine_prompt_v1)
chain_v2 = LLMChain(llm=llm, prompt=combine_prompt_v2)
chain_keyword = LLMChain(llm=llm, prompt=keyword_prompt)


def embedding(query):
    return embeddings_service.embed_query(query)


async def gen_keywords(query):
    return await chain_keyword.ainvoke({
        'query': query
    }, return_only_outputs=True)


async def invoke(docs, query, version):
    if version == "fdk-v1":
        chain = chain_v1
    elif version == "fdk-v2":
        chain = chain_v2
    else:
        return

    return await chain.ainvoke({
        'text': docs,
        'user_query': query,
    }, return_only_outputs=True)

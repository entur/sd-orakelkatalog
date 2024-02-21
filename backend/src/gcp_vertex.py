from langchain_google_vertexai import VertexAIEmbeddings, VertexAI
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from src.gcp_vertex_prompts import combine_prompt_template_v1, combine_prompt_template_v2
from google.cloud import aiplatform
import os


aiplatform.init(project=f"{os.environ.get('GCP_PROJECT')}", location=f"{os.environ.get('GCP_REGION')}")

embeddings_service = VertexAIEmbeddings(model_name="textembedding-gecko-multilingual@001")
llm = VertexAI(model_name="text-bison", max_output_tokens=1000)

combine_prompt_v1 = PromptTemplate(template=combine_prompt_template_v1, input_variables=["text", "user_query"])
combine_prompt_v2 = PromptTemplate(template=combine_prompt_template_v2, input_variables=["text", "user_query"])
chain_v1 = LLMChain(llm=llm, prompt=combine_prompt_v1)
chain_v2 = LLMChain(llm=llm, prompt=combine_prompt_v2)


def embedding(query):
    return embeddings_service.embed_query(query)


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

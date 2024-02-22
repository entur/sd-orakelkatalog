from fastapi import APIRouter, Request, Response
from src.gcp_postgres import match_datasets
from src.gcp_vertex import embedding, invoke, gen_keywords
from langchain.docstore.document import Document

router = APIRouter()

# db = connect_with_connector()


@router.post("/llm/v1")
async def llm_v1(request: Request, response: Response):
    body = await request.json()

    if "query" not in body:
        response.status_code = 400
        return response

    query_text = str(body["query"])
    llm_answer = await llm_query(query_text, "fdk-v1")
    return llm_answer["text"]


@router.post("/llm/v2")
async def llm_v1(request: Request, response: Response):
    body = await request.json()

    if "query" not in body:
        response.status_code = 400
        return response

    query_text = str(body["query"])
    llm_answer = await llm_query(query_text, "fdk-v2")
    return llm_answer["text"]


async def llm_query(query_text, llm_version):
    gen_query = await gen_keywords(query_text)
    processed_queries = preprocess_queries(query_text, gen_query["text"])

    query = embedding(processed_queries)
    matches = await match_datasets(query, llm_version)
    docs = [Document(page_content=t) for t in matches]
    answer = await invoke(docs, query_text, llm_version)
    return answer


def preprocess_queries(original_query, generated_queries):
    query = f"{original_query}\n{generated_queries}"
    query = query.replace("\n", " ")
    query = query.replace("-", " ")
    return query.strip()

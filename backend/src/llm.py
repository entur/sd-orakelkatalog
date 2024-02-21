from fastapi import APIRouter, Request, Response
from src.gcp_postgres import match_datasets
from src.gcp_vertex import embedding, invoke
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
    query = embedding(query_text)
    matches = await match_datasets(query, llm_version)

    docs = [Document(page_content=t) for t in matches]
    answer = await invoke(docs, query_text, llm_version)
    return answer

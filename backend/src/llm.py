from fastapi import APIRouter, Request
from src.gcp_postgres import connect_with_connector, match_datasets
from src.gcp_vertex import embedding, invoke
from langchain.docstore.document import Document
# import asyncio

router = APIRouter()

# db = connect_with_connector()


@router.post("/test")
async def llm_queryt(request: Request):
    print(await request.body())
    return


@router.post("/llmtest")
async def llm_query(request: Request):
    body = await request.json()
    query_text = str(body["query"])
    query = embedding(query_text)

    matches = await match_datasets(query)

    docs = [Document(page_content=t) for t in matches]
    answer = invoke(docs, query_text)
    return answer["output_text"]

from fastapi import APIRouter, Request, Response
from src.gcp_postgres import connect_with_connector, match_datasets
from src.gcp_vertex import embedding, invoke
from langchain.docstore.document import Document
# import asyncio

router = APIRouter()

# db = connect_with_connector()


@router.post("/llmtest")
async def llm_query(request: Request, response: Response):
    body = await request.json()

    if "query" not in body:
        response.status_code = 400
        return response

    query_text = str(body["query"])
    query = embedding(query_text)

    matches = await match_datasets(query)

    docs = [Document(page_content=t) for t in matches]
    answer = await invoke(docs, query_text)
    #return answer["output_text"]
    return answer["text"]

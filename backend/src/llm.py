from fastapi import APIRouter, Request, Response
from src.gcp_postgres import match_datasets
from src.gcp_vertex import embedding, invoke, gen_keywords

router = APIRouter()


@router.post("/llm/v1")
async def llm_v1(request: Request, response: Response):
    body = await request.json()

    if "query" not in body:
        response.status_code = 400
        return response

    query_text = str(body["query"])
    llm_answer, titles, links = await llm_query(query_text, "fdk-v1")
    return {'llm': llm_answer["text"], 'links': links, 'titles': titles}


@router.post("/llm/v2")
async def llm_v1(request: Request, response: Response):
    body = await request.json()

    if "query" not in body:
        response.status_code = 400
        return response

    query_text = str(body["query"])
    llm_answer, titles, links = await llm_query(query_text, "fdk-v2")
    return {'llm': llm_answer["text"], 'links': links, 'titles': titles}


@router.post("/llm/v3")
async def llm_v1(request: Request, response: Response):
    body = await request.json()

    if "query" not in body:
        response.status_code = 400
        return response

    query_text = str(body["query"])
    llm_answer, titles, links = await llm_query(query_text, "fdk-v3")
    return {'llm': llm_answer["text"], 'links': links, 'titles': titles}


async def llm_query(query_text, llm_version):
    gen_query = await gen_keywords(query_text)
    processed_queries = preprocess_queries(query_text, gen_query["text"])

    query = embedding(processed_queries)
    matches, results = await match_datasets(query, llm_version)

    titles = [r["title"].upper() for r in results if "title" in r]
    links = [r["link"] for r in results if "link" in r]

    # docs = [Document(page_content=t) for t in matches]
    answer = await invoke(matches, query_text, llm_version)
    return answer, titles, links


def preprocess_queries(original_query, generated_queries):
    query = f"{original_query}\n{generated_queries}"
    query = query.replace("\n", " ")
    query = query.replace("-", " ")
    return query.strip()

import asyncio
from etl import extract, transform, load
from embeddings import make_embeddings, write_embeddings


"""

Entrypoint for oppsett av metadata til Postgres.
Kjør denne filen for å gjøre alt av oppsett for FDK-LLM. 

"""


async def main():

    # Transform and upload data.norge metadata
    extract()
    df_datasets = transform()
    await load(df_datasets)

    # Make and upload summary embeddings
    dataset_embeddings = make_embeddings(df_datasets)
    await write_embeddings(dataset_embeddings)  # type: ignore

asyncio.run(main())

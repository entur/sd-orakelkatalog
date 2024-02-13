"""Simple rocket-launch application.

This application creates an API endpoint using `FastAPI`_ to
print out a meaningful message.

.. _FastAPI:
   https://fastapi.tiangolo.com/

"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator

from src import gcp_secret
from src import llm
from src import health

app = FastAPI(
    title="FDK Orakel Backend",
    description="Backendtjeneste for FDK Orakel",
    version="0.1.1",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(gcp_secret.router)
app.include_router(llm.router)

Instrumentator().instrument(app).expose(app)

"""Create endpoints for liveness and readiness probes.

See `Kubernetes documentation`_

.. _Kubernetes documentation:
   https://kubernetes.io/docs/tasks/configure-pod-container/configure-liveness-readiness-startup-probes/
"""

from fastapi import APIRouter

router = APIRouter()


@router.get("/health/alive")
async def alive():
    return {"status": "I'm not dead!"}


@router.get("/health/ready")
async def ready():
    return {"status": "Ready"}

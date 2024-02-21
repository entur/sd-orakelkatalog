"""Easily access secrets from our secretmanager"""

from google.cloud import secretmanager
import google_crc32c
import os
from fastapi import APIRouter

router = APIRouter()


class SecretCRCFail(Exception):
    "Rasied when CRC fails for a secret"
    pass


def get_secret(secret_name):
    """Get a secret by name, may raise exceptions"""
    client = secretmanager.SecretManagerServiceClient()
    secret = f"secrets/{secret_name}/versions/latest"
    name = f"projects/{os.environ.get('GCP_PROJECT')}/{secret}"
    response = client.access_secret_version(request={"name": name})

    # verify checksum
    crc32c = google_crc32c.Checksum()
    crc32c.update(response.payload.data)
    if response.payload.data_crc32c != int(crc32c.hexdigest(), 16):
        raise SecretCRCFail(f"CRC check failed for secret {secret_name}")

    message = response.payload.data.decode("UTF-8")
    return message


def get_secret_or_default(secret_name, default="SECRET_NOT_SET"):
    """Get a secret by name, default if none found"""
    try:
        return get_secret(secret_name)
    except Exception as e:
        print(e)
        return default

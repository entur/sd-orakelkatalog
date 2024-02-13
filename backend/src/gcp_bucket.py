"""Create endpoint for /hello"""

from os import environ
from fastapi import APIRouter
from google.cloud import storage

router = APIRouter()

# simple app that gets contents from a bucket and caches it
cache = dict()


def download_bucket_object(blob_name):
    if "BUCKET_NAME" not in environ:
        return "ERROR - BUCKET_NAME environment variable must be set"
    else:
        try:
            # Create storage client using the default credentials
            storage_client = storage.Client()
        except:
            return "No credentials/access"
        else:
            print("downloading {blob_name} from bucket...")
            # Download without granting bucket.list permissions to the service account
            blob = storage_client.bucket(environ["BUCKET_NAME"]).get_blob(blob_name)
            blob_string = blob.download_as_bytes()
            blob_string = blob_string.decode("utf-8")
            return blob_string


def get_bucket_object(blob_name):
    if blob_name not in cache:
        cache[blob_name] = download_bucket_object(blob_name)
    return cache[blob_name]


@router.get("/")
async def rocket():
    """Returns blob content"""
    return get_bucket_object("rocket.txt")

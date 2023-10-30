import os
import dotenv
import logging
import json
import time

from google.cloud import storage
from google.cloud.exceptions import NotFound

dotenv.load_dotenv()

GCS_BUCKET_NAME = os.getenv('GCS_BUCKET_NAME')

GCS_APPLICATION_CREDENTIALS = {
    "project_id": os.getenv('GCS_PROJECT_ID'),
    "private_key_id": os.getenv('GCS_PRIVATE_KEY_ID'),
    "private_key": os.getenv('GCS_PRIVATE_KEY'),
    "client_email": os.getenv('GCS_CLIENT_EMAIL'),
    "client_id": os.getenv('GCS_CLIENT_ID'),
    "token_uri": os.getenv('GCS_TOKEN_URI')
}

class GCSAdapter:
    def __init__(self, bucket_name=GCS_BUCKET_NAME):
        self.client = storage.Client.from_service_account_info(GCS_APPLICATION_CREDENTIALS)
        self.bucket = self.client.bucket(bucket_name)

    def get(self, key):
        start_time = time.time()
        logging.info(f"Fetching {key} from GCS bucket {self.bucket.name}.")
        try:
            blob = self.bucket.blob(key)
            json_data = blob.download_as_text()
            logging.info(f"Fetched {key} from GCS bucket {self.bucket.name} in {(time.time() - start_time):.2f} seconds.")
            return json.loads(json_data)
        except NotFound:
            logging.info(f"Could not find {key} in GCS bucket {self.bucket}, returning an empty list...")
            return []
        except Exception as e:
            logging.error(f"Error fetching {key} from GCS bucket {self.bucket.name}: {e}")
            raise e

    def put(self, data, key) -> None:
        start_time = time.time()
        updated_json_data = json.dumps(data, indent=2)
        logging.info(f"Uploading {key} to GCS bucket {self.bucket.name}.")
        blob = self.bucket.blob(key)
        blob.upload_from_string(updated_json_data, content_type="application/json")
        logging.info(f"Uploaded {key} to GCS bucket {self.bucket.name} in {(time.time() - start_time):.2f} seconds.")
        return

    def append(self, data, key):
        start_time = time.time()

        logging.info(f"Appending data to {key} in GCS bucket {self.bucket.name}...")

        existing_data = self.get(key)
        if isinstance(data, dict):
            updated_data = {**existing_data, **data}
        elif isinstance(data, list):
            updated_data = existing_data + data

        self.put(updated_data, key)

        logging.info(f"Appended {key} to GCS bucket {self.bucket.name} in {(time.time() - start_time):.2f} seconds.")
        return
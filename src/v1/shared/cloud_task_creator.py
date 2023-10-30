import os

import datetime
import json
from typing import Dict, Optional

from google.cloud import tasks_v2
from google.protobuf import duration_pb2, timestamp_pb2
import google.oauth2.id_token

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "./key.json"

if "key.json" not in os.listdir("./"):
    raise Exception("No GCP key.json file found")

RUG_CF_PROJECT_NAME = os.getenv("RUG_CF_PROJECT_NAME")
RUG_CF_LOCATION = os.getenv("RUG_CF_LOCATION")
RUG_CF_QUEUE_NAME = os.getenv("RUG_CF_QUEUE_NAME")
RUG_CF_QUEUE_URL = os.getenv("RUG_CF_QUEUE_URL")


def create_http_task_rug_cf(
    json_payload: Dict,
    scheduled_seconds_from_now: Optional[int] = None,
    task_id: Optional[str] = None,
    deadline_in_seconds: Optional[int] = None,
) -> tasks_v2.Task:
    """Create an HTTP POST task with a JSON payload.
    Args:
        project: The project ID where the queue is located.
        location: The location where the queue is located.
        queue: The ID of the queue to add the task to.
        url: The target URL of the task.
        json_payload: The JSON payload to send.
        scheduled_seconds_from_now: Seconds from now to schedule the task for.
        task_id: ID to use for the newly created task.
        deadline_in_seconds: The deadline in seconds for task.
    Returns:
        The newly created task.
    """

    # Create a client.
    client = tasks_v2.CloudTasksClient()

    auth_req = google.auth.transport.requests.Request()
    id_token = google.oauth2.id_token.fetch_id_token(auth_req, RUG_CF_QUEUE_URL)

    # Construct the task.
    task = tasks_v2.Task(
        http_request=tasks_v2.HttpRequest(
            http_method=tasks_v2.HttpMethod.POST,
            url=RUG_CF_QUEUE_URL,
            headers={
                "Content-type": "application/json",
                "Authorization": f"Bearer {id_token}",
            },
            body=json.dumps(json_payload).encode(),
        ),
        name=(
            client.task_path(
                RUG_CF_PROJECT_NAME, RUG_CF_LOCATION, RUG_CF_QUEUE_NAME, task_id
            )
            if task_id is not None
            else None
        ),
    )

    # Convert "seconds from now" to an absolute Protobuf Timestamp
    if scheduled_seconds_from_now is not None:
        timestamp = timestamp_pb2.Timestamp()
        timestamp.FromDatetime(
            datetime.datetime.utcnow()
            + datetime.timedelta(seconds=scheduled_seconds_from_now)
        )
        task.schedule_time = timestamp

    # Convert "deadline in seconds" to a Protobuf Duration
    if deadline_in_seconds is not None:
        duration = duration_pb2.Duration()
        duration.FromSeconds(deadline_in_seconds)
        task.dispatch_deadline = duration

    # Use the client to send a CreateTaskRequest.
    return client.create_task(
        tasks_v2.CreateTaskRequest(
            # The queue to add the task to
            parent=client.queue_path(
                RUG_CF_PROJECT_NAME, RUG_CF_LOCATION, RUG_CF_QUEUE_NAME
            ),
            # The task itself
            task=task,
        )
    )

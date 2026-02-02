import logging
import json
import os
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from azure.servicebus import ServiceBusClient, ServiceBusMessage
from azure.storage.queue import QueueClient
from dotenv import load_dotenv
from prometheus_fastapi_instrumentator import Instrumentator

# ======================
# SETUP
# ======================
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()
Instrumentator().instrument(app).expose(app)

load_dotenv()

SERVICE_BUS_CONNECTION_STR = os.environ.get("AZURE_SERVICE_BUS_CONNECTION_STRING")
QUEUE_NAME = os.environ.get("QUEUE_NAME")

STORAGE_QUEUE_CONNECTION_STR = os.environ.get("AZURE_STORAGE_QUEUE_CONNECTION_STRING")
STORAGE_QUEUE_NAME = os.environ.get("AZURE_STORAGE_QUEUE_NAME")

# ======================
# MODELS
# ======================

class RatingRequest(BaseModel):
    sessionId: int
    rating: int

# ======================
# HELPERS
# ======================

def send_to_storage_queue(message: str):
    try:
        queue_client = QueueClient.from_connection_string(
            STORAGE_QUEUE_CONNECTION_STR, STORAGE_QUEUE_NAME
        )
        queue_client.send_message(message)
        logger.info("Message sent to Azure Storage Queue.")
    except Exception as e:
        logger.error(f"Failed to send message to Storage Queue: {e}")

# ======================
# ENDPOINTS
# ======================

@app.get("/health")
def healthcheck():
    return JSONResponse(content={"status": "ok"})

@app.post("/rate")
def rate(request: RatingRequest):
    logger.info(f"Received rating: {request.sessionId} -> {request.rating}")

    message_data = {
        "sessionId": request.sessionId,
        "rating": request.rating,
        "source": "photographer-service"
    }

    message_json = json.dumps(message_data)

    try:
        with ServiceBusClient.from_connection_string(SERVICE_BUS_CONNECTION_STR) as client:
            sender = client.get_queue_sender(queue_name=QUEUE_NAME)
            with sender:
                sender.send_messages(ServiceBusMessage(message_json))

        send_to_storage_queue(json.dumps({
            "status": "success",
            "sessionId": request.sessionId
        }))

        return JSONResponse(content={"message": "Rating sent to queue"})

    except Exception as e:
        logger.error(f"Failed to send message: {e}")

        send_to_storage_queue(json.dumps({
            "status": "failure",
            "error": str(e)
        }))

        return JSONResponse(content={"message": "Failed to send"}, status_code=500)

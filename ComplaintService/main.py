from fastapi import FastAPI
from pydantic import BaseModel
import os
from azure.servicebus import ServiceBusClient, ServiceBusMessage
import json

AZURE_SERVICE_BUS_CONNECTION_STRING = os.getenv("AZURE_SERVICE_BUS_CONNECTION_STRING")
QUEUE_NAME = os.getenv("QUEUE_NAME")
AZURE_STORAGE_QUEUE_CONNECTION_STRING = os.getenv("AZURE_STORAGE_QUEUE_CONNECTION_STRING")
AZURE_STORAGE_QUEUE_NAME = os.getenv("AZURE_STORAGE_QUEUE_NAME")

app = FastAPI(title="ComplaintService")

# =====================
# Models
# =====================
class Complaint(BaseModel):
    complaint_id: int
    user_id: int
    description: str
    status: str = "new"

# =====================
# Endpoints
# =====================
@app.post("/complaints")
def create_complaint(complaint: Complaint):
    # Отправляем сообщение в Azure Service Bus
    with ServiceBusClient.from_connection_string(AZURE_SERVICE_BUS_CONNECTION_STRING) as client:
        sender = client.get_queue_sender(queue_name=QUEUE_NAME)
        with sender:
            message = ServiceBusMessage(json.dumps(complaint.dict()))
            sender.send_messages(message)

    # Логируем в Storage Queue
    from azure.storage.queue import QueueClient
    queue = QueueClient.from_connection_string(AZURE_STORAGE_QUEUE_CONNECTION_STRING, AZURE_STORAGE_QUEUE_NAME)
    queue.send_message(json.dumps(complaint.dict()))

    return {"message": "Complaint sent to BookingService", "complaint": complaint.dict()}

@app.get("/health")
def health():
    return {"status": "ComplaintService is running"}

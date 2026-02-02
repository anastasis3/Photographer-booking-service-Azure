from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import httpx
import os
from azure.servicebus import ServiceBusClient, ServiceBusMessage
from azure.storage.queue import QueueClient
import json

AZURE_SERVICE_BUS_CONNECTION_STRING = os.getenv("AZURE_SERVICE_BUS_CONNECTION_STRING")
QUEUE_NAME = os.getenv("QUEUE_NAME")
AZURE_STORAGE_QUEUE_CONNECTION_STRING = os.getenv("AZURE_STORAGE_QUEUE_CONNECTION_STRING")
AZURE_STORAGE_QUEUE_NAME = os.getenv("AZURE_STORAGE_QUEUE_NAME")
PHOTOGRAPHER_SERVICE_URL = os.getenv("PHOTOGRAPHER_SERVICE_URL")

app = FastAPI(title="BookingService")

# =====================
# Models
# =====================

class BookingRequest(BaseModel):
    user_id: int
    photographer_id: int
    date: str
    time: str
    session_type: str

class ComplaintNotification(BaseModel):
    complaint_id: int
    status: str
    description: str

# =====================
# Endpoints
# =====================

@app.post("/book")
async def create_booking(booking: BookingRequest):
    # Проверка доступности фотографа
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"{PHOTOGRAPHER_SERVICE_URL}/photographers/{booking.photographer_id}")
        if resp.status_code != 200:
            raise HTTPException(status_code=404, detail="Photographer not found")
        photographer = resp.json()
        if not photographer.get("available", True):
            raise HTTPException(status_code=400, detail="Photographer not available at this time")

    # Логируем бронирование в Storage Queue
    queue = QueueClient.from_connection_string(AZURE_STORAGE_QUEUE_CONNECTION_STRING, AZURE_STORAGE_QUEUE_NAME)
    queue.send_message(json.dumps(booking.dict()))

    return {"message": "Booking created successfully", "booking": booking.dict()}

@app.post("/complaints")
def receive_complaint(notification: ComplaintNotification):
    # Логирование жалобы в Storage Queue
    queue = QueueClient.from_connection_string(AZURE_STORAGE_QUEUE_CONNECTION_STRING, AZURE_STORAGE_QUEUE_NAME)
    queue.send_message(json.dumps(notification.dict()))
    return {"message": "Complaint received"}

@app.get("/health")
def health():
    return {"status": "BookingService is running"}

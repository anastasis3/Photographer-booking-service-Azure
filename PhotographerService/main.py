from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
import os
from azure.storage.queue import QueueClient
import json

AZURE_STORAGE_QUEUE_CONNECTION_STRING = os.getenv("AZURE_STORAGE_QUEUE_CONNECTION_STRING")
AZURE_STORAGE_QUEUE_NAME = os.getenv("AZURE_STORAGE_QUEUE_NAME")

app = FastAPI(title="PhotographerService")

# =====================
# In-memory DB (для примера)
# =====================
photographers = {
    1: {"id": 1, "name": "Alice", "available": True, "rating": 4.5},
    2: {"id": 2, "name": "Bob", "available": True, "rating": 4.7}
}

# =====================
# Models
# =====================
class Photographer(BaseModel):
    id: int
    name: str
    available: bool
    rating: float

class AvailabilityUpdate(BaseModel):
    available: bool

# =====================
# Endpoints
# =====================
@app.get("/photographers", response_model=List[Photographer])
def get_all_photographers():
    return list(photographers.values())

@app.get("/photographers/{photographer_id}", response_model=Photographer)
def get_photographer(photographer_id: int):
    photographer = photographers.get(photographer_id)
    if not photographer:
        raise HTTPException(status_code=404, detail="Photographer not found")
    return photographer

@app.put("/photographers/{photographer_id}/availability")
def update_availability(photographer_id: int, availability: AvailabilityUpdate):
    photographer = photographers.get(photographer_id)
    if not photographer:
        raise HTTPException(status_code=404, detail="Photographer not found")
    photographer["available"] = availability.available

    # Логируем изменения
    queue = QueueClient.from_connection_string(AZURE_STORAGE_QUEUE_CONNECTION_STRING, AZURE_STORAGE_QUEUE_NAME)
    queue.send_message(json.dumps({"photographer_id": photographer_id, "available": availability.available}))

    return {"message": "Availability updated", "photographer": photographer}

@app.get("/health")
def health():
    return {"status": "PhotographerService is running"}

import uuid
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()


class NotificationRequest(BaseModel):
    order_id: str
    user_id: str
    total: float


@app.post("/notifications/order-confirmed")
def order_confirmed(req: NotificationRequest):
    return {"notification_id": str(uuid.uuid4()), "status": "QUEUED"}

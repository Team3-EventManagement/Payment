from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Payment
from app.schemas import PaymentCreate, PaymentResponse
import aio_pika
import json
import os

router = APIRouter()

RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://guest:guest@localhost/")

async def publish_event(event_type: str, data: dict):
    connection = await aio_pika.connect_robust(RABBITMQ_URL)
    async with connection:
        channel = await connection.channel()
        await channel.default_exchange.publish(
            aio_pika.Message(body=json.dumps({"event": event_type, "data": data}).encode()),
            routing_key="events"
        )

@router.post("/payments", response_model=PaymentResponse)
async def create_payment(payment: PaymentCreate, db: Session = Depends(get_db)):
    db_payment = Payment(booking_id=payment.booking_id, amount=payment.amount, status="completed")
    db.add(db_payment)
    db.commit()
    db.refresh(db_payment)
    
    # Publish event
    await publish_event("PaymentCompleted", {"payment_id": db_payment.id, "booking_id": db_payment.booking_id, "amount": db_payment.amount})
    
    return db_payment

@router.get("/payments/{booking_id}", response_model=PaymentResponse)
async def get_payment(booking_id: str, db: Session = Depends(get_db)):
    payment = db.query(Payment).filter(Payment.booking_id == booking_id).first()
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    return payment
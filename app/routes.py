from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Payment
from app.schemas import PaymentCreate, PaymentResponse
import httpx  # For HTTP calls to other services
import json
import os

router = APIRouter()

# Example: HTTP communication with Booking Service
BOOKING_SERVICE_URL = "http://booking-service:8001"  # Or actual URL

@router.post("/payments", response_model=PaymentResponse)
async def create_payment(payment: PaymentCreate, db: Session = Depends(get_db)):
    # Simulate payment processing
    db_payment = Payment(booking_id=payment.booking_id, amount=payment.amount, status="completed")
    db.add(db_payment)
    db.commit()
    db.refresh(db_payment)
    
    # Synchronous HTTP call to update booking status
    async with httpx.AsyncClient() as client:
        try:
            response = await client.put(f"{BOOKING_SERVICE_URL}/bookings/{payment.booking_id}/status", json={"status": "paid"})
            if response.status_code != 200:
                # Handle error, maybe rollback payment
                pass
        except Exception as e:
            # Handle connection error
            pass
    
    # Asynchronous event publishing (would use RabbitMQ in production)
    # await publish_event("PaymentCompleted", {"payment_id": db_payment.id, "booking_id": db_payment.booking_id, "amount": db_payment.amount})
    
    return db_payment

@router.get("/payments/{booking_id}", response_model=PaymentResponse)
async def get_payment(booking_id: str, db: Session = Depends(get_db)):
    payment = db.query(Payment).filter(Payment.booking_id == booking_id).first()
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    return payment
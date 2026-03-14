from fastapi import FastAPI
from app.routes import router
from app.auth import app as auth_app

app = FastAPI(title="Payment Service", version="1.0.0")

app.include_router(router)
app.include_router(auth_app.router)
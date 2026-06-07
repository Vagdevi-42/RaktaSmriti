# backend/app/__init__.py
import os

os.environ.setdefault("AWS_REGION", "us-east-1")
os.environ.setdefault("AWS_DEFAULT_REGION", "us-east-1")

from fastapi import FastAPI
from .routes import donor_api

app = FastAPI(title="RaktaSmriti API", version="1.0")

# Register routes
app.include_router(donor_api.router)

@app.get("/")
async def root():
    return {"message": "RaktaSmriti API is running!", "status": "active"}

@app.get("/health")
async def health():
    return {"status": "healthy"}
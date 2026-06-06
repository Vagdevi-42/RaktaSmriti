# backend/app/__init__.py
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
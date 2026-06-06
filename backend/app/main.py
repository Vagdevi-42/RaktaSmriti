from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routes import health, donor_api, match, coordinator, ghost_donor, prediction
from .routes import ghost_donor
from .routes import whatsapp_webhook
from .routes import donation_request
app = FastAPI(title="RaktaSmriti API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register all routes
app.include_router(health.router)
app.include_router(donor_api.router)
app.include_router(match.router)
app.include_router(coordinator.router)
app.include_router(ghost_donor.router)
app.include_router(donation_request.router)
app.include_router(prediction.router)
app.include_router(whatsapp_webhook.router)


@app.get("/")
async def root():
    return {"message": "RaktaSmriti API is running!", "version": "2.0"}
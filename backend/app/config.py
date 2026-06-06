import os
from datetime import timedelta
from pathlib import Path

from dotenv import load_dotenv

# Load environment variables from backend/.env, regardless of the current shell directory.
load_dotenv(Path(__file__).resolve().parent.parent / ".env", override=False)

# ============================================================
# Twilio Configuration
# These variables can be imported directly using:
# from app.config import TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_WHATSAPP_NUMBER
# ============================================================

TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_WHATSAPP_NUMBER = os.getenv("TWILIO_WHATSAPP_NUMBER")
PATIENT_WHATSAPP_NUMBER = os.getenv("PATIENT_WHATSAPP_NUMBER")

# ============================================================
# AWS Configuration
# ============================================================

AWS_REGION = os.getenv("AWS_REGION")
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
DYNAMODB_TABLE = os.getenv("DYNAMODB_TABLE")

# ============================================================
# Base Configuration
# ============================================================

class Config:
    # Basic Flask config
    SECRET_KEY = os.getenv(
        "SECRET_KEY",
        "dev-secret-key-change-in-production"
    )

    DEBUG = os.getenv("DEBUG", "False").lower() == "true"

    # Database configuration
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL",
        "sqlite:///../data/raktasmitri.db"
    )

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # JWT Configuration
    JWT_SECRET_KEY = os.getenv(
        "JWT_SECRET_KEY",
        "jwt-secret-key-change-in-production"
    )

    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)

    # CORS Configuration
    CORS_ORIGINS = os.getenv(
        "CORS_ORIGINS",
        "http://localhost:3000,http://localhost:5000"
    ).split(",")

    # Blood Donation Configuration
    BLOOD_TYPES = [
        "A+",
        "A-",
        "B+",
        "B-",
        "AB+",
        "AB-",
        "O+",
        "O-"
    ]

    DONATION_ELIGIBILITY_AGE_MIN = 18
    DONATION_ELIGIBILITY_AGE_MAX = 65
    DONATION_WAIT_PERIOD_DAYS = 90

    # Pagination
    ITEMS_PER_PAGE = 20

    # Twilio Config available through Config class
    TWILIO_ACCOUNT_SID = TWILIO_ACCOUNT_SID
    TWILIO_AUTH_TOKEN = TWILIO_AUTH_TOKEN
    TWILIO_WHATSAPP_NUMBER = TWILIO_WHATSAPP_NUMBER
    PATIENT_WHATSAPP_NUMBER = PATIENT_WHATSAPP_NUMBER

    # AWS Config available through Config class
    AWS_REGION = AWS_REGION
    AWS_ACCESS_KEY_ID = AWS_ACCESS_KEY_ID
    AWS_SECRET_ACCESS_KEY = AWS_SECRET_ACCESS_KEY
    DYNAMODB_TABLE = DYNAMODB_TABLE


class DevelopmentConfig(Config):
    DEBUG = True
    ENV = "development"


class ProductionConfig(Config):
    DEBUG = False
    ENV = "production"


class TestingConfig(Config):
    TESTING = True
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"


config = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "testing": TestingConfig,
    "default": DevelopmentConfig,
}
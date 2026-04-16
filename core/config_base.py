"""
core/config_base.py — Configurações base compartilhadas.
"""
import os
from dotenv import load_dotenv

load_dotenv()

# Google Sheets
GOOGLE_SHEETS_SPREADSHEET_ID = os.getenv("GOOGLE_SHEETS_SPREADSHEET_ID", "")
GOOGLE_SERVICE_ACCOUNT_JSON  = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON", "credentials.json")

# AI Keys
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
REPLICATE_API_TOKEN = os.getenv("REPLICATE_API_TOKEN", "")

# Planos
PLANS = {
    "alpha": {"credits": 10,  "label": "Alpha",  "paid": False},
    "beta":  {"credits": 20,  "label": "Beta",   "paid": False},
    "omega": {"credits": 200, "label": "Omega",  "paid": True},
}
DEFAULT_PLAN = "alpha"

# Storage
TEMP_IMAGE_DIR = os.path.join(os.getcwd(), "temp_images")
os.makedirs(TEMP_IMAGE_DIR, exist_ok=True)

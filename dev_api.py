"""
Servidor minimal pra desenvolvimento local do dashboard.
So monta o dashboard_api (le do Monday). Sem Sheets, sem WhatsApp.

Uso:
    pip install fastapi uvicorn requests python-dotenv
    uvicorn dev_api:app --reload --port 8000

Variaveis necessarias no .env da raiz:
    MONDAY_API_TOKEN=seu_token_aqui
    DASHBOARD_API_TOKEN=qualquer_string_forte_aqui
"""

import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from alpha_os.dashboard_api import router as dashboard_router
from alpha_os.missions_api import router as missions_router

app = FastAPI(title="Alpha OS Dashboard — Local Dev")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(dashboard_router)
app.include_router(missions_router)


@app.get("/")
def root():
    return {
        "service": "alpha-os-dashboard-dev",
        "monday_token": "set" if os.getenv("MONDAY_API_TOKEN") else "MISSING",
        "dashboard_token": "set" if os.getenv("DASHBOARD_API_TOKEN") else "MISSING",
    }

import logging
import os

from fastapi import BackgroundTasks, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware

from core.sheets import SheetsManager
from whatsapp.handler import process_webhook


logger = logging.getLogger(__name__)

app = FastAPI()

VERIFY_TOKEN = os.getenv("WHATSAPP_VERIFY_TOKEN", "simulador2026")

# CORS: liberado pra o dashboard no Vercel.
# Em prod, restrinja DASHBOARD_ALLOWED_ORIGINS pro dominio do painel.
_origins_env = os.getenv("DASHBOARD_ALLOWED_ORIGINS", "*").strip()
_allowed_origins = ["*"] if _origins_env == "*" else [o.strip() for o in _origins_env.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

# Dashboard endpoints (/api/*).
try:
    from alpha_os.dashboard_api import router as dashboard_router
    app.include_router(dashboard_router)
except Exception as exc:
    logger.error("Falha ao registrar dashboard_api: %s", exc, exc_info=True)

# Missions endpoints (/api/missions, /api/mission-users, /api/mission-settings).
try:
    from alpha_os.missions_api import router as missions_router
    app.include_router(missions_router)
except Exception as exc:
    logger.error("Falha ao registrar missions_api: %s", exc, exc_info=True)

try:
    sheets = SheetsManager()
except Exception as exc:
    logger.error("Falha ao iniciar SheetsManager no servidor WhatsApp: %s", exc, exc_info=True)
    sheets = None


@app.get("/webhook")
async def verify_webhook(request: Request):
    params = request.query_params
    mode = params.get("hub.mode")
    token = params.get("hub.verify_token")
    challenge = params.get("hub.challenge")

    if mode == "subscribe" and token == VERIFY_TOKEN:
        return int(challenge)
    raise HTTPException(status_code=403, detail="Token de verificacao invalido")


@app.post("/webhook")
async def receive_webhook(request: Request, background_tasks: BackgroundTasks):
    data = await request.json()
    background_tasks.add_task(process_webhook, data, sheets)
    return {"status": "ok"}

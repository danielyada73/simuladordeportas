import logging
import os

from fastapi import BackgroundTasks, FastAPI, HTTPException, Request

from core.sheets import SheetsManager
from whatsapp.handler import process_webhook


logger = logging.getLogger(__name__)

app = FastAPI()

VERIFY_TOKEN = os.getenv("WHATSAPP_VERIFY_TOKEN", "simulador2026")

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

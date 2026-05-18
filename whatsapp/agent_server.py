"""
Servidor independente do agente WhatsApp (Caim).

Roda como SEGUNDO servico no Render, separado do simulador de portas.
Webhook diferente, numero diferente, token Anthropic proprio.

Start command:
    uvicorn whatsapp.agent_server:app --host 0.0.0.0 --port $PORT

Variaveis de ambiente obrigatorias (no Render):
    AGENT_WHATSAPP_TOKEN            token permanente do user system Meta
    AGENT_WHATSAPP_PHONE_NUMBER_ID  phone_number_id do numero do agente (Caim)
    AGENT_WHATSAPP_VERIFY_TOKEN     string qualquer pro webhook verify
    ANTHROPIC_API_KEY               sk-ant-...
    MONDAY_API_TOKEN                token Monday principal (fallback)

Variaveis opcionais (multi-usuario por numero):
    AGENT_USER_DANIEL_PHONE         numero whatsapp do Daniel (sem +, ex: 5511...)
    AGENT_USER_DANIEL_MONDAY_TOKEN  token Monday do Daniel
    AGENT_USER_JEFFERSON_PHONE      ...
    AGENT_USER_JEFFERSON_MONDAY_TOKEN
    AGENT_USER_GUSTAVO_PHONE        ...
    AGENT_USER_GUSTAVO_MONDAY_TOKEN
"""

from __future__ import annotations

import logging
import os
from typing import Any, Dict, Optional

from fastapi import BackgroundTasks, FastAPI, HTTPException, Request


logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

app = FastAPI(title="Alpha OS Agent (Caim)")

VERIFY_TOKEN = os.getenv("AGENT_WHATSAPP_VERIFY_TOKEN", "").strip()


def _normalize_phone(value: str) -> str:
    return "".join(ch for ch in str(value or "") if ch.isdigit())


USER_BY_PHONE: Dict[str, Dict[str, str]] = {}
for name in ("DANIEL", "JEFFERSON", "GUSTAVO"):
    phone = _normalize_phone(os.getenv(f"AGENT_USER_{name}_PHONE", ""))
    token = os.getenv(f"AGENT_USER_{name}_MONDAY_TOKEN", "").strip()
    if phone:
        USER_BY_PHONE[phone] = {"name": name.capitalize(), "monday_token": token}


def resolve_user(from_phone: str) -> Optional[Dict[str, str]]:
    return USER_BY_PHONE.get(_normalize_phone(from_phone))


@app.get("/")
def root() -> Dict[str, Any]:
    return {
        "service": "alpha-os-agent",
        "name": "Caim",
        "authorized_users": list({u["name"] for u in USER_BY_PHONE.values()}),
        "has_anthropic_key": bool(os.getenv("ANTHROPIC_API_KEY")),
        "has_monday_token": bool(os.getenv("MONDAY_API_TOKEN")),
        "has_whatsapp_token": bool(os.getenv("AGENT_WHATSAPP_TOKEN")),
    }


@app.get("/webhook")
async def verify_webhook(request: Request) -> int:
    if not VERIFY_TOKEN:
        raise HTTPException(status_code=500, detail="AGENT_WHATSAPP_VERIFY_TOKEN nao configurado")
    params = request.query_params
    if params.get("hub.mode") == "subscribe" and params.get("hub.verify_token") == VERIFY_TOKEN:
        challenge = params.get("hub.challenge") or "0"
        return int(challenge)
    raise HTTPException(status_code=403, detail="Token de verificacao invalido")


@app.post("/webhook")
async def receive_webhook(request: Request, background_tasks: BackgroundTasks) -> Dict[str, str]:
    data = await request.json()
    background_tasks.add_task(_handle_incoming, data)
    return {"status": "ok"}


def _handle_incoming(payload: Dict[str, Any]) -> None:
    """
    Stub: processa o webhook do WhatsApp.
    Na Fase 3, isso vai virar tool-calling com Claude:
    - extrai mensagem + numero
    - identifica usuario
    - chama Claude Sonnet com tools (Monday/Meta/Google)
    - executa, responde via WhatsApp
    """
    try:
        entry = (payload.get("entry") or [{}])[0]
        change = (entry.get("changes") or [{}])[0]
        value = change.get("value") or {}
        messages = value.get("messages") or []
        if not messages:
            return
        message = messages[0]
        from_phone = message.get("from") or ""
        text = ((message.get("text") or {}).get("body") or "").strip()
        user = resolve_user(from_phone)
        if not user:
            logger.warning("Mensagem de numero nao autorizado: %s", from_phone)
            _send_text(from_phone, "Acesso restrito. Numero nao autorizado.")
            return

        logger.info("Mensagem de %s (%s): %s", user["name"], from_phone, text[:120])
        # Fase 3: aqui entra o agente Claude com tools.
        _send_text(
            from_phone,
            f"Oi {user['name']}, recebi sua mensagem. O agente Claude ainda esta sendo conectado (Fase 3). "
            "Por enquanto so respondo ack.",
        )
    except Exception as exc:
        logger.error("Falha ao processar webhook: %s", exc, exc_info=True)


def _send_text(to_phone: str, body: str) -> None:
    import requests
    token = os.getenv("AGENT_WHATSAPP_TOKEN", "").strip()
    phone_id = os.getenv("AGENT_WHATSAPP_PHONE_NUMBER_ID", "").strip()
    if not token or not phone_id:
        logger.error("AGENT_WHATSAPP_TOKEN ou AGENT_WHATSAPP_PHONE_NUMBER_ID ausente; nao enviado.")
        return
    url = f"https://graph.facebook.com/v25.0/{phone_id}/messages"
    try:
        requests.post(
            url,
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
            json={
                "messaging_product": "whatsapp",
                "to": _normalize_phone(to_phone),
                "type": "text",
                "text": {"body": body[:4000]},
            },
            timeout=20,
        )
    except Exception as exc:
        logger.error("Falha ao enviar WhatsApp: %s", exc)

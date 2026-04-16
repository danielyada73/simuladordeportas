"""
whatsapp/server.py — Servidor para o Bot de WhatsApp (Meta Cloud API).
"""
import os
import requests
from fastapi import FastAPI, Request, HTTPException, BackgroundTasks
from pydantic import BaseModel
from core.logic import ConversationLogic
from core.sheets import SheetsManager
from core.config_base import TEMP_IMAGE_DIR

app = FastAPI()

# Configurações (Vêm do .env)
WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN", "")
VERIFY_TOKEN   = os.getenv("WHATSAPP_VERIFY_TOKEN", "simulador_token_123")
PHONE_NUMBER_ID = os.getenv("WHATSAPP_PHONE_NUMBER_ID", "")

# Instanciar Core
sheets = SheetsManager()
logic = ConversationLogic(sheets)

def send_whatsapp_message(to: str, text: str):
    """Envia mensagem de texto via API do WhatsApp."""
    url = f"https://graph.facebook.com/v18.0/{PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json",
    }
    data = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {"body": text},
    }
    response = requests.post(url, headers=headers, json=data)
    return response.json()

def download_whatsapp_media(media_id: str):
    """Baixa mídia da API do WhatsApp e salva localmente."""
    url = f"https://graph.facebook.com/v18.0/{media_id}"
    headers = {"Authorization": f"Bearer {WHATSAPP_TOKEN}"}
    
    # 1. Obter URL do arquivo
    media_info = requests.get(url, headers=headers).json()
    media_url = media_info.get("url")
    
    if not media_url: return None

    # 2. Baixar o arquivo real
    response = requests.get(media_url, headers=headers)
    ext = "jpg" # Simplificado
    filename = f"wa_{media_id}.{ext}"
    path = os.path.join(TEMP_IMAGE_DIR, filename)
    
    with open(path, "wb") as f:
        f.write(response.content)
    
    return path

async def handle_whatsapp_event(data: dict):
    """Processa o evento recebido no background."""
    try:
        entry = data.get("entry", [{}])[0]
        changes = entry.get("changes", [{}])[0]
        value = changes.get("value", {})
        message = value.get("messages", [{}])[0]
        
        if not message: return

        phone = message.get("from")
        msg_type = message.get("type")
        
        text = None
        image_path = None

        if msg_type == "text":
            text = message.get("text", {}).get("body")
        elif msg_type == "image":
            image_id = message.get("image", {}).get("id")
            image_path = download_whatsapp_media(image_id)

        # Chamar Lógica Central
        response_text, action = logic.process_message(phone, "telefone", text=text, image_path=image_path)

        # Enviar Resposta
        if response_text == "GERAR":
            send_whatsapp_message(phone, "⏳ Processando sua simulação... Isso pode levar alguns segundos.")
            # Aqui dispararíamos a geração real (ai_generator)
            # send_whatsapp_image(phone, generated_image_path)
            # TODO: Implementar envio de imagem no WhatsApp
        else:
            send_whatsapp_message(phone, response_text)

    except Exception as e:
        print(f"Erro ao processar WhatsApp: {e}")

@app.get("/webhook")
async def verify_webhook(request: Request):
    """Verificação de Webhook para a Meta."""
    params = request.query_params
    mode = params.get("hub.mode")
    token = params.get("hub.verify_token")
    challenge = params.get("hub.challenge")

    if mode == "subscribe" and token == VERIFY_TOKEN:
        return int(challenge)
    raise HTTPException(status_code=403, detail="Token de verificação inválido")

@app.post("/webhook")
async def receive_webhook(request: Request, background_tasks: BackgroundTasks):
    """Recebe mensagens do WhatsApp."""
    data = await request.json()
    background_tasks.add_task(handle_whatsapp_event, data)
    return {"status": "ok"}

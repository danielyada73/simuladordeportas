"""
whatsapp/handler.py — Handler de mensagens do WhatsApp Cloud API.
Funciona integrado ao HTTP server existente do bot (sem FastAPI).
"""
import io
import json
import logging
import os
import sys
import requests
from pathlib import Path

logger = logging.getLogger(__name__)

# Alpha OS (Agencia) mode: swap WhatsApp "brain" to Alpha OS commands.
ALPHA_OS_MODE = str(os.getenv("ALPHA_OS_MODE", "false")).strip().lower() in ("1", "true", "yes", "on")
_alpha_chat = None


def _get_alpha_chat():
    global _alpha_chat
    if _alpha_chat is not None:
        return _alpha_chat
    try:
        from alpha_os.chat import AlphaOSChat  # type: ignore

        _alpha_chat = AlphaOSChat()
        return _alpha_chat
    except Exception as exc:
        logger.error(f"Falha ao iniciar Alpha OS: {exc}")
        _alpha_chat = None
        return None

# Config do WhatsApp (vem das variáveis de ambiente no Render)
WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN", "")
PHONE_NUMBER_ID = os.getenv("WHATSAPP_PHONE_NUMBER_ID", os.getenv("PHONE_NUMBER_ID", ""))
VERIFY_TOKEN = os.getenv("WHATSAPP_VERIFY_TOKEN", "simulador2026")
TEMP_DIR = os.path.join(os.path.dirname(__file__), "..", "bot", "temp_images")
os.makedirs(TEMP_DIR, exist_ok=True)

# ─── Enviar mensagens ────────────────────────────────────────────────

def send_text(to: str, text: str):
    """Envia mensagem de texto pelo WhatsApp."""
    url = f"https://graph.facebook.com/v25.0/{PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json",
    }
    try:
        chunks = []
        body = str(text or "").strip() or "..."
        while body:
            chunks.append(body[:3500])
            body = body[3500:]

        last_response = None
        for chunk in chunks:
            payload = {
                "messaging_product": "whatsapp",
                "to": to,
                "type": "text",
                "text": {"body": chunk},
            }
            resp = requests.post(url, headers=headers, json=payload, timeout=30)
            resp.raise_for_status()
            last_response = resp.json()
        logger.info(f"WhatsApp msg enviada para {to}")
        return last_response
    except Exception as e:
        logger.error(f"Erro ao enviar WhatsApp msg: {e}")
        return None


def send_image(to: str, image_bytes: bytes, caption: str = ""):
    """Envia imagem pelo WhatsApp (upload de mídia)."""
    # 1. Upload da mídia
    upload_url = f"https://graph.facebook.com/v25.0/{PHONE_NUMBER_ID}/media"
    headers = {"Authorization": f"Bearer {WHATSAPP_TOKEN}"}
    files = {
        "file": ("simulacao.jpg", io.BytesIO(image_bytes), "image/jpeg"),
    }
    data = {"messaging_product": "whatsapp"}

    try:
        upload_resp = requests.post(upload_url, headers=headers, files=files, data=data, timeout=60)
        upload_resp.raise_for_status()
        media_id = upload_resp.json().get("id")

        if not media_id:
            logger.error("Falha no upload de mídia — sem media_id")
            return None

        # 2. Enviar mensagem com a mídia
        msg_url = f"https://graph.facebook.com/v25.0/{PHONE_NUMBER_ID}/messages"
        msg_headers = {
            "Authorization": f"Bearer {WHATSAPP_TOKEN}",
            "Content-Type": "application/json",
        }
        msg_payload = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "image",
            "image": {"id": media_id, "caption": caption},
        }
        resp = requests.post(msg_url, headers=msg_headers, json=msg_payload, timeout=30)
        resp.raise_for_status()
        logger.info(f"WhatsApp imagem enviada para {to}")
        return resp.json()

    except Exception as e:
        logger.error(f"Erro ao enviar imagem WhatsApp: {e}")
        return None


def download_media(media_id: str) -> str:
    """Baixa mídia do WhatsApp e salva localmente. Retorna o path."""
    headers = {"Authorization": f"Bearer {WHATSAPP_TOKEN}"}

    try:
        # 1. Obter URL do arquivo
        info_url = f"https://graph.facebook.com/v25.0/{media_id}"
        info_resp = requests.get(info_url, headers=headers, timeout=15)
        info_resp.raise_for_status()
        media_url = info_resp.json().get("url")

        if not media_url:
            return None

        # 2. Baixar o arquivo
        file_resp = requests.get(media_url, headers=headers, timeout=30)
        file_resp.raise_for_status()

        path = os.path.join(TEMP_DIR, f"wa_{media_id}.jpg")
        with open(path, "wb") as f:
            f.write(file_resp.content)

        logger.info(f"Mídia baixada: {path}")
        return path

    except Exception as e:
        logger.error(f"Erro ao baixar mídia WhatsApp: {e}")
        return None


# ─── Processar evento do Webhook ─────────────────────────────────────

def process_webhook(data: dict, sheets_manager):
    """
    Processa evento recebido do webhook do WhatsApp.
    Usa o mesmo SheetsManager do bot do Telegram.
    """
    try:
        entry = data.get("entry", [{}])[0]
        changes = entry.get("changes", [{}])[0]
        value = changes.get("value", {})
        messages = value.get("messages", [])

        if not messages:
            return  # Pode ser status update, ignorar.

        message = messages[0]
        phone = message.get("from")  # Número do remetente (ex: 5511912654593)
        msg_type = message.get("type")
        msg_id = message.get("id")

        logger.info(f"WhatsApp msg recebida de {phone}, tipo: {msg_type}")

        # Alpha OS takes over text messages when enabled, or when the user sends an Alpha OS command.
        if msg_type == "text":
            text = message.get("text", {}).get("body", "").strip()
            from alpha_os.chat import is_alpha_os_command  # type: ignore

            if ALPHA_OS_MODE or is_alpha_os_command(text):
                chat = _get_alpha_chat()
                if chat is None:
                    send_text(phone, "Alpha OS indisponivel agora. Verifique GOOGLE_SHEETS_SPREADSHEET_ID e credenciais.")
                    return
                try:
                    reply = chat.handle(phone, text)
                except Exception as exc:
                    logger.error(f"Erro Alpha OS: {exc}")
                    send_text(phone, f"Deu erro interno no Alpha OS: {exc}")
                    return
                send_text(phone, reply)
                return

        # Buscar ou criar usuário pela phone
        user = sheets_manager.get_user(phone_number=phone)

        if not user:
            # Novo usuário — criar com plano beta (WhatsApp = Beta por padrão)
            sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'bot'))
            from config import PLANS, DEFAULT_PLAN
            user = sheets_manager.create_user_whatsapp(phone)
            send_text(phone,
                "Olá! 👋 Seja bem-vindo ao *Simulador de Portas*!\n\n"
                "Aqui você pode ver como ficaria o seu ambiente com a porta que deseja instalar.\n\n"
                "📸 Vamos começar! Envie a foto do *ambiente* onde você quer instalar a porta.\n"
                "_(Ex: entrada da casa, quarto, corredor, sala)_\n\n"
                "💡 *Dica:* Foto bem iluminada, mostrando a porta atual!"
            )
            return

        estado = user.get("estado", "AGUARDANDO_AMBIENTE")
        creditos = int(user.get("creditos_restantes", 0))

        # ─── Mensagem de TEXTO ────────────────────────────────
        if msg_type == "text":
            text = message.get("text", {}).get("body", "").strip()

            # Comando /start ou início
            if text.lower() in ("oi", "olá", "ola", "inicio", "start", "menu", "começar"):
                nome = user.get("nome", "")
                if nome:
                    send_text(phone,
                        f"Olá, *{nome}*! 😊 Que bom te ver de volta!\n\n"
                        f"Você tem *{creditos}* simulação(ões) disponível(eis).\n\n"
                        "Envie a foto do *ambiente* para começar!"
                    )
                else:
                    send_text(phone, "Olá! Qual é o seu nome? 😊")
                sheets_manager.update_state_whatsapp(phone, "AGUARDANDO_AMBIENTE")
                return

            # Se não tem nome, salvar
            if not user.get("nome"):
                sheets_manager.save_name_whatsapp(phone, text)
                sheets_manager.update_state_whatsapp(phone, "AGUARDANDO_AMBIENTE")
                send_text(phone,
                    f"Prazer, *{text}*! 😊\n\n"
                    "📸 Envie a foto do *ambiente* onde você quer instalar a porta."
                )
                return

            # Menu pós-geração
            if estado == "AGUARDANDO_FEEDBACK":
                if text in ("1", "gerar novamente", "refazer"):
                    _handle_regenerate(phone, user, sheets_manager)
                elif text in ("2", "novo ambiente", "outro"):
                    sheets_manager.reset_images_whatsapp(phone)
                    sheets_manager.update_state_whatsapp(phone, "AGUARDANDO_AMBIENTE")
                    send_text(phone, "🔁 Vamos simular outro ambiente!\n\nEnvie a foto do novo *ambiente*.")
                elif text in ("3", "encerrar", "obrigado", "ok"):
                    sheets_manager.update_state_whatsapp(phone, "ENCERRADO")
                    send_text(phone,
                        "Obrigado por usar o *Simulador de Portas*! 🚪\n\n"
                        "Ficou satisfeito? Entre em contato para fechar o pedido!\n\n_Até logo! 👋_"
                    )
                else:
                    send_text(phone,
                        "Escolha uma opção:\n\n"
                        "1️⃣ Gerar novamente\n"
                        "2️⃣ Simular outro ambiente\n"
                        "3️⃣ Encerrar atendimento"
                    )
                return

            # Em outros estados com texto
            send_text(phone, "📸 Por favor, envie uma *imagem* (foto) para continuarmos!")
            return

        # ─── Mensagem de IMAGEM ───────────────────────────────
        if msg_type == "image":
            image_info = message.get("image", {})
            media_id = image_info.get("id")

            if not media_id:
                send_text(phone, "❌ Não consegui processar a imagem. Tente novamente.")
                return

            # Baixar imagem
            path = download_media(media_id)
            if not path:
                send_text(phone, "❌ Erro ao baixar a imagem. Envie novamente.")
                return

            # Foto do AMBIENTE
            if estado in ("AGUARDANDO_AMBIENTE", "NOVO"):
                send_text(phone, "📥 Foto do ambiente recebida!")
                sheets_manager.save_image_url_whatsapp(phone, "foto_ambiente_url", path)
                sheets_manager.update_state_whatsapp(phone, "AGUARDANDO_PORTA")
                send_text(phone,
                    "✅ Foto do ambiente recebida!\n\n"
                    "Agora envie a foto do *modelo de porta* que você deseja experimentar.\n"
                    "_(Dica: foto da porta com fundo claro e porta centralizada)_"
                )
                return

            # Foto da PORTA
            if estado == "AGUARDANDO_PORTA":
                if creditos <= 0:
                    send_text(phone,
                        "❌ Você usou todas as suas simulações.\n\n"
                        "Faça upgrade para o *Plano Omega* com *200 gerações*!"
                    )
                    sheets_manager.update_state_whatsapp(phone, "SEM_CREDITOS")
                    return

                send_text(phone, "📥 Foto da porta recebida!")
                sheets_manager.save_image_url_whatsapp(phone, "foto_porta_url", path)
                sheets_manager.update_state_whatsapp(phone, "GERANDO")

                send_text(phone,
                    "⏳ *Gerando a simulação...*\n\n"
                    "Estou processando as imagens com inteligência artificial.\n"
                    "Aguarde alguns instantes!"
                )

                # Gerar imagem
                _run_generation_whatsapp(phone, user, path, sheets_manager)
                return

            # Imagem em estado de feedback
            if estado == "AGUARDANDO_FEEDBACK":
                send_text(phone,
                    "Você está no menu de opções! Escolha:\n\n"
                    "1️⃣ Gerar novamente\n"
                    "2️⃣ Simular outro ambiente\n"
                    "3️⃣ Encerrar atendimento"
                )
                return

        # Outros tipos de mensagem
        send_text(phone,
            "😊 Por enquanto, eu só processo *imagens* (fotos).\n"
            "Envie a foto do ambiente ou da porta para continuarmos!"
        )

    except Exception as e:
        logger.error(f"Erro ao processar webhook WhatsApp: {e}", exc_info=True)


def _run_generation_whatsapp(phone: str, user: dict, porta_path: str, sheets_manager):
    """Gera a simulação e envia a imagem pelo WhatsApp."""
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'bot'))
    from ai_generator import generate_door_simulation

    ambiente_path = user.get("foto_ambiente_url", "")
    if not ambiente_path:
        send_text(phone, "❌ Não encontrei a foto do ambiente. Envie novamente.")
        sheets_manager.update_state_whatsapp(phone, "AGUARDANDO_AMBIENTE")
        return

    img_bytes, erro_msg = generate_door_simulation(ambiente_path, porta_path)

    if not img_bytes:
        msg = "😔 Ops! Houve um problema ao gerar a imagem.\nPor favor, tente novamente."
        if erro_msg:
            msg += f"\n\n_Detalhe: {erro_msg[:100]}_"
        send_text(phone, msg)
        sheets_manager.update_state_whatsapp(phone, "AGUARDANDO_AMBIENTE")
        return

    # Descontar crédito
    creditos_restantes = sheets_manager.deduct_credit_whatsapp(phone)

    # Enviar imagem gerada
    send_image(phone, img_bytes, "✅ Simulação gerada! O que achou?")

    # Menu pós-geração
    creditos_msg = (
        f"\n_Você tem {creditos_restantes} simulação(ões) restante(s)._"
        if creditos_restantes > 0
        else "\n_Você não tem mais simulações neste plano._"
    )

    send_text(phone,
        "✅ *Aqui está seu ambiente com a nova porta instalada!*\n\n"
        "O que você achou? Escolha uma opção:\n\n"
        "1️⃣ Gerar novamente (mesmas fotos, novo resultado)\n"
        "2️⃣ Simular outro ambiente (enviar novas fotos)\n"
        "3️⃣ Estou satisfeito! Encerrar atendimento"
        + creditos_msg
    )

    sheets_manager.update_state_whatsapp(phone, "AGUARDANDO_FEEDBACK")
    logger.info(f"WhatsApp: imagem entregue para {phone}, créditos restantes: {creditos_restantes}")


def _handle_regenerate(phone: str, user: dict, sheets_manager):
    """Gerar novamente com as mesmas imagens."""
    creditos = int(user.get("creditos_restantes", 0))
    if creditos <= 0:
        send_text(phone, "❌ Você não tem mais créditos. Faça upgrade para o Plano Omega!")
        sheets_manager.update_state_whatsapp(phone, "SEM_CREDITOS")
        return

    send_text(phone, "⏳ Gerando novamente...")
    sheets_manager.update_state_whatsapp(phone, "GERANDO")
    porta_path = user.get("foto_porta_url", "")
    _run_generation_whatsapp(phone, user, porta_path, sheets_manager)

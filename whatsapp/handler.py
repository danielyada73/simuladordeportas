import io
import logging
import os
import sys
import threading
import time

import requests


logger = logging.getLogger(__name__)

ALPHA_OS_MODE = str(os.getenv("ALPHA_OS_MODE", "false")).strip().lower() in ("1", "true", "yes", "on")
WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN", "")
PHONE_NUMBER_ID = os.getenv("WHATSAPP_PHONE_NUMBER_ID", os.getenv("PHONE_NUMBER_ID", ""))
VERIFY_TOKEN = os.getenv("WHATSAPP_VERIFY_TOKEN", "simulador2026")
TEMP_DIR = os.path.join(os.path.dirname(__file__), "..", "bot", "temp_images")
os.makedirs(TEMP_DIR, exist_ok=True)

_alpha_chat = None
_processed_message_ids = {}
_processed_lock = threading.Lock()
_PROCESSED_TTL_SECONDS = 900


def _get_alpha_chat():
    global _alpha_chat
    if _alpha_chat is not None:
        return _alpha_chat
    try:
        from alpha_os.chat import AlphaOSChat  # type: ignore

        _alpha_chat = AlphaOSChat()
        return _alpha_chat
    except Exception as exc:
        logger.error("Falha ao iniciar Alpha OS: %s", exc, exc_info=True)
        _alpha_chat = None
        return None


def _is_duplicate_message(message_id: str) -> bool:
    if not message_id:
        return False
    now = time.time()
    with _processed_lock:
        expired = [key for key, seen_at in _processed_message_ids.items() if now - seen_at > _PROCESSED_TTL_SECONDS]
        for key in expired:
            _processed_message_ids.pop(key, None)
        if message_id in _processed_message_ids:
            return True
        _processed_message_ids[message_id] = now
    return False


def _split_text_chunks(text: str, limit: int = 3500):
    text = (text or "").strip()
    if not text:
        return [""]
    if len(text) <= limit:
        return [text]

    chunks = []
    current = []
    current_len = 0
    for block in text.split("\n\n"):
        block = block.strip()
        if not block:
            continue
        block_len = len(block)
        extra = block_len + (2 if current else 0)
        if current and current_len + extra > limit:
            chunks.append("\n\n".join(current))
            current = [block]
            current_len = block_len
            continue
        if block_len > limit:
            if current:
                chunks.append("\n\n".join(current))
                current = []
                current_len = 0
            start = 0
            while start < block_len:
                chunks.append(block[start : start + limit])
                start += limit
            continue
        current.append(block)
        current_len += extra

    if current:
        chunks.append("\n\n".join(current))
    return chunks


def send_text(to: str, text: str):
    url = f"https://graph.facebook.com/v25.0/{PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json",
    }
    last_response = None
    for chunk in _split_text_chunks(text):
        payload = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "text",
            "text": {"body": chunk},
        }
        try:
            resp = requests.post(url, headers=headers, json=payload, timeout=30)
            resp.raise_for_status()
            last_response = resp.json()
            logger.info("WhatsApp msg enviada para %s", to)
        except Exception as exc:
            logger.error("Erro ao enviar WhatsApp msg: %s", exc)
            return None
    return last_response


def send_image(to: str, image_bytes: bytes, caption: str = ""):
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
            logger.error("Falha no upload de midia do WhatsApp.")
            return None

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
        logger.info("WhatsApp imagem enviada para %s", to)
        return resp.json()
    except Exception as exc:
        logger.error("Erro ao enviar imagem WhatsApp: %s", exc)
        return None


def download_media(media_id: str) -> str:
    headers = {"Authorization": f"Bearer {WHATSAPP_TOKEN}"}
    try:
        info_url = f"https://graph.facebook.com/v25.0/{media_id}"
        info_resp = requests.get(info_url, headers=headers, timeout=15)
        info_resp.raise_for_status()
        media_url = info_resp.json().get("url")
        if not media_url:
            return None

        file_resp = requests.get(media_url, headers=headers, timeout=30)
        file_resp.raise_for_status()

        path = os.path.join(TEMP_DIR, f"wa_{media_id}.jpg")
        with open(path, "wb") as file_handle:
            file_handle.write(file_resp.content)

        logger.info("Midia baixada: %s", path)
        return path
    except Exception as exc:
        logger.error("Erro ao baixar midia WhatsApp: %s", exc)
        return None


def _handle_alpha_os_message(phone: str, msg_type: str, message: dict):
    if msg_type != "text":
        send_text(
            phone,
            "Estou operando como Alpha OS e, por enquanto, trabalho so com texto.\n"
            "Me mande sua pergunta sobre a Monday ou use:\n"
            "novo cliente Nome do Cliente",
        )
        return

    chat = _get_alpha_chat()
    if chat is None:
        send_text(phone, "Alpha OS indisponivel agora. Verifique MONDAY_API_TOKEN e GOOGLE_SHEETS_SPREADSHEET_ID.")
        return

    text = message.get("text", {}).get("body", "").strip()
    reply = chat.handle(phone, text)
    send_text(phone, reply)


def process_webhook(data: dict, sheets_manager):
    try:
        entry = data.get("entry", [{}])[0]
        changes = entry.get("changes", [{}])[0]
        value = changes.get("value", {})
        messages = value.get("messages", [])

        if not messages:
            return

        message = messages[0]
        phone = message.get("from")
        msg_type = message.get("type")
        msg_id = message.get("id")

        logger.info("WhatsApp msg recebida de %s, tipo: %s", phone, msg_type)

        if _is_duplicate_message(msg_id):
            logger.info("Mensagem duplicada ignorada: %s", msg_id)
            return

        if ALPHA_OS_MODE:
            try:
                _handle_alpha_os_message(phone, msg_type, message)
            except Exception as exc:
                logger.error("Erro Alpha OS: %s", exc, exc_info=True)
                send_text(phone, f"Alpha OS falhou ao responder agora. Erro: {exc}")
            return

        if msg_type == "text":
            text = message.get("text", {}).get("body", "").strip()
            try:
                from alpha_os.chat import is_alpha_os_command  # type: ignore

                if is_alpha_os_command(text):
                    _handle_alpha_os_message(phone, msg_type, message)
                    return
            except Exception as exc:
                logger.error("Erro Alpha OS (modo comando): %s", exc)

        if sheets_manager is None:
            send_text(phone, "Servico temporariamente sem acesso ao simulador antigo.")
            return

        user = sheets_manager.get_user(phone_number=phone)

        if not user:
            sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "bot"))
            from config import PLANS, DEFAULT_PLAN

            user = sheets_manager.create_user_whatsapp(phone)
            send_text(
                phone,
                "Ola! Seja bem-vindo ao Simulador de Portas!\n\n"
                "Envie a foto do ambiente onde voce quer instalar a porta.",
            )
            return

        estado = user.get("estado", "AGUARDANDO_AMBIENTE")
        creditos = int(user.get("creditos_restantes", 0))

        if msg_type == "text":
            text = message.get("text", {}).get("body", "").strip()

            if text.lower() in ("oi", "olá", "ola", "inicio", "start", "menu", "comecar", "começar"):
                nome = user.get("nome", "")
                if nome:
                    send_text(
                        phone,
                        f"Ola, *{nome}*!\n\n"
                        f"Voce tem *{creditos}* simulacao(oes) disponivel(eis).\n\n"
                        "Envie a foto do ambiente para comecar!",
                    )
                else:
                    send_text(phone, "Ola! Qual e o seu nome?")
                sheets_manager.update_state_whatsapp(phone, "AGUARDANDO_AMBIENTE")
                return

            if not user.get("nome"):
                sheets_manager.save_name_whatsapp(phone, text)
                sheets_manager.update_state_whatsapp(phone, "AGUARDANDO_AMBIENTE")
                send_text(phone, f"Prazer, *{text}*!\n\nEnvie a foto do ambiente onde voce quer instalar a porta.")
                return

            if estado == "AGUARDANDO_FEEDBACK":
                if text in ("1", "gerar novamente", "refazer"):
                    _handle_regenerate(phone, user, sheets_manager)
                elif text in ("2", "novo ambiente", "outro"):
                    sheets_manager.reset_images_whatsapp(phone)
                    sheets_manager.update_state_whatsapp(phone, "AGUARDANDO_AMBIENTE")
                    send_text(phone, "Vamos simular outro ambiente.\n\nEnvie a foto do novo ambiente.")
                elif text in ("3", "encerrar", "obrigado", "ok"):
                    sheets_manager.update_state_whatsapp(phone, "ENCERRADO")
                    send_text(phone, "Obrigado por usar o Simulador de Portas. Ate logo.")
                else:
                    send_text(
                        phone,
                        "Escolha uma opcao:\n\n"
                        "1. Gerar novamente\n"
                        "2. Simular outro ambiente\n"
                        "3. Encerrar atendimento",
                    )
                return

            send_text(phone, "Por favor, envie uma imagem para continuarmos.")
            return

        if msg_type == "image":
            image_info = message.get("image", {})
            media_id = image_info.get("id")
            if not media_id:
                send_text(phone, "Nao consegui processar a imagem. Tente novamente.")
                return

            path = download_media(media_id)
            if not path:
                send_text(phone, "Erro ao baixar a imagem. Envie novamente.")
                return

            if estado in ("AGUARDANDO_AMBIENTE", "NOVO"):
                send_text(phone, "Foto do ambiente recebida.")
                sheets_manager.save_image_url_whatsapp(phone, "foto_ambiente_url", path)
                sheets_manager.update_state_whatsapp(phone, "AGUARDANDO_PORTA")
                send_text(phone, "Agora envie a foto do modelo de porta que voce deseja experimentar.")
                return

            if estado == "AGUARDANDO_PORTA":
                if creditos <= 0:
                    send_text(phone, "Voce usou todas as suas simulacoes.")
                    sheets_manager.update_state_whatsapp(phone, "SEM_CREDITOS")
                    return

                send_text(phone, "Foto da porta recebida.")
                sheets_manager.save_image_url_whatsapp(phone, "foto_porta_url", path)
                sheets_manager.update_state_whatsapp(phone, "GERANDO")
                send_text(phone, "Gerando a simulacao. Aguarde alguns instantes.")
                _run_generation_whatsapp(phone, user, path, sheets_manager)
                return

            if estado == "AGUARDANDO_FEEDBACK":
                send_text(
                    phone,
                    "Voce esta no menu de opcoes.\n\n"
                    "1. Gerar novamente\n"
                    "2. Simular outro ambiente\n"
                    "3. Encerrar atendimento",
                )
                return

        send_text(phone, "Por enquanto, eu so processo imagens. Envie a foto do ambiente ou da porta.")
    except Exception as exc:
        logger.error("Erro ao processar webhook WhatsApp: %s", exc, exc_info=True)


def _run_generation_whatsapp(phone: str, user: dict, porta_path: str, sheets_manager):
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "bot"))
    from ai_generator import generate_door_simulation

    ambiente_path = user.get("foto_ambiente_url", "")
    if not ambiente_path:
        send_text(phone, "Nao encontrei a foto do ambiente. Envie novamente.")
        sheets_manager.update_state_whatsapp(phone, "AGUARDANDO_AMBIENTE")
        return

    img_bytes, erro_msg = generate_door_simulation(ambiente_path, porta_path)

    if not img_bytes:
        msg = "Houve um problema ao gerar a imagem. Tente novamente."
        if erro_msg:
            msg += f"\n\nDetalhe: {erro_msg[:100]}"
        send_text(phone, msg)
        sheets_manager.update_state_whatsapp(phone, "AGUARDANDO_AMBIENTE")
        return

    creditos_restantes = sheets_manager.deduct_credit_whatsapp(phone)
    send_image(phone, img_bytes, "Simulacao gerada.")

    creditos_msg = (
        f"\nVoce tem {creditos_restantes} simulacao(oes) restante(s)."
        if creditos_restantes > 0
        else "\nVoce nao tem mais simulacoes neste plano."
    )

    send_text(
        phone,
        "Aqui esta seu ambiente com a nova porta instalada.\n\n"
        "O que voce achou?\n\n"
        "1. Gerar novamente (mesmas fotos, novo resultado)\n"
        "2. Simular outro ambiente (enviar novas fotos)\n"
        "3. Estou satisfeito. Encerrar atendimento"
        + creditos_msg,
    )

    sheets_manager.update_state_whatsapp(phone, "AGUARDANDO_FEEDBACK")
    logger.info("WhatsApp: imagem entregue para %s, creditos restantes: %s", phone, creditos_restantes)


def _handle_regenerate(phone: str, user: dict, sheets_manager):
    creditos = int(user.get("creditos_restantes", 0))
    if creditos <= 0:
        send_text(phone, "Voce nao tem mais creditos. Faca upgrade para o Plano Omega.")
        sheets_manager.update_state_whatsapp(phone, "SEM_CREDITOS")
        return

    send_text(phone, "Gerando novamente...")
    sheets_manager.update_state_whatsapp(phone, "GERANDO")
    porta_path = user.get("foto_porta_url", "")
    _run_generation_whatsapp(phone, user, porta_path, sheets_manager)

"""
bot.py — Simulador de Portas: Telegram Bot Principal

Fluxo:
  /start ou qualquer mensagem inicial
    → pede foto do ambiente
    → pede foto da porta
    → gera imagem com IA
    → oferece menu: gerar novamente | novo ambiente | encerrar

Estados salvos no Google Sheets por chat_id.
"""
import io
import logging
import os
import tempfile
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.constants import ParseMode
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from config import TELEGRAM_BOT_TOKEN, State, Msg, PLANS, DEFAULT_PLAN, TEMP_IMAGE_DIR
from sheets import SheetsManager
from ai_generator import generate_door_simulation

# ─── Logging ─────────────────────────────────────────────────────────────────
logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# Instância global do SheetsManager (inicializado uma vez)
sheets: SheetsManager = None


# ─── Helpers ─────────────────────────────────────────────────────────────────

import json
import sys
_PROJECT_ROOT = str(Path(__file__).resolve().parent.parent)
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)
from urllib.parse import urlparse, parse_qs

# WhatsApp verify token
WA_VERIFY_TOKEN = os.getenv("WHATSAPP_VERIFY_TOKEN", "simulador2026")

class WebhookHandler(BaseHTTPRequestHandler):
    """HTTP Handler que serve como keep-alive E webhook do WhatsApp."""

    def do_GET(self):
        parsed = urlparse(self.path)

        # WhatsApp Webhook Verification
        if parsed.path == "/webhook":
            params = parse_qs(parsed.query)
            mode = params.get("hub.mode", [None])[0]
            token = params.get("hub.verify_token", [None])[0]
            challenge = params.get("hub.challenge", [None])[0]

            if mode == "subscribe" and token == WA_VERIFY_TOKEN:
                logger.info("✅ WhatsApp Webhook verificado com sucesso!")
                self.send_response(200)
                self.send_header('Content-type', 'text/plain')
                self.end_headers()
                self.wfile.write(challenge.encode())
                return

            self.send_response(403)
            self.end_headers()
            return

        # Keep-alive padrão
        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()
        self.wfile.write(b"Bot ta on! Telegram + WhatsApp")

    def do_POST(self):
        if self.path.startswith("/webhook"):
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length)

            # Responder 200 imediatamente (Meta exige resposta rápida)
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(b'{"status":"ok"}')

            # Processar em background
            try:
                data = json.loads(body)
                from whatsapp.handler import process_webhook
                threading.Thread(
                    target=process_webhook,
                    args=(data, sheets),
                    daemon=True
                ).start()
            except ImportError:
                logger.warning("whatsapp.handler não disponível — ignorando webhook")
            except Exception as e:
                logger.error(f"Erro ao processar webhook WhatsApp: {e}")
            return

        elif self.path == "/kiwify":
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length)
            
            try:
                data = json.loads(body)
                order_status = data.get("order_status")
                
                # Kiwify usa 'paid' ou 'approved' dependendo da versão/evento
                if order_status in ["paid", "approved"]:
                    phone = data.get("customer_mobile")
                    email = data.get("customer_email")
                    
                    if phone:
                        logger.info(f"💰 Venda confirmada via Kiwify: {email} / {phone}")
                        # Atualiza no Sheets
                        sheets.set_plan_by_phone(phone, "omega")
                
                self.send_response(200)
                self.end_headers()
                self.wfile.write(b'{"status":"received"}')
            except Exception as e:
                logger.error(f"Erro ao processar webhook Kiwify: {e}")
                self.send_response(500)
                self.end_headers()
            return

        self.send_response(404)
        self.end_headers()

    def log_message(self, format, *args):
        """Silencia logs HTTP padrão para não poluir."""
        pass

def keep_alive():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(('0.0.0.0', port), WebhookHandler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    logger.info(f"🌐 Servidor HTTP rodando na porta {port} (keep-alive + WhatsApp webhook)")

def _feedback_keyboard() -> InlineKeyboardMarkup:
    """Teclado inline para o menu pós-geração."""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔄 1. Gerar novamente", callback_data="gerar_novamente")],
        [InlineKeyboardButton("🔁 2. Simular outro ambiente", callback_data="novo_ambiente")],
        [InlineKeyboardButton("✅ 3. Encerrar atendimento", callback_data="encerrar")],
    ])


async def _send_md(update: Update, text: str, reply_markup=None):
    """Envia mensagem com MarkdownV2."""
    await update.effective_chat.send_message(
        text=text,
        parse_mode=ParseMode.MARKDOWN_V2,
        reply_markup=reply_markup,
    )


async def _download_telegram_photo(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> str:
    """
    Baixa a foto de maior resolução enviada pelo usuário.
    Salva temporariamente e retorna o path local.
    """
    photo = update.message.photo[-1]  # Maior resolução
    file  = await context.bot.get_file(photo.file_id)
    ext   = "jpg"
    path  = os.path.join(TEMP_IMAGE_DIR, f"{update.effective_chat.id}_{photo.file_id}.{ext}")
    await file.download_to_drive(path)
    return path


async def _download_telegram_document(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> str:
    """
    Aceita documentos (arquivos .jpg/.png enviados como documento).
    Salva temporariamente e retorna o path local.
    """
    doc  = update.message.document
    file = await context.bot.get_file(doc.file_id)
    suffix = Path(doc.file_name).suffix if doc.file_name else ".jpg"
    path = os.path.join(TEMP_IMAGE_DIR, f"{update.effective_chat.id}_{doc.file_id}{suffix}")
    await file.download_to_drive(path)
    return path


async def _start_welcome(update: Update, user: dict):
    """Envia boas-vindas para novo usuário ou usuário retornando."""
    nome    = user.get("nome", "")
    creditos = int(user.get("creditos_restantes", 0))
    plano   = user.get("plano", DEFAULT_PLAN)
    plan_label = PLANS.get(plano, PLANS[DEFAULT_PLAN])["label"]

    if nome:
        # Usuário retornando — já tem nome salvo
        text = Msg.BOAS_VINDAS_RETORNO.format(
            nome=nome,
            creditos=creditos,
            plano=plan_label,
        )
    else:
        text = Msg.BOAS_VINDAS

    await _send_md(update, text)


# ─── Handlers de Comando ──────────────────────────────────────────────────────

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler do /start — ponto de entrada principal."""
    chat_id = update.effective_chat.id

    # Verifica parâmetros de deep link (ex: /start beta_TOKEN)
    args = context.args  # lista de argumentos passados no /start
    plano = DEFAULT_PLAN
    if args:
        arg = args[0].lower()
        if arg.startswith("alpha"):
            plano = "alpha"
        elif arg.startswith("beta"):
            plano = "beta"
        elif arg.startswith("omega"):
            plano = "omega"

    user = sheets.get_user(chat_id)

    if not user:
        # Novo usuário — criar com o plano do deep link
        user = sheets.create_user(chat_id, plano=plano)
        await _send_md(update, Msg.BOAS_VINDAS)
        logger.info(f"Novo usuário registrado: {chat_id} — plano {plano}")
    else:
        # Usuário existente — retornar ao fluxo normal
        estado = user.get("estado", State.NOVO)

        # Se estava em meio a um atendimento, reinicia
        if estado not in (State.ENCERRADO, State.AGUARDANDO_AMBIENTE, State.NOVO):
            sheets.update_state(chat_id, State.AGUARDANDO_AMBIENTE)
            sheets.reset_images(chat_id)

        await _start_welcome(update, user)
        sheets.update_state(chat_id, State.AGUARDANDO_AMBIENTE)


async def cmd_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler do /menu — mostra opções principais."""
    await _send_md(update, Msg.MENU_FEEDBACK, reply_markup=_feedback_keyboard())


async def cmd_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler do /status — mostra informações do plano e créditos."""
    chat_id = update.effective_chat.id
    user = sheets.get_user(chat_id)
    if not user:
        await _send_md(update, Msg.BOAS_VINDAS)
        return

    nome    = user.get("nome") or "não informado"
    plano   = user.get("plano", DEFAULT_PLAN)
    creditos = int(user.get("creditos_restantes", 0))
    total   = int(user.get("total_geracoes", 0))
    plan_label = PLANS.get(plano, PLANS[DEFAULT_PLAN])["label"]

    text = (
        f"📊 *Seu Painel*\n\n"
        f"👤 Nome: {nome}\n"
        f"🎫 Plano: *{plan_label}*\n"
        f"✨ Créditos restantes: *{creditos}*\n"
        f"🖼️ Total de simulações realizadas: *{total}*"
    )
    # Escapa caracteres especiais para MarkdownV2
    text = text.replace(".", "\\.").replace("(", "\\(").replace(")", "\\)").replace("-", "\\-")
    await _send_md(update, text)


# ─── Handler de Mensagem de Texto ─────────────────────────────────────────────

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Processa mensagens de texto baseado no estado atual do usuário."""
    chat_id = update.effective_chat.id
    text    = update.message.text.strip()

    user = sheets.get_user(chat_id)
    if not user:
        user = sheets.create_user(chat_id)
        await _send_md(update, Msg.BOAS_VINDAS)
        return

    estado = user.get("estado", State.NOVO)
    nome   = user.get("nome", "")

    # Estado: aguardando nome
    if estado == State.NOVO and not nome:
        sheets.save_name(chat_id, text)
        sheets.update_state(chat_id, State.AGUARDANDO_AMBIENTE)
        await _send_md(
            update,
            f"Prazer, *{_escape_md(text)}*\\! 😊\n\n" + Msg.BOAS_VINDAS.split("\\!\n\n")[1]
        )
        return

    # Estado: aguardando feedback (texto livre como resposta ao menu)
    if estado == State.AGUARDANDO_FEEDBACK:
        t = text.strip()
        if t in ("1", "gerar novamente", "gerar de novo", "refazer"):
            await _handle_gerar_novamente(update, context, user)
        elif t in ("2", "novo ambiente", "outro ambiente"):
            await _handle_novo_ambiente(update, context, user)
        elif t in ("3", "encerrar", "finalizar", "obrigado", "ok"):
            await _handle_encerrar(update, context, user)
        else:
            await _send_md(update, Msg.OPCAO_INVALIDA, reply_markup=_feedback_keyboard())
        return

    # Estado: encerrado — nova conversa
    if estado == State.ENCERRADO:
        nome_atual = user.get("nome", "")
        if not nome_atual:
            # Pede nome de forma natural
            sheets.update_state(chat_id, State.NOVO)
            await _send_md(update, Msg.PEDIU_NOME)
        else:
            sheets.update_state(chat_id, State.AGUARDANDO_AMBIENTE)
            await _send_md(
                update,
                Msg.BOAS_VINDAS_RETORNO.format(
                    nome=_escape_md(nome_atual),
                    creditos=user.get("creditos_restantes", 0),
                    plano=PLANS.get(user.get("plano", DEFAULT_PLAN), PLANS[DEFAULT_PLAN])["label"],
                ),
            )
        return

    # Em outros estados com texto, apenas orienta
    await _send_md(update, "📸 Por favor, envie uma *imagem* \\(foto\\) para continuarmos\\!")


# ─── Handler de Imagem ────────────────────────────────────────────────────────

async def handle_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Processa imagens recebidas baseado no estado atual."""
    chat_id = update.effective_chat.id

    user = sheets.get_user(chat_id)
    if not user:
        user = sheets.create_user(chat_id)
        await _send_md(update, Msg.BOAS_VINDAS)
        return

    estado   = user.get("estado", State.NOVO)
    creditos = int(user.get("creditos_restantes", 0))

    # ─── Recebeu foto do AMBIENTE ────────────────────────────────────────────
    if estado in (State.AGUARDANDO_AMBIENTE, State.NOVO):
        # Baixa a foto do ambiente
        await update.message.reply_text("📥 Recebendo foto do ambiente...")
        try:
            path = await _download_telegram_photo(update, context)
        except Exception:
            # Tenta como documento
            try:
                path = await _download_telegram_document(update, context)
            except Exception as e:
                logger.error(f"Erro ao baixar imagem do ambiente: {e}")
                await _send_md(update, Msg.AGUARDANDO_IMAGEM)
                return

        # Salva path como URL (local path por ora; pode migrar para URL pública depois)
        sheets.save_image_url(chat_id, "foto_ambiente_url", path)
        sheets.update_state(chat_id, State.AGUARDANDO_PORTA)

        await _send_md(update, Msg.PEDIR_PORTA)
        logger.info(f"Foto do ambiente recebida: {chat_id}")
        return

    # ─── Recebeu foto da PORTA ───────────────────────────────────────────────
    if estado == State.AGUARDANDO_PORTA:
        # Verificar créditos
        if creditos <= 0:
            plano = user.get("plano", DEFAULT_PLAN)
            plan_info = PLANS.get(plano, PLANS[DEFAULT_PLAN])
            await _send_md(
                update,
                Msg.SEM_CREDITOS.format(
                    creditos_total=plan_info["credits"],
                    plano=plan_info["label"],
                ),
            )
            sheets.update_state(chat_id, State.SEM_CREDITOS)
            return

        # Baixa foto da porta
        await update.message.reply_text("📥 Recebendo foto da porta...")
        try:
            path_porta = await _download_telegram_photo(update, context)
        except Exception:
            try:
                path_porta = await _download_telegram_document(update, context)
            except Exception as e:
                logger.error(f"Erro ao baixar imagem da porta: {e}")
                await _send_md(update, Msg.AGUARDANDO_IMAGEM)
                return

        sheets.save_image_url(chat_id, "foto_porta_url", path_porta)
        sheets.update_state(chat_id, State.GERANDO)

        # Atualizar os caminhos no dicionário local antes de passar
        user["foto_porta_url"] = path_porta
        
        # Inicia geração
        await _send_md(update, Msg.GERANDO)
        await _run_generation(update, context, user, chat_id)
        return

    # ─── Imagem em estado de feedback ────────────────────────────────────────
    if estado == State.AGUARDANDO_FEEDBACK:
        await _send_md(
            update,
            "Você está no menu de opções\\! Escolha uma das opções abaixo:",
            reply_markup=_feedback_keyboard(),
        )
        return

    # ─── Outros estados ───────────────────────────────────────────────────────
    await _send_md(update, "📸 Recebi sua foto\\! Digite /start para iniciar uma nova simulação\\.")


# ─── Lógica de Geração ────────────────────────────────────────────────────────

async def _run_generation(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    user: dict,
    chat_id: int,
):
    """
    Executa a geração de imagem e entrega o resultado ao cliente.
    Desconta crédito e atualiza estado.
    """
    ambiente_path = user.get("foto_ambiente_url", "")
    porta_path    = user.get("foto_porta_url", "")

    if not ambiente_path or not porta_path:
        await _send_md(update, Msg.ERRO_GERACAO)
        sheets.update_state(chat_id, State.AGUARDANDO_AMBIENTE)
        return

    # Gera a imagem
    img_bytes, erro_msg = generate_door_simulation(ambiente_path, porta_path)

    if not img_bytes:
        msg_erro = Msg.ERRO_GERACAO
        if erro_msg:
            msg_erro += f"\n\n*Detalhe técnico:* `{_escape_md(erro_msg)}`"
            
        await _send_md(update, msg_erro)
        sheets.update_state(chat_id, State.AGUARDANDO_AMBIENTE)
        return

    # Desconta crédito
    creditos_restantes = sheets.deduct_credit(chat_id)

    # Envia imagem gerada
    try:
        await context.bot.send_photo(
            chat_id=chat_id,
            photo=io.BytesIO(img_bytes),
            caption="✅ Simulação gerada! O que achou?",
        )
    except Exception as e:
        logger.error(f"Erro ao enviar imagem gerada: {e}")
        await _send_md(update, Msg.ERRO_GERACAO)
        return

    # Menu pós-geração
    creditos_msg = (
        f"\n_Você tem {creditos_restantes} simulação\\(ões\\) restante\\(s\\)\\._"
        if creditos_restantes > 0
        else "\n_Você não tem mais simulações neste plano\\._"
    )
    await _send_md(
        update,
        Msg.RESULTADO + "\n\n" + Msg.MENU_FEEDBACK + creditos_msg,
        reply_markup=_feedback_keyboard(),
    )

    sheets.update_state(chat_id, State.AGUARDANDO_FEEDBACK)
    logger.info(f"Imagem entregue: {chat_id} — créditos restantes: {creditos_restantes}")


# ─── Handlers de Botão Inline ────────────────────────────────────────────────

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Processa cliques no teclado inline."""
    query   = update.callback_query
    chat_id = update.effective_chat.id
    data    = query.data

    await query.answer()  # Remove o "loading" no botão

    user = sheets.get_user(chat_id)
    if not user:
        await _send_md(update, Msg.BOAS_VINDAS)
        return

    if data == "gerar_novamente":
        await _handle_gerar_novamente(update, context, user)
    elif data == "novo_ambiente":
        await _handle_novo_ambiente(update, context, user)
    elif data == "encerrar":
        await _handle_encerrar(update, context, user)


async def _handle_gerar_novamente(
    update: Update, context: ContextTypes.DEFAULT_TYPE, user: dict
):
    """Gera novamente com as mesmas duas imagens."""
    chat_id  = update.effective_chat.id
    creditos = int(user.get("creditos_restantes", 0))

    # Recarregar usuário para ter dados atuais
    user = sheets.get_user(chat_id)
    creditos = int(user.get("creditos_restantes", 0))

    if creditos <= 0:
        plano = user.get("plano", DEFAULT_PLAN)
        plan_info = PLANS.get(plano, PLANS[DEFAULT_PLAN])
        await _send_md(
            update,
            Msg.SEM_CREDITOS.format(
                creditos_total=plan_info["credits"],
                plano=plan_info["label"],
            ),
        )
        sheets.update_state(chat_id, State.SEM_CREDITOS)
        return

    await _send_md(update, Msg.GERANDO)
    sheets.update_state(chat_id, State.GERANDO)
    await _run_generation(update, context, user, chat_id)


async def _handle_novo_ambiente(
    update: Update, context: ContextTypes.DEFAULT_TYPE, user: dict
):
    """Reinicia o fluxo para um novo ambiente (pede novas fotos)."""
    chat_id = update.effective_chat.id
    sheets.reset_images(chat_id)
    sheets.update_state(chat_id, State.AGUARDANDO_AMBIENTE)
    await _send_md(
        update,
        "🔁 Vamos simular outro ambiente\\!\n\n"
        "Envie a foto do novo *ambiente* onde você quer instalar a porta\\.",
    )


async def _handle_encerrar(
    update: Update, context: ContextTypes.DEFAULT_TYPE, user: dict
):
    """Encerra o atendimento sem apagar o histórico."""
    chat_id = update.effective_chat.id
    sheets.update_state(chat_id, State.ENCERRADO)
    # Verifica se precisa salvar o nome antes de encerrar
    nome = user.get("nome", "")
    if not nome:
        await _send_md(
            update,
            "Antes de encerrar, qual é o seu nome? Quero te reconhecer na próxima vez\\! 😊"
        )
        # Próxima mensagem de texto será capturada por handle_text com estado ENCERRADO
        # Aqui ficamos em ENCERRADO para identificar que precisamos do nome
        return
    await _send_md(update, Msg.ENCERRAMENTO)


# ─── Handler padrão para mídias não-imagem ───────────────────────────────────

async def handle_other_media(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Responde para vídeo, áudio, stickers, etc."""
    await _send_md(
        update,
        "😊 Recebi sua mensagem\\!\n\n"
        "Por enquanto, eu só processo *imagens* \\(fotos\\)\\.\n"
        "Envie a foto do ambiente ou da porta para continuarmos\\!",
    )


# ─── Utilitários ─────────────────────────────────────────────────────────────

def _escape_md(text: str) -> str:
    """Escapa caracteres especiais do MarkdownV2."""
    special = r"\_*[]()~`>#+-=|{}.!"
    return "".join(f"\\{c}" if c in special else c for c in text)


# ─── Erros ───────────────────────────────────────────────────────────────────

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    """Log de erros não capturados."""
    logger.error(f"Erro não capturado: {context.error}", exc_info=context.error)


# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    global sheets

    sheets = SheetsManager()

    # Ativa o servidor web fake para o Render.com não desligar o bot (Free Tier)
    keep_alive()

    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # Comandos
    app.add_handler(CommandHandler("start",  cmd_start))
    app.add_handler(CommandHandler("menu",   cmd_menu))
    app.add_handler(CommandHandler("status", cmd_status))

    # Fotos e documentos (imagens enviadas como arquivo)
    app.add_handler(
        MessageHandler(filters.PHOTO | (filters.Document.IMAGE), handle_image)
    )

    # Texto
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    # Outros tipos de mídia
    app.add_handler(
        MessageHandler(
            filters.AUDIO | filters.VIDEO | filters.VOICE | filters.Sticker.ALL,
            handle_other_media,
        )
    )

    # Botões inline
    app.add_handler(CallbackQueryHandler(handle_callback))

    # Erro global
    app.add_error_handler(error_handler)

    logger.info("🚪 Simulador de Portas Bot iniciado. Aguardando mensagens...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()

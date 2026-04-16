"""
core/logic.py — Lógica de conversação agnóstica de canal.
"""
import logging
from typing import Tuple, Optional, Any
from .sheets import SheetsManager
from .config_niche import get_msg
from .config_base import PLANS, DEFAULT_PLAN
from bot.ai_generator import generate_door_simulation # Mantemos por enquanto

logger = logging.getLogger(__name__)

class State:
    NOVO               = "NOVO"
    AGUARDANDO_AMBIENTE = "AGUARDANDO_AMBIENTE"
    AGUARDANDO_PORTA    = "AGUARDANDO_PORTA"
    GERANDO             = "GERANDO"
    AGUARDANDO_FEEDBACK = "AGUARDANDO_FEEDBACK"
    ENCERRADO           = "ENCERRADO"
    SEM_CREDITOS        = "SEM_CREDITOS"

class ConversationLogic:
    def __init__(self, sheets_manager: SheetsManager):
        self.sheets = sheets_manager

    def process_message(self, identifier: str, col_id: str, text: str = None, image_path: str = None) -> Tuple[str, Optional[Any]]:
        """
        Processa uma interação e retorna (texto_resposta, markup/adicional).
        identifier: chat_id ou telefone
        col_id: 'chat_id' ou 'telefone'
        """
        user = self.sheets._get_row(identifier, col_id)
        if not user:
            user = self.sheets.create_user(telegram_id=identifier if col_id == "chat_id" else "", 
                                          phone=identifier if col_id == "telefone" else "")
            return get_msg("welcome"), None

        estado = user.get("estado", State.NOVO)
        creditos = int(user.get("creditos_restantes", 0))

        # Fluxo de Nome (se for novo)
        if estado == State.NOVO and not user.get("nome"):
            if text:
                self.sheets.update_user(identifier, col_id, "nome", text)
                self.sheets.update_user(identifier, col_id, "estado", State.AGUARDANDO_AMBIENTE)
                return f"Prazer, {text}! 😊\n\nEnvie a foto do ambiente para começar.", None
            return "Qual é o seu nome?", None

        # Recebendo Imagem
        if image_path:
            if estado in (State.AGUARDANDO_AMBIENTE, State.NOVO):
                self.sheets.update_user(identifier, col_id, "foto_ambiente_url", image_path)
                self.sheets.update_user(identifier, col_id, "estado", State.AGUARDANDO_PORTA)
                return get_msg("ask_item"), None

            if estado == State.AGUARDANDO_PORTA:
                if creditos <= 0:
                    return get_msg("no_credits", plano=user.get("plano")), "SEM_CREDITOS"
                
                self.sheets.update_user(identifier, col_id, "foto_porta_url", image_path)
                self.sheets.update_user(identifier, col_id, "estado", State.GERANDO)
                return "GERAR", None # Sinal para o bot disparar a geração real

        # Comandos de Texto (Status/Menu)
        if text:
            t = text.lower()
            if "/status" in t or "status" in t:
                usadas = int(user.get("total_geracoes", 0))
                restantes = int(user.get("creditos_restantes", 0))
                total_plano = usadas + restantes
                return (
                    f"📊 *Seu Painel*\n\n"
                    f"👤 Nome: {user.get('nome')}\n"
                    f"🎫 Plano: *{user.get('plano').upper()}*\n"
                    f"✨ Créditos: *{usadas} / {total_plano}* (usados/total)\n\n"
                    "O que deseja fazer agora?\n" + get_msg("menu")
                ), None

        return "📸 Por favor, envie uma foto para continuar!", None

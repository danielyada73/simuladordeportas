"""
sheets.py — Integração com Google Sheets
Gerencia usuários, estados, créditos e histórico de conversas.
"""
import logging
from datetime import datetime
from typing import Optional, Dict, Any

import gspread
from google.oauth2.service_account import Credentials

from config import GOOGLE_SERVICE_ACCOUNT_JSON, GOOGLE_SHEETS_SPREADSHEET_ID, PLANS, DEFAULT_PLAN

logger = logging.getLogger(__name__)

# Escopos necessários para leitura/escrita
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

# Colunas da planilha — mantidas em ordem para append correto
COLUMNS = [
    "chat_id",
    "nome",
    "telefone",
    "email",
    "plano",
    "creditos_restantes",
    "total_geracoes",
    "estado",
    "foto_ambiente_url",
    "foto_porta_url",
    "data_cadastro",
    "ultimo_contato",
]


class SheetsManager:
    def __init__(self):
        import os
        env_creds = os.environ.get("GOOGLE_CREDENTIALS_JSON")
        
        if env_creds:
            import json
            try:
                creds_info = json.loads(env_creds)
                creds = Credentials.from_service_account_info(
                    creds_info, scopes=SCOPES
                )
            except Exception as e:
                logger.error(f"Erro ao carregar credenciais do JSON na variável de ambiente: {e}")
                raise
        else:
            creds = Credentials.from_service_account_file(
                GOOGLE_SERVICE_ACCOUNT_JSON, scopes=SCOPES
            )
        self._client = gspread.authorize(creds)
        self._sheet  = self._client.open_by_key(GOOGLE_SHEETS_SPREADSHEET_ID)
        self._ws     = self._sheet.worksheet("Usuarios")
        logger.info("Google Sheets conectado com sucesso.")

    # ─── Helpers internos ────────────────────────────────────────────────────

    def _get_row_by_chat_id(self, chat_id: int) -> Optional[Dict[str, Any]]:
        """Retorna a linha do usuário como dict ou None se não existir."""
        try:
            records = self._ws.get_all_records()
            for i, row in enumerate(records, start=2):  # linha 1 = cabeçalho
                if str(row.get("chat_id")) == str(chat_id):
                    row["_row_index"] = i
                    return row
            return None
        except Exception as e:
            logger.error(f"Erro ao buscar usuário {chat_id}: {e}")
            return None

    def _col_index(self, col_name: str) -> int:
        """Retorna o índice (1-based) da coluna pelo nome."""
        return COLUMNS.index(col_name) + 1

    def _update_cell(self, row_index: int, col_name: str, value):
        """Atualiza uma célula específica."""
        col_idx = self._col_index(col_name)
        self._ws.update_cell(row_index, col_idx, str(value))

    # ─── API Pública ─────────────────────────────────────────────────────────

    def get_user(self, chat_id: int) -> Optional[Dict[str, Any]]:
        """Busca usuário pelo chat_id. Retorna dict ou None."""
        return self._get_row_by_chat_id(chat_id)

    def create_user(self, chat_id: int, plano: str = DEFAULT_PLAN) -> Dict[str, Any]:
        """Cria um novo usuário com o plano especificado."""
        now = datetime.now().strftime("%d/%m/%Y %H:%M")
        credits = PLANS.get(plano, PLANS[DEFAULT_PLAN])["credits"]

        new_row = {
            "chat_id":            str(chat_id),
            "nome":               "",
            "telefone":           "",
            "email":              "",
            "plano":              plano,
            "creditos_restantes": credits,
            "total_geracoes":     0,
            "estado":             "AGUARDANDO_AMBIENTE",
            "foto_ambiente_url":  "",
            "foto_porta_url":     "",
            "data_cadastro":      now,
            "ultimo_contato":     now,
        }
        # Append na ordem das colunas
        self._ws.append_row([new_row[col] for col in COLUMNS])
        logger.info(f"Novo usuário criado: {chat_id} — plano {plano}")
        return new_row

    def update_state(self, chat_id: int, state: str):
        """Atualiza o estado da conversa do usuário."""
        user = self._get_row_by_chat_id(chat_id)
        if not user:
            return
        self._update_cell(user["_row_index"], "estado", state)
        self._update_cell(user["_row_index"], "ultimo_contato",
                          datetime.now().strftime("%d/%m/%Y %H:%M"))
        logger.debug(f"Estado atualizado: {chat_id} → {state}")

    def save_image_url(self, chat_id: int, field: str, url: str):
        """
        Salva URL de imagem.
        field: 'foto_ambiente_url' ou 'foto_porta_url'
        """
        user = self._get_row_by_chat_id(chat_id)
        if not user:
            return
        self._update_cell(user["_row_index"], field, url)
        logger.debug(f"URL de imagem salva: {chat_id} — {field}")

    def deduct_credit(self, chat_id: int) -> int:
        """
        Desconta 1 crédito e incrementa total_geracoes.
        Retorna o novo saldo de créditos.
        """
        user = self._get_row_by_chat_id(chat_id)
        if not user:
            return 0
        current = int(user.get("creditos_restantes", 0))
        total   = int(user.get("total_geracoes", 0))
        new_credits = max(0, current - 1)
        self._update_cell(user["_row_index"], "creditos_restantes", new_credits)
        self._update_cell(user["_row_index"], "total_geracoes", total + 1)
        logger.info(f"Crédito descontado: {chat_id} — restam {new_credits}")
        return new_credits

    def save_name(self, chat_id: int, nome: str):
        """Salva o nome do usuário."""
        user = self._get_row_by_chat_id(chat_id)
        if not user:
            return
        self._update_cell(user["_row_index"], "nome", nome)
        logger.info(f"Nome salvo: {chat_id} → {nome}")

    def set_plan(self, chat_id: int, plano: str):
        """Atualiza o plano e adiciona os créditos correspondentes."""
        user = self._get_row_by_chat_id(chat_id)
        if not user:
            return
        credits_to_add = PLANS.get(plano, PLANS[DEFAULT_PLAN])["credits"]
        current = int(user.get("creditos_restantes", 0))
        new_total = current + credits_to_add
        self._update_cell(user["_row_index"], "plano", plano)
        self._update_cell(user["_row_index"], "creditos_restantes", new_total)
        logger.info(f"Plano atualizado: {chat_id} → {plano}, créditos: {new_total}")

    def reset_images(self, chat_id: int):
        """Limpa as URLs de imagem para nova rodada."""
        user = self._get_row_by_chat_id(chat_id)
        if not user:
            return
        self._update_cell(user["_row_index"], "foto_ambiente_url", "")
        self._update_cell(user["_row_index"], "foto_porta_url", "")

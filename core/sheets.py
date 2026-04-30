"""
core/sheets.py — Integração com Google Sheets (Core)
Gerencia usuários, estados, créditos e histórico de conversas para múltiplos canais.
"""
import logging
from datetime import datetime
from typing import Optional, Dict, Any
import time

import gspread
from google.oauth2.service_account import Credentials

# Importamos do config central (que criaremos a seguir)
from .config_base import GOOGLE_SERVICE_ACCOUNT_JSON, GOOGLE_SHEETS_SPREADSHEET_ID, PLANS, DEFAULT_PLAN

logger = logging.getLogger(__name__)

SHEETS_INIT_RETRIES = 6
SHEETS_INIT_BACKOFF_SECONDS = 2

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

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
        import json
        env_creds = os.environ.get("GOOGLE_CREDENTIALS_JSON")
        
        if env_creds:
            try:
                creds_info = json.loads(env_creds)
                creds = Credentials.from_service_account_info(creds_info, scopes=SCOPES)
            except Exception as e:
                logger.error(f"Erro ao carregar credenciais do JSON: {e}")
                raise
        else:
            creds = Credentials.from_service_account_file(GOOGLE_SERVICE_ACCOUNT_JSON, scopes=SCOPES)

        self._client = gspread.authorize(creds)

        last_exc = None
        for attempt in range(1, SHEETS_INIT_RETRIES + 1):
            try:
                self._sheet = self._client.open_by_key(GOOGLE_SHEETS_SPREADSHEET_ID)
                self._ws = self._sheet.worksheet("Usuarios")
                logger.info("Google Sheets conectado.")
                return
            except Exception as exc:
                last_exc = exc
                if attempt >= SHEETS_INIT_RETRIES:
                    break
                wait_seconds = SHEETS_INIT_BACKOFF_SECONDS * attempt
                logger.warning(
                    "Falha ao iniciar Google Sheets core (tentativa %s/%s). Nova tentativa em %ss. Erro: %s",
                    attempt,
                    SHEETS_INIT_RETRIES,
                    wait_seconds,
                    exc,
                )
                time.sleep(wait_seconds)

        raise last_exc

    def _get_row(self, identifier: str, col_name: str = "chat_id") -> Optional[Dict[str, Any]]:
        """Busca uma linha por qualquer coluna identificadora."""
        try:
            records = self._ws.get_all_records()
            for i, row in enumerate(records, start=2):
                if str(row.get(col_name)) == str(identifier):
                    row["_row_index"] = i
                    return row
            return None
        except Exception as e:
            logger.error(f"Erro ao buscar {col_name}={identifier}: {e}")
            return None

    def _col_index(self, col_name: str) -> int:
        return COLUMNS.index(col_name) + 1

    def _update_cell(self, row_index: int, col_name: str, value):
        col_idx = self._col_index(col_name)
        self._ws.update_cell(row_index, col_idx, str(value))

    # ─── API Pública ─────────────────────────────────────────────────────────

    def get_user_by_telegram(self, chat_id: Any) -> Optional[Dict[str, Any]]:
        return self._get_row(str(chat_id), "chat_id")

    def get_user_by_phone(self, phone: str) -> Optional[Dict[str, Any]]:
        return self._get_row(phone, "telefone")

    def create_user(self, telegram_id: str = "", phone: str = "", plano: str = DEFAULT_PLAN) -> Dict[str, Any]:
        """Cria usuário com Telegram ID ou Telefone."""
        now = datetime.now().strftime("%d/%m/%Y %H:%M")
        credits = PLANS.get(plano, PLANS[DEFAULT_PLAN])["credits"]

        new_row = {
            "chat_id":            telegram_id,
            "nome":               "",
            "telefone":           phone,
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
        self._ws.append_row([new_row[col] for col in COLUMNS])
        return new_row

    def update_user(self, identifier: str, col_id: str, field: str, value: Any):
        """Atualiza um campo genérico de um usuário."""
        user = self._get_row(identifier, col_id)
        if not user: return
        self._update_cell(user["_row_index"], field, value)
        self._update_cell(user["_row_index"], "ultimo_contato", datetime.now().strftime("%d/%m/%Y %H:%M"))

    def deduct_credit(self, identifier: str, col_id: str = "chat_id") -> int:
        user = self._get_row(identifier, col_id)
        if not user: return 0
        current = int(user.get("creditos_restantes", 0))
        total   = int(user.get("total_geracoes", 0))
        new_credits = max(0, current - 1)
        self._update_cell(user["_row_index"], "creditos_restantes", new_credits)
        self._update_cell(user["_row_index"], "total_geracoes", total + 1)
        return new_credits

    def reset_images(self, identifier: str, col_id: str = "chat_id"):
        user = self._get_row(identifier, col_id)
        if not user: return
        self._update_cell(user["_row_index"], "foto_ambiente_url", "")
        self._update_cell(user["_row_index"], "foto_porta_url", "")

import json
import logging
import os
import re
from dataclasses import dataclass
from copy import deepcopy
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

import gspread
from google.oauth2.service_account import Credentials


logger = logging.getLogger(__name__)

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

CLIENTS_SHEET_NAME = os.getenv("ALPHA_OS_CLIENTS_SHEET", "AlphaOS_Clients")
SESSIONS_SHEET_NAME = os.getenv("ALPHA_OS_SESSIONS_SHEET", "AlphaOS_Sessions")
BLOBS_SHEET_NAME = os.getenv("ALPHA_OS_BLOBS_SHEET", "AlphaOS_Blobs")

CLIENTS_HEADERS = ["client_id", "client_name", "created_at", "updated_at", "data_json"]
SESSIONS_HEADERS = ["phone", "last_client_id", "updated_at"]
BLOBS_HEADERS = ["client_id", "field_key", "version", "part_index", "content"]

DETACHED_TEXT_PATHS = (
    "briefing",
    "artifacts.googleSourceText",
    "artifacts.metaSourceText",
    "artifacts.googleAdsJson",
    "artifacts.metaAdsJson",
    "artifacts.metricsJson",
)

INLINE_JSON_SOFT_LIMIT = 45000
BLOB_CHUNK_SIZE = 45000


def _default_platform_config() -> Dict[str, Any]:
    return {
        "common": {
            "landing_page_url": "",
            "thank_you_url": "",
            "country": "Brazil",
            "language": "Portuguese",
            "timezone": "America/Sao_Paulo",
            "currency_code": "BRL",
        },
        "google": {
            "customer_id": "",
            "manager_customer_id": "",
            "conversion_action_name": "",
            "conversion_category": "SUBMIT_LEAD_FORM",
        },
        "meta": {
            "ad_account_id": "",
            "page_id": "",
            "pixel_id": "",
            "instagram_actor_id": "",
            "objective": "OUTCOME_TRAFFIC",
            "cta_type": "LEARN_MORE",
        },
    }


def _default_artifacts() -> Dict[str, Any]:
    return {
        "googleAdsJson": "",
        "metaAdsJson": "",
        "metricsJson": "",
        "googleSourceText": "",
        "metaSourceText": "",
        "analysis": {
            "google": {},
            "meta": {},
        },
    }


def _default_stages() -> Dict[str, Any]:
    return {
        "onboarding": {"status": "waiting", "message": ""},
        "phase2": {"status": "waiting", "message": ""},
        "googlePublish": {"status": "waiting", "message": ""},
        "metaPublish": {"status": "waiting", "message": ""},
        "dailyAnalysis": {"status": "waiting", "message": ""},
        "weeklyAnalysis": {"status": "waiting", "message": ""},
    }


def _merge_defaults(target: Dict[str, Any], defaults: Dict[str, Any]) -> Dict[str, Any]:
    for key, value in defaults.items():
        if key not in target:
            target[key] = value
            continue
        if isinstance(value, dict) and isinstance(target.get(key), dict):
            _merge_defaults(target[key], value)
    return target


def normalize_client(client: Dict[str, Any]) -> Dict[str, Any]:
    client = dict(client or {})
    client.setdefault("status", "briefing_received")
    _merge_defaults(
        client,
        {
            "stages": _default_stages(),
            "artifacts": _default_artifacts(),
            "config": _default_platform_config(),
            "logs": [],
            "storage": {"blob_fields": {}},
        },
    )
    return client


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _slugify(value: str) -> str:
    value = (value or "").strip().lower()
    value = value.encode("ascii", errors="ignore").decode("ascii")
    value = re.sub(r"[^a-z0-9]+", "-", value).strip("-")
    return value[:60] or "cliente"


def _get_nested(data: Dict[str, Any], path: str) -> Any:
    cursor: Any = data
    for part in [p for p in str(path or "").split(".") if p]:
        if not isinstance(cursor, dict):
            return None
        cursor = cursor.get(part)
    return cursor


def _set_nested(data: Dict[str, Any], path: str, value: Any):
    parts = [p for p in str(path or "").split(".") if p]
    if not parts:
        return
    cursor = data
    for part in parts[:-1]:
        next_value = cursor.get(part)
        if not isinstance(next_value, dict):
            next_value = {}
            cursor[part] = next_value
        cursor = next_value
    cursor[parts[-1]] = value


def _delete_nested(data: Dict[str, Any], path: str):
    parts = [p for p in str(path or "").split(".") if p]
    if not parts:
        return
    cursor: Any = data
    for part in parts[:-1]:
        if not isinstance(cursor, dict):
            return
        cursor = cursor.get(part)
    if isinstance(cursor, dict):
        cursor.pop(parts[-1], None)


def _chunk_text(text: str, chunk_size: int = BLOB_CHUNK_SIZE) -> List[str]:
    value = str(text or "")
    if not value:
        return []
    return [value[i : i + chunk_size] for i in range(0, len(value), chunk_size)]


def _load_google_credentials() -> Credentials:
    env_json = os.environ.get("GOOGLE_CREDENTIALS_JSON")
    if env_json:
        try:
            info = json.loads(env_json)
            return Credentials.from_service_account_info(info, scopes=SCOPES)
        except Exception as exc:
            raise RuntimeError(f"Invalid GOOGLE_CREDENTIALS_JSON: {exc}") from exc

    file_path = os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON", "credentials.json")
    if not os.path.exists(file_path):
        raise RuntimeError("Missing GOOGLE_CREDENTIALS_JSON or GOOGLE_SERVICE_ACCOUNT_JSON file.")
    return Credentials.from_service_account_file(file_path, scopes=SCOPES)


def _open_or_create_worksheet(sheet, name: str, headers: List[str]):
    try:
        ws = sheet.worksheet(name)
    except gspread.WorksheetNotFound:
        ws = sheet.add_worksheet(title=name, rows=1000, cols=max(10, len(headers)))
        ws.append_row(headers)
        return ws

    # Ensure headers exist
    existing = ws.row_values(1)
    if existing != headers:
        if not existing:
            ws.append_row(headers)
        else:
            logger.warning("Worksheet %s headers differ; expected %s got %s", name, headers, existing)
    return ws


@dataclass
class AlphaOSStore:
    spreadsheet_id: str

    def __post_init__(self):
        creds = _load_google_credentials()
        client = gspread.authorize(creds)
        sheet = client.open_by_key(self.spreadsheet_id)
        self._clients_ws = _open_or_create_worksheet(sheet, CLIENTS_SHEET_NAME, CLIENTS_HEADERS)
        self._sessions_ws = _open_or_create_worksheet(sheet, SESSIONS_SHEET_NAME, SESSIONS_HEADERS)
        self._blobs_ws = _open_or_create_worksheet(sheet, BLOBS_SHEET_NAME, BLOBS_HEADERS)

    def _clients_records(self) -> List[Dict[str, Any]]:
        return self._clients_ws.get_all_records()

    def _sessions_records(self) -> List[Dict[str, Any]]:
        return self._sessions_ws.get_all_records()

    def _blob_records(self) -> List[Dict[str, Any]]:
        return self._blobs_ws.get_all_records()

    def _store_blob_field(self, client_id: str, field_key: str, value: str) -> Dict[str, Any]:
        text = str(value or "")
        version = _utc_now_iso()
        rows = [
            [client_id, field_key, version, index, chunk]
            for index, chunk in enumerate(_chunk_text(text), start=1)
        ]
        if rows:
            self._blobs_ws.append_rows(rows, value_input_option="RAW")
        return {
            "sheet": BLOBS_SHEET_NAME,
            "version": version,
            "parts": len(rows),
            "chars": len(text),
        }

    def _load_blob_field(self, client_id: str, field_key: str, metadata: Dict[str, Any], client_blob_rows: Optional[List[Dict[str, Any]]] = None) -> str:
        version = str((metadata or {}).get("version") or "").strip()
        if not client_id or not field_key or not version:
            return ""

        rows = client_blob_rows if client_blob_rows is not None else self._blob_records()
        parts = []
        for row in rows:
            if str(row.get("client_id") or "").strip() != client_id:
                continue
            if str(row.get("field_key") or "").strip() != field_key:
                continue
            if str(row.get("version") or "").strip() != version:
                continue
            try:
                part_index = int(row.get("part_index") or 0)
            except Exception:
                part_index = 0
            parts.append((part_index, str(row.get("content") or "")))
        parts.sort(key=lambda item: item[0])
        return "".join(content for _, content in parts)

    def _hydrate_blob_fields(self, client: Dict[str, Any]) -> Dict[str, Any]:
        client = normalize_client(client)
        client_id = str(client.get("id") or client.get("client_id") or "").strip()
        blob_fields = (((client.get("storage") or {}).get("blob_fields")) or {})
        if not client_id or not isinstance(blob_fields, dict) or not blob_fields:
            return client

        client_rows = [row for row in self._blob_records() if str(row.get("client_id") or "").strip() == client_id]
        for field_key, metadata in blob_fields.items():
            if not isinstance(metadata, dict):
                continue
            content = self._load_blob_field(client_id, field_key, metadata, client_rows)
            if content:
                _set_nested(client, field_key, content)
        return client

    def _existing_blob_meta(self, row: Dict[str, Any]) -> Dict[str, Any]:
        try:
            data = json.loads(row.get("data_json") or "{}")
        except Exception:
            return {}
        return (((data.get("storage") or {}).get("blob_fields")) or {}) if isinstance(data, dict) else {}

    def list_clients(self) -> List[Dict[str, Any]]:
        items = []
        for row in self._clients_records():
            items.append(
                {
                    "client_id": str(row.get("client_id") or ""),
                    "client_name": str(row.get("client_name") or ""),
                    "created_at": str(row.get("created_at") or ""),
                    "updated_at": str(row.get("updated_at") or ""),
                }
            )
        items.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        return items

    def _find_client_row(self, client_id: str) -> Optional[Tuple[int, Dict[str, Any]]]:
        client_id = str(client_id or "").strip()
        if not client_id:
            return None
        records = self._clients_records()
        for idx, row in enumerate(records, start=2):  # 1 is header
            if str(row.get("client_id")) == client_id:
                return idx, row
        return None

    def get_client(self, client_id: str) -> Optional[Dict[str, Any]]:
        found = self._find_client_row(client_id)
        if not found:
            return None
        _, row = found
        try:
            data = json.loads(row.get("data_json") or "{}")
            return self._hydrate_blob_fields(data)
        except Exception:
            return None

    def find_client(self, term: str) -> Optional[Dict[str, Any]]:
        term_norm = (term or "").strip().lower()
        if not term_norm:
            return None
        for client in self.list_clients():
            if term_norm == client["client_id"].lower():
                return self.get_client(client["client_id"])
        for client in self.list_clients():
            if term_norm in client["client_name"].lower():
                return self.get_client(client["client_id"])
        return None

    def upsert_client(self, client: Dict[str, Any]):
        client = normalize_client(client)
        client_id = str(client.get("id") or client.get("client_id") or "").strip()
        if not client_id:
            raise ValueError("client id missing")

        now = _utc_now_iso()
        client["updatedAt"] = now

        found = self._find_client_row(client_id)
        existing_full = self.get_client(client_id) if found else None
        existing_blob_meta = self._existing_blob_meta(found[1]) if found else {}

        client_to_store = deepcopy(client)
        storage = client_to_store.setdefault("storage", {})
        blob_fields_meta = storage.setdefault("blob_fields", {})

        for field_key in DETACHED_TEXT_PATHS:
            new_value = _get_nested(client, field_key)
            if not isinstance(new_value, str) or not new_value.strip():
                _delete_nested(client_to_store, field_key)
                blob_fields_meta.pop(field_key, None)
                continue

            old_value = _get_nested(existing_full or {}, field_key)
            if old_value == new_value and field_key in existing_blob_meta:
                metadata = existing_blob_meta[field_key]
            else:
                metadata = self._store_blob_field(client_id, field_key, new_value)

            _set_nested(client_to_store, field_key, "")
            blob_fields_meta[field_key] = metadata

        if not blob_fields_meta:
            storage.pop("blob_fields", None)
        if not storage:
            client_to_store.pop("storage", None)

        payload = json.dumps(client_to_store, ensure_ascii=False)
        if len(payload) > INLINE_JSON_SOFT_LIMIT:
            compact_client = deepcopy(client_to_store)
            logs = compact_client.get("logs")
            if isinstance(logs, list) and len(logs) > 25:
                compact_client["logs"] = logs[:25]
            payload = json.dumps(compact_client, ensure_ascii=False)
            client_to_store = compact_client

        if not found:
            created_at = client.get("createdAt") or now
            self._clients_ws.append_row(
                [client_id, client.get("name") or client.get("client_name") or "", created_at, now, payload]
            )
            return

        row_index, _ = found
        # Update 4 columns (name, updated_at, data_json)
        self._clients_ws.update_cell(row_index, 2, client.get("name") or client.get("client_name") or "")
        self._clients_ws.update_cell(row_index, 4, now)
        self._clients_ws.update_cell(row_index, 5, payload)

    def create_client(self, name: str, briefing: str) -> Dict[str, Any]:
        name = str(name or "").strip()
        briefing = str(briefing or "").strip()
        if not name:
            raise ValueError("Nome do cliente e obrigatorio.")
        if not briefing:
            raise ValueError("Briefing e obrigatorio.")

        now = _utc_now_iso()
        client_id = f"{_slugify(name)}-{int(datetime.now().timestamp())}"
        client = {
            "id": client_id,
            "name": name,
            "briefing": briefing,
            "status": "briefing_received",
            "createdAt": now,
            "updatedAt": now,
            "stages": _default_stages(),
            "artifacts": _default_artifacts(),
            "config": _default_platform_config(),
            "logs": [{"at": now, "type": "client_created", "message": "Briefing recebido via WhatsApp."}],
        }
        self.upsert_client(client)
        return client

    def update_client_config(self, client_id: str, path: str, value: Any) -> Dict[str, Any]:
        client = self.get_client(client_id)
        if not client:
            raise ValueError("Cliente nao encontrado.")

        parts = [part for part in str(path or "").split(".") if part]
        if not parts:
            raise ValueError("Caminho de configuracao invalido.")

        cursor = client.setdefault("config", {})
        for part in parts[:-1]:
            next_value = cursor.get(part)
            if not isinstance(next_value, dict):
                next_value = {}
                cursor[part] = next_value
            cursor = next_value

        cursor[parts[-1]] = value
        client.setdefault("logs", []).insert(
            0,
            {
                "at": _utc_now_iso(),
                "type": "config_updated",
                "message": f"Configuracao atualizada: {path}",
            },
        )
        self.upsert_client(client)
        return client

    def set_last_client_for_phone(self, phone: str, client_id: str):
        phone = str(phone or "").strip()
        client_id = str(client_id or "").strip()
        if not phone or not client_id:
            return
        now = _utc_now_iso()
        records = self._sessions_records()
        for idx, row in enumerate(records, start=2):
            if str(row.get("phone")) == phone:
                self._sessions_ws.update_cell(idx, 2, client_id)
                self._sessions_ws.update_cell(idx, 3, now)
                return
        self._sessions_ws.append_row([phone, client_id, now])

    def get_last_client_for_phone(self, phone: str) -> Optional[str]:
        phone = str(phone or "").strip()
        if not phone:
            return None
        for row in self._sessions_records():
            if str(row.get("phone")) == phone:
                return str(row.get("last_client_id") or "").strip() or None
        return None

import json
import os
import re
from typing import Dict, Optional, Tuple

import requests

from .store import AlphaOSStore


STAGES = {
    "onboarding": {
        "label": "Criar Monday do cliente",
        "env": "N8N_ONBOARDING_WEBHOOK_URL",
    },
    "phase2": {
        "label": "Gerar LP, criativos e campanhas",
        "env": "N8N_PHASE2_WEBHOOK_URL",
    },
    "googlePublish": {
        "label": "Publicar Google Ads pausado",
        "env": "N8N_GOOGLE_PUBLISH_WEBHOOK_URL",
    },
    "metaPublish": {
        "label": "Publicar Meta Ads pausado",
        "env": "N8N_META_PUBLISH_WEBHOOK_URL",
    },
    "dailyAnalysis": {
        "label": "Analise diaria",
        "env": "N8N_DAILY_ANALYSIS_WEBHOOK_URL",
    },
    "weeklyAnalysis": {
        "label": "Analise semanal",
        "env": "N8N_WEEKLY_ANALYSIS_WEBHOOK_URL",
    },
}

STAGE_ALIASES = {
    "monday": "onboarding",
    "onboarding": "onboarding",
    "briefing": "onboarding",
    "fase2": "phase2",
    "phase2": "phase2",
    "gerar": "phase2",
    "conteudo": "phase2",
    "google": "googlePublish",
    "googleads": "googlePublish",
    "meta": "metaPublish",
    "metaads": "metaPublish",
    "diaria": "dailyAnalysis",
    "diario": "dailyAnalysis",
    "daily": "dailyAnalysis",
    "semanal": "weeklyAnalysis",
    "weekly": "weeklyAnalysis",
}


def _norm(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").strip().lower())


def is_alpha_os_command(text: str) -> bool:
    t = _norm(text)
    if not t:
        return False
    return (
        t in ("ajuda", "help", "menu", "start", "/start")
        or t.startswith("novo cliente")
        or t.startswith("novo_cliente")
        or t in ("clientes", "listar clientes")
        or t.startswith("status")
        or t.startswith("rodar")
        or t.startswith("validar")
    )


def _help_text() -> str:
    return "\n".join(
        [
            "Alpha OS pronto.",
            "",
            "Comandos:",
            "novo cliente Nome do Cliente",
            "Briefing completo na linha seguinte",
            "",
            "clientes",
            "status Nome ou ID",
            "rodar Nome ou ID fase2",
            "rodar Nome ou ID monday",
            "rodar Nome ou ID diaria",
            "rodar Nome ou ID semanal",
        ]
    )


def _format_status(client: Dict) -> str:
    lines = [
        f"Cliente: {client.get('name')}",
        f"ID: {client.get('id')}",
        f"Status: {client.get('status')}",
        "",
    ]
    stages = client.get("stages", {})
    for key, meta in STAGES.items():
        state = stages.get(key, {})
        status = state.get("status", "waiting")
        msg = state.get("message") or ""
        label = meta["label"]
        lines.append(f"- {label}: {status}{f' ({msg})' if msg else ''}")
    return "\n".join(lines)


def _parse_new_client(raw: str) -> Tuple[str, str]:
    raw = (raw or "").strip()
    lines = raw.splitlines()
    first = lines[0] if lines else ""
    name = re.sub(r"^/?novo[_ ]cliente\s*", "", first, flags=re.IGNORECASE).strip()
    briefing = "\n".join(lines[1:]).strip()
    briefing = re.sub(r"^briefing\s*:\s*", "", briefing, flags=re.IGNORECASE).strip()
    return name, briefing


def _call_webhook(url: str, payload: Dict) -> Tuple[bool, str]:
    try:
        resp = requests.post(url, json=payload, timeout=30)
        if resp.status_code >= 400:
            return False, f"Webhook retornou {resp.status_code}: {resp.text[:200]}"
        return True, "Etapa enviada com sucesso."
    except Exception as exc:
        return False, f"Erro ao chamar webhook: {exc}"


class AlphaOSChat:
    def __init__(self):
        spreadsheet_id = os.getenv("GOOGLE_SHEETS_SPREADSHEET_ID", "")
        if not spreadsheet_id:
            raise RuntimeError("Missing GOOGLE_SHEETS_SPREADSHEET_ID")
        self.store = AlphaOSStore(spreadsheet_id=spreadsheet_id)

    def handle(self, phone: str, text: str) -> str:
        raw = (text or "").strip()
        t = _norm(raw)

        if not t or t in ("ajuda", "help", "menu", "start", "/start"):
            return _help_text()

        if t.startswith("novo cliente") or t.startswith("novo_cliente"):
            name, briefing = _parse_new_client(raw)
            if not name or not briefing:
                return "Envie assim:\n\nnovo cliente Nome do Cliente\nBriefing completo aqui..."
            client = self.store.create_client(name=name, briefing=briefing)
            self.store.set_last_client_for_phone(phone, client["id"])
            return f"Operacao criada para {client['name']}.\nID: {client['id']}\nProximo: rodar {client['id']} fase2"

        if t in ("clientes", "listar clientes"):
            clients = self.store.list_clients()
            if not clients:
                return "Nenhum cliente criado ainda."
            return "\n\n".join([f"{c['client_name']}\nID: {c['client_id']}\nStatus: briefing_received" for c in clients[:10]])

        if t.startswith("status"):
            term = raw.split(" ", 1)[1].strip() if " " in raw else ""
            client = self._resolve_client(phone, term)
            if not client:
                return "Nao encontrei esse cliente. Use 'clientes' para listar."
            return _format_status(client)

        if t.startswith("rodar"):
            parts = raw.split()
            if len(parts) < 2:
                return "Uso: rodar <nome ou id> <fase2|monday|diaria|semanal>"
            stage_alias = _norm(parts[-1])
            stage = STAGE_ALIASES.get(stage_alias)
            term = " ".join(parts[1:-1]).strip()
            client = self._resolve_client(phone, term)
            if not stage:
                return "Etapa invalida. Use monday, fase2, diaria ou semanal."
            if not client:
                return "Nao encontrei esse cliente. Use 'clientes' para listar."
            return self._run_stage(phone, client, stage)

        return _help_text()

    def _resolve_client(self, phone: str, term: str) -> Optional[Dict]:
        term = (term or "").strip()
        if not term:
            last = self.store.get_last_client_for_phone(phone)
            if last:
                return self.store.get_client(last)
            return None
        client = self.store.find_client(term)
        if client:
            self.store.set_last_client_for_phone(phone, client.get("id"))
        return client

    def _run_stage(self, phone: str, client: Dict, stage_key: str) -> str:
        meta = STAGES.get(stage_key)
        env = meta["env"]
        url = os.getenv(env, "").strip()

        stages = client.setdefault("stages", {})
        stage = stages.setdefault(stage_key, {"status": "waiting", "message": ""})

        if not url:
            stage["status"] = "needs_config"
            stage["message"] = f"Falta configurar {env}."
            self.store.upsert_client(client)
            return _format_status(client)

        payload = {
            "client_id": client.get("id"),
            "client_name": client.get("name"),
            "briefing": client.get("briefing"),
            "artifacts": client.get("artifacts", {}),
            "source": "simuladordeportas-whatsapp",
            "stage": stage_key,
            "from_phone": phone,
        }

        ok, message = _call_webhook(url, payload)
        stage["status"] = "done" if ok else "error"
        stage["message"] = message
        self.store.upsert_client(client)
        return _format_status(client)


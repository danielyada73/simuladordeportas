import json
import os
import re
import unicodedata
from typing import Dict, Optional, Tuple

import requests

from .campaign_ops import (
    analyze_google,
    analyze_meta,
    prepare_google_payload,
    prepare_meta_payload,
    publish_google,
    publish_meta,
    readiness_text,
)
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
        or t in ("config", "infra", "setup")
        or t.startswith("definir ")
        or t.startswith("configurar ")
        or t.startswith("preparar ")
        or t.startswith("publicar ")
        or t.startswith("publica ")
        or t.startswith("publique ")
        or t.startswith("analisar ")
        or t.startswith("analisa ")
        or t.startswith("analise ")
        or t.startswith("o que falta")
        or t.startswith("prontidao")
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
            "Alpha OS pronto para operar.",
            "",
            "Voce pode falar comigo assim:",
            "novo cliente Nome do Cliente",
            "Briefing completo na linha seguinte",
            "",
            "config",
            "clientes",
            "status Nome ou ID",
            "definir Nome ou ID campo valor",
            "preparar google Nome ou ID",
            "preparar meta Nome ou ID",
            "publicar google Nome ou ID",
            "publicar meta Nome ou ID",
            "analisar google Nome ou ID mensal",
            "analisar meta Nome ou ID mensal",
            "o que falta Nome ou ID",
            "rodar Nome ou ID monday",
            "rodar Nome ou ID fase2",
            "validar Nome ou ID",
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


def _call_n8n_form(url: str, client_name: str, briefing: str) -> Tuple[bool, str]:
    """
    Submete um Form Trigger do n8n (workflow 01) via HTTP.

    Campos do seu form atual:
      field-0 = Nome do Cliente
      field-1 = Segmento
      field-2 = Transcrição da Reunião (file)
      field-3 = Prazo de Entrega
    """
    try:
        prazo = os.getenv("ALPHA_OS_ONBOARDING_PRAZO", "15 Dias").strip() or "15 Dias"
        segmento = os.getenv("ALPHA_OS_ONBOARDING_SEGMENTO", "via WhatsApp").strip() or "via WhatsApp"

        data = {
            "field-0": client_name,
            "field-1": segmento,
            "field-3": prazo,
        }
        files = {
            "field-2": ("transcricao.txt", (briefing or "").encode("utf-8"), "text/plain"),
        }

        resp = requests.post(url, data=data, files=files, timeout=30)
        if resp.status_code >= 400:
            return False, f"Form do n8n retornou {resp.status_code}: {resp.text[:200]}"
        return True, "Onboarding enviado para o n8n (workflow 01)."
    except Exception as exc:
        return False, f"Erro ao enviar para o Form do n8n: {exc}"


def _strip_accents(text: str) -> str:
    return "".join(ch for ch in unicodedata.normalize("NFKD", text or "") if not unicodedata.combining(ch))


def _norm_cmp(text: str) -> str:
    t = _strip_accents(text).strip().lower()
    t = re.sub(r"\s*-\s*", "-", t)
    t = re.sub(r"\s+", " ", t)
    return t


def _mark_stage(client: Dict, stage_key: str, status: str, message: str):
    stages = client.setdefault("stages", {})
    stage = stages.setdefault(stage_key, {"status": "waiting", "message": ""})
    stage["status"] = status
    stage["message"] = message


def _candidate_board_names(client_name: str) -> Dict[str, Tuple[str, ...]]:
    return {
        "briefing_board_id": (
            f"{client_name}- 1. BRIEFING",
            f"{client_name} - 1. BRIEFING",
        ),
        "lp_board_id": (
            f"{client_name}- 2. CRIACAO DE LP",
            f"{client_name}- 2. CRIAÇÃO DE LP",
            f"{client_name} - 2. CRIACAO DE LP",
            f"{client_name} - 2. CRIAÇÃO DE LP",
        ),
        "campanhas_board_id": (
            f"{client_name}- 3. CAMPANHAS",
            f"{client_name} - 3. CAMPANHAS",
        ),
        "otimizacoes_board_id": (
            f"{client_name}- 4. OTIMIZACOES",
            f"{client_name}- 4. OTIMIZAÇÕES",
            f"{client_name} - 4. OTIMIZACOES",
            f"{client_name} - 4. OTIMIZAÇÕES",
        ),
        "saldo_board_id": (
            f"{client_name}- 5. SALDO",
            f"{client_name} - 5. SALDO",
        ),
    }


def _config_token_index(parts):
    for index, token in enumerate(parts):
        if "." in token:
            return index
    return -1


def _monday_token() -> str:
    return os.getenv("MONDAY_API_TOKEN", "").strip()


def _env_value(name: str) -> str:
    return os.getenv(name, "").strip()


def _is_set(name: str) -> bool:
    return bool(_env_value(name))


def _infra_status_text() -> str:
    checks = [
        ("ALPHA_OS_MODE", _env_value("ALPHA_OS_MODE").lower() in ("1", "true", "yes", "on")),
        ("WHATSAPP_TOKEN", _is_set("WHATSAPP_TOKEN")),
        ("WHATSAPP_PHONE_NUMBER_ID", _is_set("WHATSAPP_PHONE_NUMBER_ID") or _is_set("PHONE_NUMBER_ID")),
        ("WHATSAPP_VERIFY_TOKEN", _is_set("WHATSAPP_VERIFY_TOKEN")),
        ("GOOGLE_SHEETS_SPREADSHEET_ID", _is_set("GOOGLE_SHEETS_SPREADSHEET_ID")),
        ("GOOGLE_CREDENTIALS_JSON", _is_set("GOOGLE_CREDENTIALS_JSON") or _is_set("GOOGLE_SERVICE_ACCOUNT_JSON")),
        ("GEMINI_API_KEY ou OPENAI_API_KEY", _is_set("GEMINI_API_KEY") or _is_set("OPENAI_API_KEY")),
        ("MONDAY_API_TOKEN", _is_set("MONDAY_API_TOKEN")),
        ("N8N_ONBOARDING_WEBHOOK_URL", _is_set("N8N_ONBOARDING_WEBHOOK_URL")),
        ("N8N_PHASE2_WEBHOOK_URL", _is_set("N8N_PHASE2_WEBHOOK_URL")),
        ("N8N_GOOGLE_PUBLISH_WEBHOOK_URL", _is_set("N8N_GOOGLE_PUBLISH_WEBHOOK_URL")),
        ("N8N_META_PUBLISH_WEBHOOK_URL", _is_set("N8N_META_PUBLISH_WEBHOOK_URL")),
        ("N8N_DAILY_ANALYSIS_WEBHOOK_URL", _is_set("N8N_DAILY_ANALYSIS_WEBHOOK_URL")),
        ("N8N_WEEKLY_ANALYSIS_WEBHOOK_URL", _is_set("N8N_WEEKLY_ANALYSIS_WEBHOOK_URL")),
        ("GOOGLE_ADS_DEVELOPER_TOKEN", _is_set("GOOGLE_ADS_DEVELOPER_TOKEN")),
        (
            "GOOGLE_ADS auth",
            _is_set("GOOGLE_ADS_CREDENTIALS_JSON")
            or _is_set("GOOGLE_ADS_CREDENTIALS_PATH")
            or (_is_set("GOOGLE_ADS_CLIENT_ID") and _is_set("GOOGLE_ADS_CLIENT_SECRET") and _is_set("GOOGLE_ADS_REFRESH_TOKEN")),
        ),
        ("META_ACCESS_TOKEN", _is_set("META_ACCESS_TOKEN")),
    ]

    lines = ["Alpha OS - Infra atual", ""]
    for name, ok in checks:
        lines.append(f"- {name}: {'OK' if ok else 'MISSING'}")

    lines.extend(
        [
            "",
            "Fora do Render, ainda precisa existir:",
            "- n8n fluxo 01 ativo e com Form URL",
            "- n8n fluxo 02 ativo em /webhook/status_monday",
            "- se usar publicacao direta: Google Ads e Meta com acesso valido no proprio Render",
            "- se usar n8n para publicar: fluxo Google ativo e fluxo Meta ativo",
            "- credenciais do Monday, Google Docs, Gemini, Google Ads e Meta nos lugares certos",
        ]
    )
    return "\n".join(lines)


def _monday_graphql(query: str, variables: Optional[Dict] = None) -> Dict:
    token = _monday_token()
    if not token:
        raise RuntimeError("Missing MONDAY_API_TOKEN")
    url = os.getenv("MONDAY_API_URL", "https://api.monday.com/v2").strip() or "https://api.monday.com/v2"
    headers = {"Authorization": token, "Content-Type": "application/json"}
    body = {"query": query}
    if variables is not None:
        body["variables"] = variables
    resp = requests.post(url, headers=headers, json=body, timeout=30)
    resp.raise_for_status()
    payload = resp.json()
    if payload.get("errors"):
        raise RuntimeError(str(payload["errors"])[:300])
    return payload.get("data") or {}


def _discover_monday_artifacts(client_name: str) -> Dict[str, str]:
    """
    Descobre os boards do cliente pelo padrão de nomenclatura do seu workflow 01.
    Retorna um dict com IDs (strings).
    """
    expected = {
        "briefing_board_id": f"{client_name}- 1. BRIEFING",
        "lp_board_id": f"{client_name}- 2. CRIAÇÃO DE LP",
        "campanhas_board_id": f"{client_name}- 3. CAMPANHAS",
        "otimizacoes_board_id": f"{client_name}- 4. OTIMIZAÇÕES",
        "saldo_board_id": f"{client_name}- 5. SALDO",
    }

    data = _monday_graphql("query { boards(limit: 500) { id name } }")
    boards = data.get("boards") or []

    found: Dict[str, str] = {}
    name_to_id = {_norm_cmp(b.get("name", "")): str(b.get("id")) for b in boards}

    for key, name in expected.items():
        board_id = name_to_id.get(_norm_cmp(name))
        if board_id:
            found[key] = board_id

    return found


def _discover_briefing_item_id(briefing_board_id: str) -> Optional[str]:
    if not briefing_board_id:
        return None
    q = (
        "query { "
        f"boards (ids: [{briefing_board_id}]) {{ "
        'items_page (query_params: {rules: [{column_id: "name", compare_value: ["CRIAR RESUMO DO CLIENTE"], operator: any_of}]}) { '
        "items { id name } "
        "} "
        "} "
        "}"
    )
    data = _monday_graphql(q)
    boards = data.get("boards") or []
    if not boards:
        return None
    items_page = boards[0].get("items_page") or {}
    items = items_page.get("items") or []
    if not items:
        return None
    return str(items[0].get("id") or "").strip() or None


def _discover_item_id_by_name(board_id: str, item_name: str) -> Optional[str]:
    if not board_id or not item_name:
        return None
    # Use monday server-side filtering first (fast).
    q = (
        "query { "
        f"boards (ids: [{board_id}]) {{ "
        f'items_page (query_params: {{rules: [{{column_id: "name", compare_value: ["{item_name}"], operator: any_of}}]}}) {{ '
        "items { id name } "
        "} "
        "} "
        "}"
    )
    data = _monday_graphql(q)
    boards = data.get("boards") or []
    if not boards:
        return None
    items_page = boards[0].get("items_page") or {}
    items = items_page.get("items") or []
    if not items:
        return None
    return str(items[0].get("id") or "").strip() or None


def _discover_monday_artifacts(client_name: str) -> Dict[str, str]:
    expected = _candidate_board_names(client_name)

    data = _monday_graphql("query { boards(limit: 500) { id name } }")
    boards = data.get("boards") or []

    found: Dict[str, str] = {}
    name_to_id = {_norm_cmp(board.get("name", "")): str(board.get("id")) for board in boards}

    for key, names in expected.items():
        for name in names:
            board_id = name_to_id.get(_norm_cmp(name))
            if board_id:
                found[key] = board_id
                break

    if len(found) < len(expected):
        normalized_client = _norm_cmp(client_name)
        suffixes = {
            "briefing_board_id": ("1. briefing",),
            "lp_board_id": ("2. criacao de lp", "2. criação de lp"),
            "campanhas_board_id": ("3. campanhas",),
            "otimizacoes_board_id": ("4. otimizacoes", "4. otimizações"),
            "saldo_board_id": ("5. saldo",),
        }
        for board in boards:
            board_name_norm = _norm_cmp(board.get("name", ""))
            for key, key_suffixes in suffixes.items():
                if key in found:
                    continue
                if normalized_client in board_name_norm and any(board_name_norm.endswith(suffix) for suffix in key_suffixes):
                    found[key] = str(board.get("id"))
                    break

    return found


def _discover_item_id_by_name(board_id: str, item_name: str) -> Optional[str]:
    if not board_id or not item_name:
        return None

    q = (
        "query { "
        f"boards (ids: [{board_id}]) {{ "
        f'items_page (query_params: {{rules: [{{column_id: "name", compare_value: ["{item_name}"], operator: any_of}}]}}) {{ '
        "items { id name } "
        "} "
        "} "
        "}"
    )
    data = _monday_graphql(q)
    boards = data.get("boards") or []
    if boards:
        items_page = boards[0].get("items_page") or {}
        items = items_page.get("items") or []
        if items:
            return str(items[0].get("id") or "").strip() or None

    q = (
        "query { "
        f"boards (ids: [{board_id}]) {{ "
        "items_page(limit: 200) { "
        "items { id name } "
        "} "
        "} "
        "}"
    )
    data = _monday_graphql(q)
    boards = data.get("boards") or []
    if not boards:
        return None
    items_page = boards[0].get("items_page") or {}
    items = items_page.get("items") or []
    target = _norm_cmp(item_name)
    for item in items:
        if _norm_cmp(item.get("name", "")) == target:
            return str(item.get("id") or "").strip() or None
    return None


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

        if t in ("config", "infra", "setup"):
            return _infra_status_text()

        if t.startswith("novo cliente") or t.startswith("novo_cliente"):
            name, briefing = _parse_new_client(raw)
            if not name or not briefing:
                return "Envie assim:\n\nnovo cliente Nome do Cliente\nBriefing completo aqui..."
            client = self.store.create_client(name=name, briefing=briefing)
            self.store.set_last_client_for_phone(phone, client["id"])
            return f"Operacao criada para {client['name']}.\nID: {client['id']}\nProximo: rodar {client['id']} monday"

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

        if t.startswith("o que falta") or t.startswith("prontidao"):
            term = raw.split(" ", 3)[-1].strip() if " " in raw else ""
            if t.startswith("o que falta"):
                term = raw[len("o que falta") :].strip()
            elif t.startswith("prontidao"):
                term = raw[len("prontidao") :].strip()
            client = self._resolve_client(phone, term)
            if not client:
                return "Nao encontrei esse cliente. Use 'clientes' para listar."
            return readiness_text(client)

        if t.startswith("definir ") or t.startswith("configurar "):
            command_name = "definir" if t.startswith("definir ") else "configurar"
            body = raw[len(command_name) :].strip()
            parts = body.split()
            field_index = _config_token_index(parts)
            if len(parts) < 3 or field_index <= 0 or field_index == len(parts) - 1:
                return (
                    "Uso: definir <cliente> <campo> <valor>\n"
                    "Exemplos:\n"
                    "definir clinica common.landing_page_url https://site.com\n"
                    "definir clinica google.customer_id 1234567890\n"
                    "definir clinica meta.ad_account_id 377601641828660\n"
                    "definir clinica common.country United States"
                )
            field_path = parts[field_index].strip()
            value = " ".join(parts[field_index + 1 :]).strip().strip('"').strip("'")
            term = " ".join(parts[:field_index]).strip()
            client = self._resolve_client(phone, term)
            if not client:
                return "Nao encontrei esse cliente. Use 'clientes' para listar."
            updated = self.store.update_client_config(client["id"], field_path, value)
            return f"Configuracao salva para {updated['name']}.\n{field_path} = {value}"

        if t.startswith("preparar "):
            parts = raw.split()
            if len(parts) < 3:
                return "Uso: preparar <google|meta> <cliente>"
            platform = _norm(parts[1])
            term = " ".join(parts[2:]).strip()
            client = self._resolve_client(phone, term)
            if not client:
                return "Nao encontrei esse cliente. Use 'clientes' para listar."
            try:
                if platform == "google":
                    client = prepare_google_payload(client)
                    _mark_stage(client, "googlePublish", "ready", "Payload Google preparado e pronto para publicar.")
                    self.store.upsert_client(client)
                    return f"Payload Google preparado para {client['name']} e guardado em artifacts.googleAdsJson."
                if platform == "meta":
                    client = prepare_meta_payload(client)
                    _mark_stage(client, "metaPublish", "ready", "Payload Meta preparado e pronto para publicar.")
                    self.store.upsert_client(client)
                    return f"Payload Meta preparado para {client['name']} e guardado em artifacts.metaAdsJson."
                return "Plataforma invalida. Use preparar google <cliente> ou preparar meta <cliente>."
            except Exception as exc:
                return f"Erro ao preparar payload: {exc}"

        if t.startswith("publicar ") or t.startswith("publica ") or t.startswith("publique "):
            words = raw.split()
            if len(words) < 3:
                return "Uso: publicar <google|meta> <cliente>"
            platform = _norm(words[1])
            term = " ".join(words[2:]).strip()
            client = self._resolve_client(phone, term)
            if not client:
                return "Nao encontrei esse cliente. Use 'clientes' para listar."
            try:
                if platform == "google":
                    client = publish_google(client)
                    _mark_stage(client, "googlePublish", "done", "Campanhas Google Ads publicadas em modo pausado.")
                    self.store.upsert_client(client)
                    return f"Google Ads publicado para {client['name']} em modo pausado."
                if platform == "meta":
                    client = publish_meta(client)
                    _mark_stage(client, "metaPublish", "done", "Campanhas Meta Ads publicadas em modo pausado.")
                    self.store.upsert_client(client)
                    return f"Meta Ads publicado para {client['name']} em modo pausado."
                return "Plataforma invalida. Use publicar google <cliente> ou publicar meta <cliente>."
            except Exception as exc:
                return f"Erro ao publicar: {exc}"

        if t.startswith("analisar ") or t.startswith("analisa ") or t.startswith("analise "):
            parts = raw.split()
            if len(parts) < 4:
                return "Uso: analisar <google|meta> <cliente> <diaria|semanal|mensal|trimestral|semestral|anual>"
            platform = _norm(parts[1])
            period = _norm(parts[-1])
            term = " ".join(parts[2:-1]).strip()
            client = self._resolve_client(phone, term)
            if not client:
                return "Nao encontrei esse cliente. Use 'clientes' para listar."
            try:
                if platform == "google":
                    client = analyze_google(client, period)
                    _mark_stage(
                        client,
                        "dailyAnalysis" if period in ("diaria", "diario", "hoje", "1d") else "weeklyAnalysis",
                        "done",
                        f"Analise Google {period} concluida.",
                    )
                    self.store.upsert_client(client)
                    summary = (((client.get("artifacts") or {}).get("analysis") or {}).get("google") or {}).get(period, {}).get("summary", "")
                    return summary or "Analise Google concluida."
                if platform == "meta":
                    client = analyze_meta(client, period)
                    _mark_stage(
                        client,
                        "dailyAnalysis" if period in ("diaria", "diario", "hoje", "1d") else "weeklyAnalysis",
                        "done",
                        f"Analise Meta {period} concluida.",
                    )
                    self.store.upsert_client(client)
                    summary = (((client.get("artifacts") or {}).get("analysis") or {}).get("meta") or {}).get(period, {}).get("summary", "")
                    return summary or "Analise Meta concluida."
                return "Plataforma invalida. Use analisar google <cliente> mensal ou analisar meta <cliente> mensal."
            except Exception as exc:
                return f"Erro ao analisar: {exc}"

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

        if t.startswith("validar"):
            term = raw.split(" ", 1)[1].strip() if " " in raw else ""
            client = self._resolve_client(phone, term)
            if not client:
                return "Nao encontrei esse cliente. Use 'clientes' para listar."
            return self._validate_client(client)

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

        ok = False
        message = ""

        if stage_key == "onboarding":
            # Seu fluxo 01 hoje e um Form Trigger do n8n (URL /form/<id>).
            if "/form/" in url:
                ok, message = _call_n8n_form(url, client.get("name") or "", client.get("briefing") or "")
            else:
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

        elif stage_key == "phase2":
            # Para disparar o workflow 02 (status_monday) precisamos do pulseId do item
            # "CRIAR RESUMO DO CLIENTE" no board de briefing.
            artifacts = client.setdefault("artifacts", {})
            monday = artifacts.setdefault("monday", {})

            if not _monday_token():
                stage["status"] = "needs_config"
                stage["message"] = "Falta configurar MONDAY_API_TOKEN (para achar o pulseId no Monday)."
                self.store.upsert_client(client)
                return _format_status(client)

            try:
                if not monday.get("briefing_board_id"):
                    monday.update(_discover_monday_artifacts(client.get("name") or ""))
                if not monday.get("briefing_item_id") and monday.get("briefing_board_id"):
                    monday["briefing_item_id"] = _discover_briefing_item_id(monday.get("briefing_board_id")) or ""
            except Exception as exc:
                stage["status"] = "error"
                stage["message"] = f"Erro ao validar Monday: {exc}"
                self.store.upsert_client(client)
                return _format_status(client)

            briefing_item_id = str(monday.get("briefing_item_id") or "").strip()
            if not briefing_item_id:
                stage["status"] = "blocked"
                stage["message"] = (
                    "Nao achei o item 'CRIAR RESUMO DO CLIENTE' no Monday ainda. "
                    "Rode 'rodar <id> monday' e aguarde finalizar."
                )
                self.store.upsert_client(client)
                return _format_status(client)

            event_payload = {"event": {"type": "update_column_value", "pulseId": int(briefing_item_id)}}
            ok, message = _call_webhook(url, event_payload)

        elif stage_key == "googlePublish":
            artifacts = client.setdefault("artifacts", {})
            monday = artifacts.setdefault("monday", {})

            if not _monday_token():
                stage["status"] = "needs_config"
                stage["message"] = "Falta configurar MONDAY_API_TOKEN (para achar o pulseId no Monday)."
                self.store.upsert_client(client)
                return _format_status(client)

            try:
                if not monday.get("campanhas_board_id"):
                    monday.update(_discover_monday_artifacts(client.get("name") or ""))
                if not monday.get("google_item_id") and monday.get("campanhas_board_id"):
                    monday["google_item_id"] = (
                        _discover_item_id_by_name(monday.get("campanhas_board_id"), "Criação de Campanha Google ADS")
                        or ""
                    )
            except Exception as exc:
                stage["status"] = "error"
                stage["message"] = f"Erro ao validar Monday: {exc}"
                self.store.upsert_client(client)
                return _format_status(client)

            item_id = str(monday.get("google_item_id") or "").strip()
            if not item_id:
                stage["status"] = "blocked"
                stage["message"] = "Nao achei a tarefa 'Criação de Campanha Google ADS' no quadro de CAMPANHAS."
                self.store.upsert_client(client)
                return _format_status(client)

            event_payload = {"event": {"type": "update_column_value", "pulseId": int(item_id)}}
            ok, message = _call_webhook(url, event_payload)

        elif stage_key == "metaPublish":
            artifacts = client.setdefault("artifacts", {})
            monday = artifacts.setdefault("monday", {})

            if not _monday_token():
                stage["status"] = "needs_config"
                stage["message"] = "Falta configurar MONDAY_API_TOKEN (para achar o pulseId no Monday)."
                self.store.upsert_client(client)
                return _format_status(client)

            try:
                if not monday.get("campanhas_board_id"):
                    monday.update(_discover_monday_artifacts(client.get("name") or ""))
                if not monday.get("meta_item_id") and monday.get("campanhas_board_id"):
                    monday["meta_item_id"] = (
                        _discover_item_id_by_name(monday.get("campanhas_board_id"), "Criação de Campanha Meta ADS")
                        or ""
                    )
            except Exception as exc:
                stage["status"] = "error"
                stage["message"] = f"Erro ao validar Monday: {exc}"
                self.store.upsert_client(client)
                return _format_status(client)

            item_id = str(monday.get("meta_item_id") or "").strip()
            if not item_id:
                stage["status"] = "blocked"
                stage["message"] = "Nao achei a tarefa 'Criação de Campanha Meta ADS' no quadro de CAMPANHAS."
                self.store.upsert_client(client)
                return _format_status(client)

            event_payload = {"event": {"type": "update_column_value", "pulseId": int(item_id)}}
            ok, message = _call_webhook(url, event_payload)

        else:
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

    def _validate_client(self, client: Dict) -> str:
        artifacts = client.setdefault("artifacts", {})
        monday = artifacts.setdefault("monday", {})

        if not _monday_token():
            return "Falta configurar MONDAY_API_TOKEN no Render para eu conseguir validar boards/itens."

        try:
            if not monday.get("briefing_board_id"):
                monday.update(_discover_monday_artifacts(client.get("name") or ""))
            if monday.get("briefing_board_id") and not monday.get("briefing_item_id"):
                monday["briefing_item_id"] = _discover_briefing_item_id(monday.get("briefing_board_id")) or ""
            if monday.get("campanhas_board_id") and not monday.get("google_item_id"):
                monday["google_item_id"] = (
                    _discover_item_id_by_name(monday.get("campanhas_board_id"), "Criação de Campanha Google ADS")
                    or _discover_item_id_by_name(monday.get("campanhas_board_id"), "Criacao de Campanha Google ADS")
                    or ""
                )
            if monday.get("campanhas_board_id") and not monday.get("meta_item_id"):
                monday["meta_item_id"] = (
                    _discover_item_id_by_name(monday.get("campanhas_board_id"), "Criação de Campanha Meta ADS")
                    or _discover_item_id_by_name(monday.get("campanhas_board_id"), "Criacao de Campanha Meta ADS")
                    or ""
                )
            self.store.upsert_client(client)
        except Exception as exc:
            return f"Erro ao validar Monday: {exc}"

        lines = [
            f"Cliente: {client.get('name')}",
            f"ID: {client.get('id')}",
            "",
            "Monday:",
            f"- briefing_board_id: {monday.get('briefing_board_id') or 'NA'}",
            f"- briefing_item_id (pulseId): {monday.get('briefing_item_id') or 'NA'}",
            f"- lp_board_id: {monday.get('lp_board_id') or 'NA'}",
            f"- campanhas_board_id: {monday.get('campanhas_board_id') or 'NA'}",
            f"- google_item_id (pulseId): {monday.get('google_item_id') or 'NA'}",
            f"- meta_item_id (pulseId): {monday.get('meta_item_id') or 'NA'}",
        ]
        return "\n".join(lines)

import json
import os
from datetime import date, timedelta
from typing import Any, Dict, Tuple

import requests

from .llm import complete_json, complete_text


def graph_version() -> str:
    return os.getenv("META_GRAPH_VERSION", "v25.0").strip() or "v25.0"


def access_token() -> str:
    token = os.getenv("META_ACCESS_TOKEN", "").strip() or os.getenv("WHATSAPP_TOKEN", "").strip()
    if not token:
        raise RuntimeError("Missing META_ACCESS_TOKEN")
    return token


def _graph_encode(payload: Dict[str, Any]) -> Dict[str, Any]:
    encoded: Dict[str, Any] = {}
    for key, value in (payload or {}).items():
        if value is None:
            continue
        if isinstance(value, (dict, list)):
            encoded[key] = json.dumps(value, ensure_ascii=False)
        else:
            encoded[key] = value
    return encoded


def graph_post(path: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    response = requests.post(
        f"https://graph.facebook.com/{graph_version()}/{path}",
        data=_graph_encode(payload),
        timeout=60,
    )
    if response.status_code >= 400:
        raise RuntimeError(response.text)
    return response.json()


def graph_get(path: str, params: Dict[str, Any]) -> Dict[str, Any]:
    response = requests.get(
        f"https://graph.facebook.com/{graph_version()}/{path}",
        params=_graph_encode(params),
        timeout=60,
    )
    if response.status_code >= 400:
        raise RuntimeError(response.text)
    return response.json()


def extract_payload_from_text(source_text: str) -> Dict[str, Any]:
    prompt = f"""
Voce e um extrator de dados JSON estrito. Sua unica funcao e ler o texto estruturado da Campanha Meta Ads e extrair os dados do PRIMEIRO conjunto e do PRIMEIRO anuncio, formatando tudo em um UNICO objeto JSON valido.

REGRAS CRITICAS:
1. Retorne APENAS o JSON. Zero texto antes ou depois. Nao use crases. Apenas o objeto puro.
2. O orcamento ('daily_budget') deve ser um NUMERO INTEIRO em centavos (ex: R$ 50,00 vira 5000).
3. Siga EXATAMENTE esta estrutura de chaves:

{{
  "campaign_name": "Nome da Campanha",
  "adset_name": "Nome do Conjunto",
  "daily_budget": 5000,
  "ad_name": "Nome do Anuncio",
  "primary_text": "Texto principal do anuncio",
  "headline": "Titulo curto do anuncio"
}}

TEXTO DA CAMPANHA:
{source_text}
"""
    return complete_json(prompt)


def publish_structure(payload_json: Any, client_config: Dict[str, Any]) -> Dict[str, Any]:
    payload = json.loads(payload_json) if isinstance(payload_json, str) else payload_json
    meta = (client_config or {}).get("meta", {})
    common = (client_config or {}).get("common", {})

    ad_account_id = str(meta.get("ad_account_id") or "").replace("act_", "").strip()
    page_id = str(meta.get("page_id") or "").strip()
    landing_page_url = str(common.get("landing_page_url") or "").strip()
    objective = str(meta.get("objective") or "OUTCOME_TRAFFIC").strip()
    cta_type = str(meta.get("cta_type") or "LEARN_MORE").strip()
    instagram_actor_id = str(meta.get("instagram_actor_id") or "").strip()

    if not ad_account_id:
        raise RuntimeError("Falta meta.ad_account_id na configuracao do cliente.")
    if not page_id:
        raise RuntimeError("Falta meta.page_id na configuracao do cliente.")
    if not landing_page_url:
        raise RuntimeError("Falta common.landing_page_url na configuracao do cliente.")

    campaign = graph_post(
        f"act_{ad_account_id}/campaigns",
        {
            "name": payload["campaign_name"],
            "objective": objective,
            "status": "PAUSED",
            "special_ad_categories": ["NONE"],
            "access_token": access_token(),
        },
    )

    adset = graph_post(
        f"act_{ad_account_id}/adsets",
        {
            "name": payload["adset_name"],
            "campaign_id": campaign["id"],
            "daily_budget": int(payload["daily_budget"]),
            "billing_event": "IMPRESSIONS",
            "optimization_goal": "LINK_CLICKS",
            "bid_strategy": "LOWEST_COST_WITHOUT_CAP",
            "targeting": {"geo_locations": {"countries": ["BR"]}},
            "status": "PAUSED",
            "access_token": access_token(),
        },
    )

    creative = graph_post(
        f"act_{ad_account_id}/adcreatives",
        {
            "name": f"{payload['ad_name']} - Criativo",
            "object_story_spec": {
                "page_id": page_id,
                **({"instagram_actor_id": instagram_actor_id} if instagram_actor_id else {}),
                "link_data": {
                    "message": payload["primary_text"],
                    "link": landing_page_url,
                    "name": payload["headline"],
                    "call_to_action": {"type": cta_type},
                },
            },
            "access_token": access_token(),
        },
    )

    ad = graph_post(
        f"act_{ad_account_id}/ads",
        {
            "name": payload["ad_name"],
            "adset_id": adset["id"],
            "creative": {"creative_id": creative["id"]},
            "status": "PAUSED",
            "access_token": access_token(),
        },
    )

    return {
        "campaign": campaign,
        "adset": adset,
        "creative": creative,
        "ad": ad,
    }


def _resolve_period(period: str) -> Tuple[str, str]:
    period = str(period or "30d").strip().lower()
    today = date.today()
    if period in ("diaria", "diario", "hoje", "1d"):
        start = today
    elif period in ("semanal", "7d"):
        start = today - timedelta(days=7)
    elif period in ("mensal", "30d"):
        start = today - timedelta(days=30)
    elif period in ("trimestral", "90d"):
        start = today - timedelta(days=90)
    elif period in ("semestral", "180d"):
        start = today - timedelta(days=180)
    elif period in ("anual", "365d"):
        start = today - timedelta(days=365)
    else:
        raise ValueError("Periodo invalido. Use diaria, semanal, mensal, trimestral, semestral ou anual.")
    return start.isoformat(), today.isoformat()


def fetch_account_insights(ad_account_id: str, period: str) -> Dict[str, Any]:
    ad_account_id = str(ad_account_id or "").replace("act_", "").strip()
    if not ad_account_id:
        raise RuntimeError("ad_account_id vazio")

    start, end = _resolve_period(period)
    response = graph_get(
        f"act_{ad_account_id}/insights",
        {
            "level": "campaign",
            "fields": "campaign_id,campaign_name,impressions,clicks,spend,ctr,cpc,actions,reach",
            "time_range": json.dumps({"since": start, "until": end}),
            "limit": 200,
            "access_token": access_token(),
        },
    )
    return {"period": period, "start": start, "end": end, "data": response.get("data", []), "raw": response}


def summarize_metrics(metrics: Dict[str, Any], client_name: str, period: str) -> str:
    prompt = f"""
Analise estes dados reais de trafego da Meta Ads e me de um relatorio executivo curto em portugues.

Cliente: {client_name}
Periodo: {period}
Dados:
{json.dumps(metrics.get("data", []), ensure_ascii=False)}

Quero:
- veredito geral
- criativos ou campanhas que merecem atencao
- gargalos claros
- 3 proximas acoes objetivas

Fale como diretor de trafego senior. Seja direto.
"""
    return complete_text(prompt)

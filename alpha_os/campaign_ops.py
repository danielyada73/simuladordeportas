import json
from typing import Any, Dict, List

from .google_ads_ops import (
    extract_payload_from_text as extract_google_payload,
    fetch_campaign_metrics as fetch_google_metrics,
    publish_search_structure,
    summarize_metrics as summarize_google_metrics,
)
from .meta_ops import (
    extract_payload_from_text as extract_meta_payload,
    fetch_account_insights,
    publish_structure as publish_meta_structure,
    summarize_metrics as summarize_meta_metrics,
)
from .monday_client import latest_update_text


def required_fields(client: Dict[str, Any], platform: str) -> List[str]:
    config = client.get("config") or {}
    common = config.get("common") or {}
    google = config.get("google") or {}
    meta = config.get("meta") or {}

    base_missing = []
    if not common.get("landing_page_url"):
        base_missing.append("common.landing_page_url")

    if platform == "google":
        missing = list(base_missing)
        if not google.get("manager_customer_id") and not google.get("customer_id"):
            missing.append("google.customer_id ou google.manager_customer_id")
        if not common.get("country"):
            missing.append("common.country")
        if not common.get("language"):
            missing.append("common.language")
        if not common.get("timezone"):
            missing.append("common.timezone")
        if not common.get("currency_code"):
            missing.append("common.currency_code")
        return missing

    if platform == "meta":
        missing = list(base_missing)
        if not meta.get("ad_account_id"):
            missing.append("meta.ad_account_id")
        if not meta.get("page_id"):
            missing.append("meta.page_id")
        return missing

    return base_missing


def readiness_text(client: Dict[str, Any]) -> str:
    google_missing = required_fields(client, "google")
    meta_missing = required_fields(client, "meta")
    lines = [
        f"Cliente: {client.get('name')}",
        "",
        "Google Ads:",
        f"- {'pronto' if not google_missing else 'faltando'}",
    ]
    lines.extend([f"- {item}" for item in google_missing])
    lines.extend(
        [
            "",
            "Meta Ads:",
            f"- {'pronto' if not meta_missing else 'faltando'}",
        ]
    )
    lines.extend([f"- {item}" for item in meta_missing])
    return "\n".join(lines)


def _google_item_id(client: Dict[str, Any]) -> str:
    monday = ((client.get("artifacts") or {}).get("monday") or {})
    return str(monday.get("google_item_id") or "").strip()


def _meta_item_id(client: Dict[str, Any]) -> str:
    monday = ((client.get("artifacts") or {}).get("monday") or {})
    return str(monday.get("meta_item_id") or "").strip()


def prepare_google_payload(client: Dict[str, Any]) -> Dict[str, Any]:
    item_id = _google_item_id(client)
    if not item_id:
        raise RuntimeError("Falta google_item_id no Monday. Rode 'validar <cliente>' primeiro.")

    source_text = latest_update_text(item_id)
    payload = extract_google_payload(source_text, client.get("name", ""))

    common = ((client.get("config") or {}).get("common") or {})
    google = ((client.get("config") or {}).get("google") or {})
    payload.setdefault("cliente", {})
    payload["cliente"]["nome"] = payload["cliente"].get("nome") or client.get("name", "")
    payload["cliente"]["customer_id"] = payload["cliente"].get("customer_id") or str(google.get("customer_id") or "")
    payload["cliente"]["landing_page_url"] = payload["cliente"].get("landing_page_url") or str(common.get("landing_page_url") or "")
    payload.setdefault("campanhas", [])

    config_conta = payload["cliente"].setdefault("configuracao_conta", {})
    config_conta["descriptive_name"] = config_conta.get("descriptive_name") or client.get("name", "")
    config_conta["currency_code"] = config_conta.get("currency_code") or str(common.get("currency_code") or "BRL")
    config_conta["time_zone"] = config_conta.get("time_zone") or str(common.get("timezone") or "America/Sao_Paulo")
    config_conta["pais_faturamento"] = config_conta.get("pais_faturamento") or str(common.get("country") or "Brazil")

    conversion = payload["cliente"].setdefault("conversion_action", {})
    conversion["nome"] = conversion.get("nome") or str(google.get("conversion_action_name") or f"Lead - {client.get('name', '')}")
    conversion["category"] = conversion.get("category") or str(google.get("conversion_category") or "SUBMIT_LEAD_FORM")
    conversion["valor_padrao_reais"] = conversion.get("valor_padrao_reais") or 0

    for campaign in payload["campanhas"]:
        campaign["idioma"] = campaign.get("idioma") or str(common.get("language") or "Portuguese")
        campaign["geo_targets"] = campaign.get("geo_targets") or [str(common.get("country") or "Brazil")]

    artifacts = client.setdefault("artifacts", {})
    artifacts["googleSourceText"] = source_text
    artifacts["googleAdsJson"] = json.dumps(payload, ensure_ascii=False, indent=2)
    return client


def prepare_meta_payload(client: Dict[str, Any]) -> Dict[str, Any]:
    item_id = _meta_item_id(client)
    if not item_id:
        raise RuntimeError("Falta meta_item_id no Monday. Rode 'validar <cliente>' primeiro.")

    source_text = latest_update_text(item_id)
    payload = extract_meta_payload(source_text)
    artifacts = client.setdefault("artifacts", {})
    artifacts["metaSourceText"] = source_text
    artifacts["metaAdsJson"] = json.dumps(payload, ensure_ascii=False, indent=2)
    return client


def publish_google(client: Dict[str, Any], validate_only: bool = False) -> Dict[str, Any]:
    missing = required_fields(client, "google")
    if missing:
        raise RuntimeError("Faltam campos para Google Ads: " + ", ".join(missing))
    artifacts = client.setdefault("artifacts", {})
    if not artifacts.get("googleAdsJson"):
        prepare_google_payload(client)
    google = ((client.get("config") or {}).get("google") or {})
    result = publish_search_structure(
        artifacts["googleAdsJson"],
        manager_customer_id=str(google.get("manager_customer_id") or ""),
        validate_only=validate_only,
    )
    artifacts.setdefault("publish", {})["google"] = result
    return client


def publish_meta(client: Dict[str, Any]) -> Dict[str, Any]:
    missing = required_fields(client, "meta")
    if missing:
        raise RuntimeError("Faltam campos para Meta Ads: " + ", ".join(missing))
    artifacts = client.setdefault("artifacts", {})
    if not artifacts.get("metaAdsJson"):
        prepare_meta_payload(client)
    result = publish_meta_structure(artifacts["metaAdsJson"], client.get("config") or {})
    artifacts.setdefault("publish", {})["meta"] = result
    return client


def analyze_google(client: Dict[str, Any], period: str) -> Dict[str, Any]:
    google = ((client.get("config") or {}).get("google") or {})
    customer_id = str(google.get("customer_id") or "").strip()
    if not customer_id:
        raise RuntimeError("Falta google.customer_id na configuracao do cliente.")
    metrics = fetch_google_metrics(customer_id, period)
    summary = summarize_google_metrics(metrics, client.get("name", ""), period)
    artifacts = client.setdefault("artifacts", {})
    analysis = artifacts.setdefault("analysis", {}).setdefault("google", {})
    analysis[period] = {"metrics": metrics, "summary": summary}
    return client


def analyze_meta(client: Dict[str, Any], period: str) -> Dict[str, Any]:
    meta = ((client.get("config") or {}).get("meta") or {})
    ad_account_id = str(meta.get("ad_account_id") or "").strip()
    if not ad_account_id:
        raise RuntimeError("Falta meta.ad_account_id na configuracao do cliente.")
    metrics = fetch_account_insights(ad_account_id, period)
    summary = summarize_meta_metrics(metrics, client.get("name", ""), period)
    artifacts = client.setdefault("artifacts", {})
    analysis = artifacts.setdefault("analysis", {}).setdefault("meta", {})
    analysis[period] = {"metrics": metrics, "summary": summary}
    return client

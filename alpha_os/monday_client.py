import os
from typing import Any, Dict, Optional

import requests


def monday_token() -> str:
    return os.getenv("MONDAY_API_TOKEN", "").strip()


def monday_url() -> str:
    return os.getenv("MONDAY_API_URL", "https://api.monday.com/v2").strip() or "https://api.monday.com/v2"


def ensure_monday_configured():
    if not monday_token():
        raise RuntimeError("Missing MONDAY_API_TOKEN")


def graphql(query: str, variables: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    ensure_monday_configured()
    headers = {"Authorization": monday_token(), "Content-Type": "application/json"}
    payload: Dict[str, Any] = {"query": query}
    if variables is not None:
        payload["variables"] = variables
    response = requests.post(monday_url(), headers=headers, json=payload, timeout=30)
    response.raise_for_status()
    data = response.json()
    if data.get("errors"):
        raise RuntimeError(str(data["errors"])[:300])
    return data.get("data") or {}


def latest_update_text(item_id: str) -> str:
    item_id = str(item_id or "").strip()
    if not item_id:
        raise ValueError("item_id vazio")
    data = graphql(
        f"""
        query {{
          items(ids: [{item_id}]) {{
            name
            updates(limit: 1) {{
              text_body
              body
            }}
          }}
        }}
        """
    )
    items = data.get("items") or []
    if not items:
        raise RuntimeError("Item nao encontrado no Monday.")
    updates = items[0].get("updates") or []
    if not updates:
        raise RuntimeError("Item sem updates no Monday.")
    update = updates[0]
    return str(update.get("text_body") or update.get("body") or "").strip()

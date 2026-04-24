import os
import re
import unicodedata
from typing import Any, Dict, List, Optional

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


def _strip_accents(text: str) -> str:
    return "".join(char for char in unicodedata.normalize("NFKD", text or "") if not unicodedata.combining(char))


def _norm(text: str) -> str:
    value = _strip_accents(text or "").lower().strip()
    value = re.sub(r"\s*-\s*", "-", value)
    value = re.sub(r"\s+", " ", value)
    return value


def list_boards(limit: int = 500) -> List[Dict[str, str]]:
    data = graphql(f"query {{ boards(limit: {int(limit)}) {{ id name }} }}")
    boards = data.get("boards") or []
    return [{"id": str(board.get("id") or ""), "name": str(board.get("name") or "")} for board in boards]


def _extract_client_name(board_name: str) -> Optional[str]:
    name = str(board_name or "").strip()
    match = re.match(r"^(.*?)\s*-\s*[1-5]\.", name)
    if match:
        client_name = match.group(1).strip()
        return client_name or None
    return None


def _typed_boards(boards: List[Dict[str, str]]) -> Dict[str, Dict[str, str]]:
    typed: Dict[str, Dict[str, str]] = {}
    for board in boards:
        normalized_name = _norm(board["name"])
        if "1. briefing" in normalized_name:
            typed["briefing"] = board
        elif "2. criacao de lp" in normalized_name or "2. criação de lp" in normalized_name:
            typed["lp"] = board
        elif "3. campanhas" in normalized_name:
            typed["campanhas"] = board
        elif "4. otimizacoes" in normalized_name or "4. otimizações" in normalized_name:
            typed["otimizacoes"] = board
        elif "5. saldo" in normalized_name:
            typed["saldo"] = board
    return typed


def list_client_groups(limit: int = 500) -> List[Dict[str, Any]]:
    boards = list_boards(limit=limit)
    groups: Dict[str, Dict[str, Any]] = {}

    for board in boards:
        client_name = _extract_client_name(board.get("name", ""))
        if not client_name:
            continue
        key = _norm(client_name)
        entry = groups.setdefault(key, {"client_name": client_name, "boards": []})
        entry["boards"].append(board)

    results: List[Dict[str, Any]] = []
    for _, entry in groups.items():
        results.append(
            {
                "client_name": entry["client_name"],
                "boards": _typed_boards(entry["boards"]),
            }
        )

    results.sort(key=lambda item: _norm(item.get("client_name", "")))
    return results


def find_client_boards(search_text: str, limit: int = 500) -> Optional[Dict[str, Any]]:
    groups = {_norm(item.get("client_name", "")): item for item in list_client_groups(limit=limit)}
    query = _norm(search_text)
    if not query:
        return None

    best = None
    best_score = -1
    query_tokens = set(query.split())

    for key, entry in groups.items():
        score = 0
        if key in query:
            score += 100
        key_tokens = set(key.split())
        score += len(query_tokens & key_tokens) * 10
        if score > best_score:
            best = entry
            best_score = score

    if best_score <= 0:
        return None

    return {"client_name": best["client_name"], "boards": best.get("boards") or {}}


def board_items_with_latest_updates(board_id: str, limit: int = 200) -> List[Dict[str, str]]:
    board_id = str(board_id or "").strip()
    if not board_id:
        return []
    data = graphql(
        f"""
        query {{
          boards(ids: [{board_id}]) {{
            items_page(limit: {int(limit)}) {{
              items {{
                id
                name
                updates(limit: 1) {{
                  text_body
                  body
                }}
              }}
            }}
          }}
        }}
        """
    )
    boards = data.get("boards") or []
    if not boards:
        return []
    items_page = boards[0].get("items_page") or {}
    items = items_page.get("items") or []
    rows: List[Dict[str, str]] = []
    for item in items:
        updates = item.get("updates") or []
        latest = updates[0] if updates else {}
        rows.append(
            {
                "id": str(item.get("id") or ""),
                "name": str(item.get("name") or ""),
                "latest_update": str(latest.get("text_body") or latest.get("body") or "").strip(),
            }
        )
    return rows


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

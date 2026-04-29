import html
import os
import re
import time
import unicodedata
from difflib import SequenceMatcher
from typing import Any, Dict, List, Optional

import requests


CACHE_TTL_SECONDS = 60

BOARD_TYPE_MARKERS = {
    "briefing": [
        "1 briefing",
        "briefing",
    ],
    "lp": [
        "2 criacao de lp e estrutura",
        "2 criação de lp e estrutura",
        "criacao de lp e estrutura",
        "criação de lp e estrutura",
        "2 criacao de lp",
        "2 criação de lp",
        "criacao de lp",
        "criação de lp",
        "landing page e estrutura",
        "lp",
    ],
    "campanhas": [
        "3 campanhas e otimizacoes",
        "3 campanhas e otimizações",
        "campanhas e otimizacoes",
        "campanhas e otimizações",
        "3 campanhas",
        "campanhas",
    ],
    "otimizacoes": [
        "4 otimizacoes",
        "4 otimizações",
        "otimizacoes",
        "otimizações",
    ],
    "saldo": [
        "5 saldo",
        "saldo",
    ],
}

ITEM_MARKERS = {
    "google": [
        "criacao de campanha google ads",
        "criação de campanha google ads",
        "campanha google ads",
        "google ads",
    ],
    "meta": [
        "criacao de campanha meta ads",
        "criação de campanha meta ads",
        "campanha meta ads",
        "meta ads",
        "facebook ads",
    ],
}

_BOARDS_CACHE: Optional[List[Dict[str, str]]] = None
_BOARDS_CACHE_AT = 0.0
_ITEMS_CACHE: Dict[str, Dict[str, Any]] = {}


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
    value = re.sub(r"[^a-z0-9]+", " ", value)
    return re.sub(r"\s+", " ", value).strip()


def _slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", _norm(text)).strip("-") or "cliente"


def _contains_marker(text_norm: str, marker_norm: str) -> bool:
    if not text_norm or not marker_norm:
        return False
    if len(marker_norm) <= 3 and " " not in marker_norm:
        return marker_norm in text_norm.split()
    return re.search(rf"\b{re.escape(marker_norm)}\b", text_norm) is not None


def _match_score(a: str, b: str) -> float:
    a_norm = _norm(a)
    b_norm = _norm(b)
    if not a_norm or not b_norm:
        return 0.0
    if a_norm == b_norm:
        return 1.0
    if a_norm in b_norm or b_norm in a_norm:
        return 0.93
    compact_a = a_norm.replace(" ", "")
    compact_b = b_norm.replace(" ", "")
    return max(
        SequenceMatcher(None, a_norm, b_norm).ratio(),
        SequenceMatcher(None, compact_a, compact_b).ratio(),
    )


def _strip_html(value: str) -> str:
    text = html.unescape(value or "")
    text = re.sub(r"<br\s*/?>", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"</p\s*>", "\n\n", text, flags=re.IGNORECASE)
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def list_boards(limit: int = 500) -> List[Dict[str, str]]:
    global _BOARDS_CACHE, _BOARDS_CACHE_AT
    now = time.time()
    if _BOARDS_CACHE is not None and now - _BOARDS_CACHE_AT < CACHE_TTL_SECONDS:
        return _BOARDS_CACHE

    data = graphql(f"query {{ boards(limit: {int(limit)}) {{ id name state }} }}")
    boards = data.get("boards") or []
    rows = []
    for board in boards:
        if str(board.get("state") or "").lower() == "archived":
            continue
        rows.append({"id": str(board.get("id") or ""), "name": str(board.get("name") or "")})
    _BOARDS_CACHE = rows
    _BOARDS_CACHE_AT = now
    return rows


def _detect_board_type(board_name: str) -> Optional[str]:
    board_norm = _norm(board_name)
    for board_type, markers in BOARD_TYPE_MARKERS.items():
        for marker in markers:
            if _contains_marker(board_norm, _norm(marker)):
                return board_type
    return None


def _extract_client_name(board_name: str, board_type: Optional[str]) -> Optional[str]:
    name = str(board_name or "").strip()
    if not board_type:
        return None

    cleaned = name
    for marker in BOARD_TYPE_MARKERS.get(board_type, []):
        escaped = re.escape(marker)
        patterns = [
            rf"^\s*{escaped}\s*[-|:/>]+\s*",
            rf"\s*[-|:/>]+\s*{escaped}\s*$",
            rf"^\s*{escaped}\s+",
            rf"\s+{escaped}\s*$",
        ]
        for pattern in patterns:
            cleaned = re.sub(pattern, "", cleaned, flags=re.IGNORECASE)

    cleaned = re.sub(r"^\s*[-|:/>]+\s*", "", cleaned).strip()
    cleaned = re.sub(r"\s*[-|:/>]+\s*$", "", cleaned).strip()
    return cleaned or None


def _typed_boards(boards: List[Dict[str, str]]) -> Dict[str, Dict[str, str]]:
    typed: Dict[str, Dict[str, str]] = {}
    for board in boards:
        board_type = _detect_board_type(board["name"])
        if board_type and board_type not in typed:
            typed[board_type] = board
    return typed


def list_client_groups(limit: int = 500) -> List[Dict[str, Any]]:
    groups: Dict[str, Dict[str, Any]] = {}
    for board in list_boards(limit=limit):
        board_type = _detect_board_type(board["name"])
        if not board_type:
            continue
        client_name = _extract_client_name(board["name"], board_type)
        if not client_name:
            continue
        key = _norm(client_name)
        entry = groups.setdefault(key, {"client_name": client_name, "boards": []})
        entry["boards"].append(board)

    results: List[Dict[str, Any]] = []
    for entry in groups.values():
        results.append({"client_name": entry["client_name"], "boards": _typed_boards(entry["boards"])})
    results.sort(key=lambda item: _norm(item.get("client_name", "")))
    return results


def find_client_boards(search_text: str, limit: int = 500) -> Optional[Dict[str, Any]]:
    groups = list_client_groups(limit=limit)
    query = _norm(search_text)
    if not query:
        return None

    for entry in groups:
        client_name = entry.get("client_name", "")
        if query in (_norm(client_name), _slug(client_name), _norm(f"monday-{_slug(client_name)}")):
            return {"client_name": client_name, "boards": entry.get("boards") or {}}

    for entry in groups:
        client_name = entry.get("client_name", "")
        client_norm = _norm(client_name)
        if query in client_norm or client_norm in query:
            return {"client_name": client_name, "boards": entry.get("boards") or {}}

    best_entry = None
    best_score = 0.0
    for entry in groups:
        score = _match_score(query, entry.get("client_name", ""))
        if score > best_score:
            best_entry = entry
            best_score = score

    if best_entry and best_score >= 0.72:
        return {"client_name": best_entry["client_name"], "boards": best_entry.get("boards") or {}}
    return None


def board_items_with_latest_updates(board_id: str, limit: int = 200) -> List[Dict[str, str]]:
    board_id = str(board_id or "").strip()
    if not board_id:
        return []

    cache_key = f"board:{board_id}:{int(limit)}"
    now = time.time()
    cached = _ITEMS_CACHE.get(cache_key)
    if cached and now - cached["at"] < CACHE_TTL_SECONDS:
        return cached["rows"]

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
    rows = []
    for item in items:
        updates = item.get("updates") or []
        latest = updates[0] if updates else {}
        rows.append(
            {
                "id": str(item.get("id") or ""),
                "name": str(item.get("name") or ""),
                "latest_update": _strip_html(str(latest.get("text_body") or latest.get("body") or "").strip()),
            }
        )

    _ITEMS_CACHE[cache_key] = {"at": now, "rows": rows}
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
    return _strip_html(str(update.get("text_body") or update.get("body") or "").strip())

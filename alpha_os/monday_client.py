import html
import os
import re
import time
import unicodedata
import json
from datetime import date, datetime, timedelta
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
_TASKS_CACHE: Optional[List[Dict[str, Any]]] = None
_TASKS_CACHE_AT = 0.0


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


# Marcadores tipicos de mojibake UTF-8-lido-como-latin1
_MOJIBAKE_MARKERS = (
    "Ã§", "Ã£", "Ã©", "Ã¡", "Ã³", "Ãµ", "Ã­",
    "ÃÂ", "Â ", "â€", "ï¿½",
    "Ã§", "Ã£", "Ã©",
)


def _fix_mojibake(value: str) -> str:
    """
    Desfaz mojibake UTF-8 lido como Latin-1.
    Ex: 'Criaã§ã£o' -> 'Criação'
    Aplica so se detectar marcadores tipicos.
    """
    if not value or not any(m in value for m in _MOJIBAKE_MARKERS):
        return value
    try:
        return value.encode("latin-1", errors="strict").decode("utf-8", errors="strict")
    except (UnicodeEncodeError, UnicodeDecodeError):
        # tenta com cp1252 (Windows variant) que cobre mais bytes
        try:
            return value.encode("cp1252", errors="strict").decode("utf-8", errors="strict")
        except (UnicodeEncodeError, UnicodeDecodeError):
            return value


def _clean_text(value: Any) -> str:
    """
    Sanitiza string vinda do Monday/Supabase:
    - desfaz mojibake (UTF-8 lido como Latin-1)
    - remove surrogates invalidos
    - normaliza Unicode pra NFC
    """
    if value is None:
        return ""
    if not isinstance(value, str):
        value = str(value)
    # 1. tenta desfazer mojibake se detectado
    value = _fix_mojibake(value)
    # 2. remove surrogates invalidos
    value = value.encode("utf-8", errors="ignore").decode("utf-8", errors="ignore")
    # 3. normaliza
    return unicodedata.normalize("NFC", value)


def _looks_like_email(value: str) -> bool:
    if not value:
        return False
    return "@" in value and "." in value.split("@", 1)[-1]


# Mapeamento manual de email -> nome display (quando o Monday devolve email no campo de pessoa)
EMAIL_TO_NAME: Dict[str, str] = {
    "je.belleck1@gmail.com": "Jefferson Belleck",
    "jefferson@alphadigital.com.br": "Jefferson Belleck",
}


def _resolve_person_name(raw: str) -> str:
    raw = _clean_text(raw).strip()
    if not raw:
        return raw
    if _looks_like_email(raw):
        key = raw.lower()
        if key in EMAIL_TO_NAME:
            return EMAIL_TO_NAME[key]
        # fallback: pega parte antes do @, capitaliza
        local = key.split("@", 1)[0]
        local = re.sub(r"[\._-]+", " ", local).strip().title()
        return local or raw
    return raw


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


def _parse_json(value: str) -> Dict[str, Any]:
    raw = str(value or "").strip()
    if not raw:
        return {}
    try:
        parsed = json.loads(raw)
        return parsed if isinstance(parsed, dict) else {}
    except Exception:
        return {}


def _parse_iso_date(value: str) -> Optional[date]:
    raw = str(value or "").strip()
    if not raw:
        return None
    for fmt in ("%Y-%m-%d", "%Y-%m-%d %H:%M:%S", "%d/%m/%Y", "%m/%d/%Y"):
        try:
            return datetime.strptime(raw[: len(fmt)], fmt).date()
        except Exception:
            continue
    match = re.search(r"(\d{4}-\d{2}-\d{2})", raw)
    if match:
        try:
            return datetime.strptime(match.group(1), "%Y-%m-%d").date()
        except Exception:
            return None
    return None


def _extract_column_date(column: Dict[str, Any]) -> Optional[date]:
    text = str(column.get("text") or "").strip()
    if text:
        parsed = _parse_iso_date(text)
        if parsed:
            return parsed
    value = _parse_json(column.get("value") or "")
    for key in ("date", "from", "to"):
        parsed = _parse_iso_date(str(value.get(key) or ""))
        if parsed:
            return parsed
    return None


def _split_people(text: str) -> List[str]:
    raw = str(text or "").strip()
    if not raw:
        return []
    parts = re.split(r",|/|;|\n| e ", raw, flags=re.IGNORECASE)
    people = []
    for part in parts:
        value = part.strip()
        if value and value not in people:
            people.append(value)
    return people


def _is_done_status(status_text: str) -> bool:
    status_norm = _norm(status_text)
    return status_norm in {
        "feito",
        "concluido",
        "concluida",
        "done",
        "complete",
        "completed",
        "finalizado",
        "finalizada",
        "ok",
    }


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
        board_name = _clean_text(board.get("name") or "")
        # filtra boards auxiliares de subitens (Monday cria automaticamente como "Subelementos de ...")
        if board_name.lower().startswith(("subelementos de", "subitems of", "subelementos")):
            continue
        rows.append({"id": str(board.get("id") or ""), "name": board_name})
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
    name = _clean_text(board_name or "").strip()
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

    # remove numeracao residual do POP (ex: "- 3.", "3 -", "1.", " 5 ", "- 4. ")
    cleaned = re.sub(r"\s*[-|:/>]+\s*\d+\.?\s*$", "", cleaned).strip()
    cleaned = re.sub(r"^\s*\d+\.?\s*[-|:/>]+\s*", "", cleaned).strip()
    cleaned = re.sub(r"\s+\d+\.?\s*$", "", cleaned).strip()
    cleaned = re.sub(r"^\s*\d+\.?\s+", "", cleaned).strip()
    # tira separadores residuais
    cleaned = re.sub(r"^\s*[-|:/>]+\s*", "", cleaned).strip()
    cleaned = re.sub(r"\s*[-|:/>]+\s*$", "", cleaned).strip()
    return cleaned or None


def _looks_like_valid_client_name(client_name: str, board_type: Optional[str]) -> bool:
    name = _norm(client_name)
    if not name:
        return False
    if len(name) < 4:
        return False
    generic_names = {
        "briefing",
        "lp",
        "saldo",
        "campanhas",
        "otimizacoes",
        "otimizacoes es",
        "criacao de lp",
        "criacao de lp e estrutura",
        "e estrutura",
        "estrutura",
        # nomes residuais que aparecem quando o board e generico (sem cliente)
        "e otimizacoes",
        "saldo de campanha",
        "campanha",
        "campanhas e otimizacoes",
        "criacao de lp e estrutura es",
    }
    if name in generic_names:
        return False
    # se comeca com fragmento residual de marker (ex: "e otimiz...")
    suspicious_prefixes = ("e otimiz", "e estrutura", "de saldo", "de campanha")
    for prefix in suspicious_prefixes:
        if name.startswith(prefix):
            return False
    for marker in BOARD_TYPE_MARKERS.get(board_type or "", []):
        marker_norm = _norm(marker)
        if name == marker_norm:
            return False
        # rejeita se o que sobrou esta contido inteiramente dentro do marker
        if name in marker_norm:
            return False
    return True


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
        if not client_name or not _looks_like_valid_client_name(client_name, board_type):
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


def board_items_full(board_id: str, limit: int = 200) -> List[Dict[str, Any]]:
    board_id = str(board_id or "").strip()
    if not board_id:
        return []

    cache_key = f"board_full:{board_id}:{int(limit)}"
    now = time.time()
    cached = _ITEMS_CACHE.get(cache_key)
    if cached and now - cached["at"] < CACHE_TTL_SECONDS:
        return cached["rows"]

    data = graphql(
        f"""
        query {{
          boards(ids: [{board_id}]) {{
            id
            name
            items_page(limit: {int(limit)}) {{
              items {{
                id
                name
                group {{
                  id
                  title
                }}
                column_values {{
                  id
                  text
                  type
                  value
                  column {{
                    title
                  }}
                }}
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

    board = boards[0]
    board_name = _clean_text(board.get("name") or "")
    items = ((board.get("items_page") or {}).get("items")) or []
    rows: List[Dict[str, Any]] = []
    for item in items:
        updates = item.get("updates") or []
        latest = updates[0] if updates else {}
        columns = []
        for column in item.get("column_values") or []:
            columns.append(
                {
                    "id": str(column.get("id") or ""),
                    "title": str((column.get("column") or {}).get("title") or ""),
                    "type": str(column.get("type") or ""),
                    "text": str(column.get("text") or ""),
                    "value": str(column.get("value") or ""),
                }
            )
        rows.append(
            {
                "id": str(item.get("id") or ""),
                "name": str(item.get("name") or ""),
                "board_id": board_id,
                "board_name": board_name,
                "group_id": str((item.get("group") or {}).get("id") or ""),
                "group_name": str((item.get("group") or {}).get("title") or ""),
                "latest_update": _strip_html(str(latest.get("text_body") or latest.get("body") or "").strip()),
                "columns": columns,
            }
        )

    _ITEMS_CACHE[cache_key] = {"at": now, "rows": rows}
    return rows


def list_all_tasks(limit_per_board: int = 200) -> List[Dict[str, Any]]:
    global _TASKS_CACHE, _TASKS_CACHE_AT
    now = time.time()
    if _TASKS_CACHE is not None and now - _TASKS_CACHE_AT < CACHE_TTL_SECONDS:
        return _TASKS_CACHE

    tasks: List[Dict[str, Any]] = []
    for entry in list_client_groups(limit=500):
        client_name = str(entry.get("client_name") or "")
        boards = entry.get("boards") or {}
        for board_type, board in boards.items():
            board_id = str((board or {}).get("id") or "").strip()
            if not board_id:
                continue
            for item in board_items_full(board_id, limit=limit_per_board):
                status_text = ""
                due_date = None
                people: List[str] = []
                priority_text = ""
                columns_by_title: Dict[str, str] = {}
                status_column_id = ""

                for column in item.get("columns") or []:
                    title = _clean_text(column.get("title") or "")
                    title_norm = _norm(title)
                    text = _clean_text(column.get("text") or "").strip()
                    col_type = str(column.get("type") or "").strip().lower()
                    if title:
                        columns_by_title[title] = text

                    if not due_date and col_type in ("date", "timeline"):
                        due_date = _extract_column_date(column)
                    if not status_text and (title_norm == "status" or col_type in ("color", "status")) and text:
                        status_text = text
                        status_column_id = str(column.get("id") or "")
                    if not priority_text and title_norm == "prioridade" and text:
                        priority_text = text
                    if col_type in ("multiple-person", "people", "person", "team") and text:
                        for raw_person in _split_people(text):
                            people.append(_resolve_person_name(raw_person))

                dedup_people: List[str] = []
                for person in people:
                    if person and person not in dedup_people:
                        dedup_people.append(person)

                tasks.append(
                    {
                        "client_name": _clean_text(client_name),
                        "board_type": board_type,
                        "board_id": item.get("board_id"),
                        "board_name": _clean_text(item.get("board_name") or ""),
                        "group_id": item.get("group_id"),
                        "group_name": _clean_text(item.get("group_name") or ""),
                        "item_id": item.get("id"),
                        "item_name": _clean_text(item.get("name") or ""),
                        "status": _clean_text(status_text),
                        "status_column_id": status_column_id,
                        "priority": _clean_text(priority_text),
                        "due_date": due_date.isoformat() if due_date else "",
                        "assignees": dedup_people,
                        "assignees_text": ", ".join(dedup_people),
                        "latest_update": _clean_text(item.get("latest_update") or ""),
                        "columns": columns_by_title,
                    }
                )

    _TASKS_CACHE = tasks
    _TASKS_CACHE_AT = now
    return tasks


def find_tasks(
    search_text: str,
    client_name: str = "",
    assignee_name: str = "",
    include_done: bool = True,
    limit: int = 20,
) -> List[Dict[str, Any]]:
    query = _norm(search_text)
    client_query = _norm(client_name)
    assignee_query = _norm(assignee_name)
    matches: List[Dict[str, Any]] = []

    for task in list_all_tasks():
        if client_query and client_query not in _norm(task.get("client_name")):
            continue
        if assignee_query and assignee_query not in _norm(task.get("assignees_text")):
            continue
        if not include_done and _is_done_status(task.get("status") or ""):
            continue

        haystacks = [
            task.get("item_name") or "",
            task.get("board_name") or "",
            task.get("group_name") or "",
            task.get("latest_update") or "",
        ]
        score = 0.0
        for hay in haystacks:
            score = max(score, _match_score(query, hay))
            if query and (_norm(query) in _norm(hay) or _norm(hay) in _norm(query)):
                score = max(score, 0.94)
        if client_query and client_query == _norm(task.get("client_name") or ""):
            score += 0.03
        if score >= 0.72:
            enriched = dict(task)
            enriched["_score"] = score
            matches.append(enriched)

    matches.sort(key=lambda item: item.get("_score", 0.0), reverse=True)
    return matches[:limit]


def tasks_for_window(
    start_date: date,
    end_date: date,
    assignee_name: str = "",
    include_done: bool = False,
) -> List[Dict[str, Any]]:
    assignee_query = _norm(assignee_name)
    rows: List[Dict[str, Any]] = []
    for task in list_all_tasks():
        due = _parse_iso_date(task.get("due_date") or "")
        if not due or due < start_date or due > end_date:
            continue
        if assignee_query and assignee_query not in _norm(task.get("assignees_text")):
            continue
        if not include_done and _is_done_status(task.get("status") or ""):
            continue
        rows.append(task)
    rows.sort(key=lambda item: (item.get("due_date") or "", _norm(item.get("client_name") or ""), _norm(item.get("item_name") or "")))
    return rows


def overdue_tasks(reference_date: Optional[date] = None, assignee_name: str = "", include_done: bool = False) -> List[Dict[str, Any]]:
    today = reference_date or date.today()
    assignee_query = _norm(assignee_name)
    rows: List[Dict[str, Any]] = []
    for task in list_all_tasks():
        due = _parse_iso_date(task.get("due_date") or "")
        if not due or due >= today:
            continue
        if assignee_query and assignee_query not in _norm(task.get("assignees_text")):
            continue
        if not include_done and _is_done_status(task.get("status") or ""):
            continue
        rows.append(task)
    rows.sort(key=lambda item: (item.get("due_date") or "", _norm(item.get("client_name") or ""), _norm(item.get("item_name") or "")))
    return rows


def weekly_tasks(reference_date: Optional[date] = None, assignee_name: str = "", include_done: bool = False) -> List[Dict[str, Any]]:
    today = reference_date or date.today()
    end = today + timedelta(days=7)
    return tasks_for_window(today, end, assignee_name=assignee_name, include_done=include_done)


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

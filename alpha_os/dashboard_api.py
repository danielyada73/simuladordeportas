"""
Dashboard API.

Reads tasks from Supabase snapshot (kind='tasks_full') populated by /api/sync.
Painel sempre le do cache (instantaneo). Monday so e tocado quando /sync roda.

Auth: Bearer token via DASHBOARD_API_TOKEN.
Sync auth: Bearer token via DASHBOARD_API_TOKEN OU SYNC_SECRET (pra cron jobs).
"""

from __future__ import annotations

import os
from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Header, HTTPException, Query

from . import monday_client
from . import monday_sync
from . import supabase_client


router = APIRouter(prefix="/api", tags=["dashboard"])


# ---------------------------------------------------------------- auth

def _expected_token() -> str:
    token = os.getenv("DASHBOARD_API_TOKEN", "").strip()
    if not token:
        raise HTTPException(status_code=500, detail="DASHBOARD_API_TOKEN nao configurado")
    return token


def _check_auth(authorization: Optional[str]) -> None:
    expected = _expected_token()
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Bearer token obrigatorio")
    if authorization.split(" ", 1)[1].strip() != expected:
        raise HTTPException(status_code=401, detail="Token invalido")


def _check_sync_auth(authorization: Optional[str]) -> None:
    """Sync aceita DASHBOARD_API_TOKEN OU um SYNC_SECRET separado (pra Render Cron)."""
    expected = _expected_token()
    sync_secret = os.getenv("SYNC_SECRET", "").strip()
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Bearer token obrigatorio")
    token = authorization.split(" ", 1)[1].strip()
    if token != expected and (not sync_secret or token != sync_secret):
        raise HTTPException(status_code=401, detail="Token invalido")


# ---------------------------------------------------------------- helpers

PRIORITY_ORDER = {
    "critico": 0, "critica": 0, "urgente": 1,
    "alta": 2, "media": 3, "média": 3, "baixa": 4,
}


def _priority_rank(value: str) -> int:
    return PRIORITY_ORDER.get((value or "").strip().lower(), 5)


def _is_done(status_text: str) -> bool:
    return monday_client._is_done_status(status_text or "")


def _parse_date_param(value: Optional[str]) -> Optional[date]:
    if not value:
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Data invalida: {value}") from exc


def _window_range(window: str, custom_from: Optional[str], custom_to: Optional[str]) -> tuple[Optional[date], Optional[date]]:
    today = date.today()
    window = (window or "all").lower()
    if window == "today": return today, today
    if window == "tomorrow": return today + timedelta(days=1), today + timedelta(days=1)
    if window == "week": return today, today + timedelta(days=7)
    if window == "month": return today, today + timedelta(days=30)
    if window == "overdue": return None, today - timedelta(days=1)
    if window == "custom": return _parse_date_param(custom_from), _parse_date_param(custom_to)
    if window == "all": return None, None
    raise HTTPException(status_code=400, detail=f"Janela invalida: {window}")


def _load_tasks_from_cache() -> tuple[List[Dict[str, Any]], Optional[str]]:
    """Le tarefas do Supabase. Se Supabase nao configurado, fallback pra Monday direto."""
    if supabase_client.is_configured():
        try:
            cached = monday_sync.load_cached_tasks()
            return cached["tasks"], cached.get("last_synced_at")
        except RuntimeError as exc:
            # cache vazio — tenta Monday direto na primeira vez
            try:
                return monday_client.list_all_tasks(), None
            except Exception as monday_exc:
                raise HTTPException(
                    status_code=503,
                    detail=f"Cache vazio e Monday indisponivel: {monday_exc}. Rode POST /api/sync.",
                ) from exc
    # Sem Supabase, vai direto no Monday (modo legado)
    try:
        return monday_client.list_all_tasks(), None
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Monday indisponivel: {exc}") from exc


def _filter_and_sort(
    tasks: List[Dict[str, Any]],
    window: str,
    custom_from: Optional[str],
    custom_to: Optional[str],
    assignee: Optional[str],
    client: Optional[str],
    include_done: bool,
) -> List[Dict[str, Any]]:
    start, end = _window_range(window, custom_from, custom_to)
    assignee_norm = monday_client._norm(assignee or "")
    client_norm = monday_client._norm(client or "")

    rows: List[Dict[str, Any]] = []
    for task in tasks:
        due_str = task.get("due_date") or ""
        due = monday_client._parse_iso_date(due_str) if due_str else None

        if window != "all":
            if window == "overdue":
                if not due or due >= date.today():
                    continue
                if _is_done(task.get("status") or ""):
                    continue
            else:
                if start and (not due or due < start):
                    continue
                if end and (not due or due > end):
                    continue

        if not include_done and _is_done(task.get("status") or ""):
            continue
        if assignee_norm and assignee_norm not in monday_client._norm(task.get("assignees_text") or ""):
            continue
        if client_norm and client_norm not in monday_client._norm(task.get("client_name") or ""):
            continue

        rows.append(task)

    rows.sort(key=lambda t: (
        _priority_rank(t.get("priority") or ""),
        t.get("due_date") or "9999-12-31",
        monday_client._norm(t.get("client_name") or ""),
    ))
    return rows


def _serialize_task(task: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "id": task.get("item_id"),
        "name": task.get("item_name"),
        "client": task.get("client_name"),
        "board_type": task.get("board_type"),
        "board_name": task.get("board_name"),
        "group_name": task.get("group_name"),
        "status": task.get("status"),
        "priority": task.get("priority"),
        "priority_rank": _priority_rank(task.get("priority") or ""),
        "due_date": task.get("due_date"),
        "assignees": task.get("assignees") or [],
        "latest_update": (task.get("latest_update") or "")[:500],
        "is_done": _is_done(task.get("status") or ""),
    }


# ---------------------------------------------------------------- endpoints

@router.get("/health")
def health() -> Dict[str, Any]:
    cache_info: Dict[str, Any] = {"supabase_configured": supabase_client.is_configured()}
    if supabase_client.is_configured():
        try:
            snap = supabase_client.load_snapshot(monday_sync.SNAPSHOT_KIND_TASKS)
            if snap:
                cache_info["last_sync"] = snap.get("last_synced_at")
                cache_info["item_count"] = snap.get("item_count")
                cache_info["sync_status"] = snap.get("status")
            else:
                cache_info["cache"] = "empty"
        except Exception as exc:
            cache_info["error"] = str(exc)[:200]
    return {"status": "ok", "service": "dashboard_api", "time": datetime.utcnow().isoformat(), **cache_info}


@router.get("/debug/boards")
def debug_boards(authorization: Optional[str] = Header(default=None)) -> Dict[str, Any]:
    _check_auth(authorization)
    try:
        boards = monday_client.list_boards(limit=20)
        return {
            "count": len(boards),
            "token_tail": (monday_client.monday_token()[-6:] if monday_client.monday_token() else "no-token"),
            "sample": [{"id": b["id"], "name": b["name"]} for b in boards[:10]],
        }
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Monday call failed: {exc}") from exc


@router.post("/sync")
def trigger_sync(authorization: Optional[str] = Header(default=None)) -> Dict[str, Any]:
    """Forca sync Monday → Supabase. Pode ser chamado por cron (Render Cron Job)."""
    _check_sync_auth(authorization)
    return monday_sync.sync_tasks_full()


@router.get("/tasks")
def list_tasks(
    authorization: Optional[str] = Header(default=None),
    window: str = Query(default="all"),
    custom_from: Optional[str] = Query(default=None),
    custom_to: Optional[str] = Query(default=None),
    assignee: Optional[str] = Query(default=None),
    client: Optional[str] = Query(default=None),
    include_done: bool = Query(default=False),
    limit: int = Query(default=500, ge=1, le=2000),
) -> Dict[str, Any]:
    _check_auth(authorization)
    tasks, last_synced = _load_tasks_from_cache()
    filtered = _filter_and_sort(tasks, window, custom_from, custom_to, assignee, client, include_done)
    serialized = [_serialize_task(t) for t in filtered[:limit]]
    return {
        "window": window,
        "count": len(serialized),
        "total_before_limit": len(filtered),
        "last_synced_at": last_synced,
        "items": serialized,
    }


@router.get("/tasks/by-assignee")
def tasks_by_assignee(
    authorization: Optional[str] = Header(default=None),
    window: str = Query(default="all"),
    custom_from: Optional[str] = Query(default=None),
    custom_to: Optional[str] = Query(default=None),
) -> Dict[str, Any]:
    _check_auth(authorization)
    all_tasks, last_synced = _load_tasks_from_cache()
    in_window = _filter_and_sort(all_tasks, window, custom_from, custom_to,
                                  assignee=None, client=None, include_done=True)

    today = date.today()
    week_end = today + timedelta(days=7)

    buckets: Dict[str, Dict[str, Any]] = {}
    for task in in_window:
        names = task.get("assignees") or ["Sem responsavel"]
        status_done = _is_done(task.get("status") or "")
        due = monday_client._parse_iso_date(task.get("due_date") or "")

        is_overdue = bool(due and due < today and not status_done)
        is_next7 = bool(due and today <= due <= week_end and not status_done)
        is_in_progress = (not status_done) and not is_overdue

        for name in names:
            bucket = buckets.setdefault(name, {
                "assignee": name, "total": 0, "done": 0, "overdue": 0,
                "in_progress": 0, "next_7_days": 0,
                "by_priority": {"urgente": 0, "alta": 0, "media": 0, "baixa": 0, "outros": 0},
            })
            bucket["total"] += 1
            if status_done: bucket["done"] += 1
            if is_overdue: bucket["overdue"] += 1
            if is_in_progress: bucket["in_progress"] += 1
            if is_next7: bucket["next_7_days"] += 1

            prio = (task.get("priority") or "").strip().lower()
            if prio in ("urgente", "critico", "critica"): bucket["by_priority"]["urgente"] += 1
            elif prio == "alta": bucket["by_priority"]["alta"] += 1
            elif prio in ("media", "média"): bucket["by_priority"]["media"] += 1
            elif prio == "baixa": bucket["by_priority"]["baixa"] += 1
            else: bucket["by_priority"]["outros"] += 1

    rows = sorted(buckets.values(), key=lambda b: (-b["overdue"], -b["in_progress"], b["assignee"]))
    return {"window": window, "last_synced_at": last_synced, "assignees": rows}


POP_STAGE_BY_BOARD = {"briefing": 1, "lp": 3, "campanhas": 5, "otimizacoes": 6, "saldo": 6}
POP_STAGE_LABELS = {
    1: "Briefing", 3: "Criacao de LP", 5: "Estruturacao de Campanhas",
    6: "Otimizacao + Saldo (loop semanal)",
}


@router.get("/clients/stages")
def clients_stages(authorization: Optional[str] = Header(default=None)) -> Dict[str, Any]:
    _check_auth(authorization)
    all_tasks, last_synced = _load_tasks_from_cache()

    by_client: Dict[str, Dict[str, Dict[str, int]]] = {}
    for task in all_tasks:
        client_name = task.get("client_name") or ""
        board_type = task.get("board_type") or ""
        if not client_name or not board_type: continue
        c = by_client.setdefault(client_name, {})
        b = c.setdefault(board_type, {"total": 0, "done": 0, "overdue": 0})
        b["total"] += 1
        if _is_done(task.get("status") or ""): b["done"] += 1
        due = monday_client._parse_iso_date(task.get("due_date") or "")
        if due and due < date.today() and not _is_done(task.get("status") or ""):
            b["overdue"] += 1

    rows: List[Dict[str, Any]] = []
    for client_name, boards in by_client.items():
        boards_summary = {}
        for board_type, stats in boards.items():
            pct = (stats["done"] / stats["total"] * 100.0) if stats["total"] > 0 else 0.0
            boards_summary[board_type] = {
                "total": stats["total"], "done": stats["done"],
                "overdue": stats["overdue"], "pct_done": round(pct, 1),
            }

        current_stage = 1
        for board_type in ("briefing", "lp", "campanhas", "otimizacoes", "saldo"):
            b = boards_summary.get(board_type)
            if not b: continue
            if b["pct_done"] < 100:
                current_stage = POP_STAGE_BY_BOARD[board_type]
                break
            current_stage = POP_STAGE_BY_BOARD[board_type]

        total_overdue = sum(b["overdue"] for b in boards_summary.values())
        if current_stage >= 6 and total_overdue == 0:
            health = "green"
        elif total_overdue == 0:
            health = "yellow"
        else:
            health = "red"

        rows.append({
            "client": client_name,
            "current_stage": current_stage,
            "current_stage_label": POP_STAGE_LABELS.get(current_stage, ""),
            "health": health,
            "total_overdue": total_overdue,
            "boards": boards_summary,
        })

    rows.sort(key=lambda r: (-r["total_overdue"], r["current_stage"], r["client"]))
    return {"count": len(rows), "last_synced_at": last_synced, "clients": rows}

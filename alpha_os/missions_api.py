"""
Missions API — sistema 100% independente do Monday.

Usa Supabase como fonte unica de verdade. Mesma autenticacao
Bearer DASHBOARD_API_TOKEN do dashboard_api.
"""

from __future__ import annotations

import os
from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Header, HTTPException, Query
from pydantic import BaseModel, Field

from . import supabase_client


router = APIRouter(prefix="/api", tags=["missions"])


# ---------------------------------------------------------------- auth

def _check_auth(authorization: Optional[str]) -> None:
    expected = os.getenv("DASHBOARD_API_TOKEN", "").strip()
    if not expected:
        raise HTTPException(status_code=500, detail="DASHBOARD_API_TOKEN nao configurado")
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Bearer token obrigatorio")
    if authorization.split(" ", 1)[1].strip() != expected:
        raise HTTPException(status_code=401, detail="Token invalido")


def _require_supabase():
    if not supabase_client.is_configured():
        raise HTTPException(status_code=500, detail="Supabase nao configurado")
    return supabase_client.get_client()


# ---------------------------------------------------------------- date helpers

def _window_dates(window: str, custom_from: Optional[str], custom_to: Optional[str]) -> tuple[Optional[str], Optional[str]]:
    today = date.today()
    w = (window or "all").lower()
    if w == "today": return today.isoformat(), today.isoformat()
    if w == "tomorrow":
        d = (today + timedelta(days=1)).isoformat()
        return d, d
    if w == "overdue": return None, (today - timedelta(days=1)).isoformat()
    if w == "week": return today.isoformat(), (today + timedelta(days=7)).isoformat()
    if w == "month": return today.isoformat(), (today + timedelta(days=30)).isoformat()
    if w == "custom": return custom_from, custom_to
    if w == "all": return None, None
    raise HTTPException(status_code=400, detail=f"Janela invalida: {window}")


# ---------------------------------------------------------------- schemas

class MissionCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    client: Optional[str] = None
    responsible_slug: str
    priority: str = "media"
    kind: str = "principal"
    due_date: str
    notes: Optional[str] = None
    sort_order: Optional[int] = None
    created_by_slug: Optional[str] = None


class MissionUpdate(BaseModel):
    name: Optional[str] = None
    client: Optional[str] = None
    responsible_slug: Optional[str] = None
    priority: Optional[str] = None
    kind: Optional[str] = None
    due_date: Optional[str] = None
    status: Optional[str] = None
    notes: Optional[str] = None
    sort_order: Optional[int] = None


class UserCreate(BaseModel):
    slug: str = Field(min_length=2, max_length=40)
    display_name: str = Field(min_length=1, max_length=80)
    photo_url: Optional[str] = None
    accent_color: Optional[str] = "#3b82f6"


class UserUpdate(BaseModel):
    display_name: Optional[str] = None
    photo_url: Optional[str] = None
    accent_color: Optional[str] = None
    is_active: Optional[bool] = None
    sort_order: Optional[int] = None


class SettingsUpdate(BaseModel):
    logo_url: Optional[str] = None
    client_options: Optional[List[str]] = None


_PRIORITY_RANK = {"alta": 0, "media": 1, "baixa": 2}


def _mission_sort_key(mission: Dict[str, Any]) -> tuple[int, str, int, str]:
    raw_order = mission.get("sort_order")
    try:
        sort_order = int(raw_order) if raw_order is not None else 999999
    except (TypeError, ValueError):
        sort_order = 999999
    return (
        sort_order,
        mission.get("due_date") or "",
        _PRIORITY_RANK.get(mission.get("priority") or "media", 1),
        mission.get("created_at") or "",
    )


# ---------------------------------------------------------------- missions

@router.get("/missions")
def list_missions(
    authorization: Optional[str] = Header(default=None),
    window: str = Query(default="all"),
    custom_from: Optional[str] = Query(default=None),
    custom_to: Optional[str] = Query(default=None),
    include_completed: bool = Query(default=True),
) -> Dict[str, Any]:
    _check_auth(authorization)
    sb = _require_supabase()
    start, end = _window_dates(window, custom_from, custom_to)

    q = sb.table("missions").select("*")
    if start: q = q.gte("due_date", start)
    if end: q = q.lte("due_date", end)
    if not include_completed: q = q.neq("status", "concluida")

    rows = q.execute().data or []
    rows.sort(key=_mission_sort_key)
    return {"window": window, "count": len(rows), "items": rows}


@router.get("/missions/stats")
def missions_stats(
    authorization: Optional[str] = Header(default=None),
    window: str = Query(default="today"),
    custom_from: Optional[str] = Query(default=None),
    custom_to: Optional[str] = Query(default=None),
) -> Dict[str, Any]:
    _check_auth(authorization)
    sb = _require_supabase()
    start, end = _window_dates(window, custom_from, custom_to)

    q = sb.table("missions").select("*")
    if start: q = q.gte("due_date", start)
    if end: q = q.lte("due_date", end)
    rows = q.execute().data or []

    total = len(rows)
    by_status = {"nao_iniciada": 0, "em_progresso": 0, "concluida": 0}
    by_priority = {"alta": 0, "media": 0, "baixa": 0}
    by_kind = {"principal": 0, "secundaria": 0}
    by_responsible: Dict[str, Dict[str, int]] = {}

    for m in rows:
        s = m.get("status") or "nao_iniciada"
        p = m.get("priority") or "media"
        k = m.get("kind") or "principal"
        r = m.get("responsible_slug") or "?"

        by_status[s] = by_status.get(s, 0) + 1
        by_priority[p] = by_priority.get(p, 0) + 1
        by_kind[k] = by_kind.get(k, 0) + 1

        bucket = by_responsible.setdefault(r, {
            "slug": r, "total": 0, "done": 0, "in_progress": 0, "not_started": 0,
            "alta": 0, "media": 0, "baixa": 0, "principal": 0, "secundaria": 0,
        })
        bucket["total"] += 1
        if s == "concluida": bucket["done"] += 1
        elif s == "em_progresso": bucket["in_progress"] += 1
        else: bucket["not_started"] += 1
        bucket[p] = bucket.get(p, 0) + 1
        bucket[k] = bucket.get(k, 0) + 1

    return {
        "window": window,
        "total": total,
        "by_status": by_status,
        "by_priority": by_priority,
        "by_kind": by_kind,
        "by_responsible": list(by_responsible.values()),
    }


@router.post("/missions")
def create_mission(
    payload: MissionCreate,
    authorization: Optional[str] = Header(default=None),
) -> Dict[str, Any]:
    _check_auth(authorization)
    sb = _require_supabase()

    if payload.priority not in ("alta", "media", "baixa"):
        raise HTTPException(status_code=400, detail="priority invalido")
    if payload.kind not in ("principal", "secundaria"):
        raise HTTPException(status_code=400, detail="kind invalido")
    try:
        datetime.strptime(payload.due_date, "%Y-%m-%d")
    except Exception:
        raise HTTPException(status_code=400, detail="due_date deve ser YYYY-MM-DD")

    data = payload.model_dump(exclude_none=True)
    result = sb.table("missions").insert(data).execute()
    rows = result.data or []
    if not rows:
        raise HTTPException(status_code=500, detail="Falha ao criar missao")
    return rows[0]


@router.patch("/missions/{mission_id}")
def update_mission(
    mission_id: str,
    payload: MissionUpdate,
    authorization: Optional[str] = Header(default=None),
) -> Dict[str, Any]:
    _check_auth(authorization)
    sb = _require_supabase()

    update: Dict[str, Any] = {k: v for k, v in payload.model_dump(exclude_unset=True).items()}
    if "status" in update and update["status"] not in ("nao_iniciada", "em_progresso", "concluida"):
        raise HTTPException(status_code=400, detail="status invalido")
    if "priority" in update and update["priority"] not in ("alta", "media", "baixa"):
        raise HTTPException(status_code=400, detail="priority invalido")
    if "kind" in update and update["kind"] not in ("principal", "secundaria"):
        raise HTTPException(status_code=400, detail="kind invalido")
    if "due_date" in update:
        try:
            datetime.strptime(update["due_date"], "%Y-%m-%d")
        except Exception:
            raise HTTPException(status_code=400, detail="due_date deve ser YYYY-MM-DD")

    update["updated_at"] = datetime.utcnow().isoformat()
    if update.get("status") == "concluida":
        update["completed_at"] = datetime.utcnow().isoformat()
    elif "status" in update:
        # se voltou pra outro status, limpa completed_at
        update["completed_at"] = None

    result = sb.table("missions").update(update).eq("id", mission_id).execute()
    rows = result.data or []
    if not rows:
        raise HTTPException(status_code=404, detail="Missao nao encontrada")
    return rows[0]


@router.delete("/missions/{mission_id}")
def delete_mission(
    mission_id: str,
    authorization: Optional[str] = Header(default=None),
) -> Dict[str, Any]:
    _check_auth(authorization)
    sb = _require_supabase()
    result = sb.table("missions").delete().eq("id", mission_id).execute()
    return {"deleted": True, "id": mission_id, "rows": len(result.data or [])}


# ---------------------------------------------------------------- users

@router.get("/mission-users")
def list_users(authorization: Optional[str] = Header(default=None)) -> Dict[str, Any]:
    _check_auth(authorization)
    sb = _require_supabase()
    rows = sb.table("mission_users").select("*").eq("is_active", True).order("sort_order").execute().data or []
    return {"count": len(rows), "items": rows}


@router.post("/mission-users")
def create_user(payload: UserCreate, authorization: Optional[str] = Header(default=None)) -> Dict[str, Any]:
    _check_auth(authorization)
    sb = _require_supabase()
    data = payload.model_dump(exclude_none=True)
    data["slug"] = data["slug"].lower().strip()
    result = sb.table("mission_users").upsert(data, on_conflict="slug").execute()
    rows = result.data or []
    return rows[0] if rows else data


@router.patch("/mission-users/{slug}")
def update_user(slug: str, payload: UserUpdate, authorization: Optional[str] = Header(default=None)) -> Dict[str, Any]:
    _check_auth(authorization)
    sb = _require_supabase()
    update = {k: v for k, v in payload.model_dump(exclude_none=True).items()}
    if not update:
        raise HTTPException(status_code=400, detail="Nada pra atualizar")
    result = sb.table("mission_users").update(update).eq("slug", slug).execute()
    rows = result.data or []
    if not rows:
        raise HTTPException(status_code=404, detail="User nao encontrado")
    return rows[0]


# ---------------------------------------------------------------- settings

@router.get("/mission-settings")
def get_settings(authorization: Optional[str] = Header(default=None)) -> Dict[str, Any]:
    _check_auth(authorization)
    sb = _require_supabase()
    result = sb.table("mission_settings").select("*").eq("id", "singleton").limit(1).execute()
    rows = result.data or []
    if not rows:
        return {"id": "singleton", "logo_url": None, "client_options": []}
    return rows[0]


@router.patch("/mission-settings")
def update_settings(payload: SettingsUpdate, authorization: Optional[str] = Header(default=None)) -> Dict[str, Any]:
    _check_auth(authorization)
    sb = _require_supabase()
    update = {k: v for k, v in payload.model_dump(exclude_none=True).items()}
    update["updated_at"] = datetime.utcnow().isoformat()
    sb.table("mission_settings").upsert({"id": "singleton", **update}, on_conflict="id").execute()
    return get_settings(authorization)

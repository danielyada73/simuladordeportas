"""
Wrapper fino do Supabase. So o que a gente realmente usa.

Variaveis necessarias:
    SUPABASE_URL=https://xxxxx.supabase.co
    SUPABASE_SERVICE_KEY=eyJ...   (service_role key, nao a anon)
"""

from __future__ import annotations

import os
from typing import Any, Dict, Optional

_CLIENT = None


def get_client():
    """Retorna client Supabase singleton. Levanta se nao configurado."""
    global _CLIENT
    if _CLIENT is not None:
        return _CLIENT

    url = (os.getenv("SUPABASE_URL") or "").strip()
    key = (os.getenv("SUPABASE_SERVICE_KEY") or "").strip()
    if not url or not key:
        raise RuntimeError("SUPABASE_URL ou SUPABASE_SERVICE_KEY ausente")

    try:
        from supabase import create_client
    except ImportError as exc:
        raise RuntimeError("Pacote supabase nao instalado. pip install supabase") from exc

    _CLIENT = create_client(url, key)
    return _CLIENT


def is_configured() -> bool:
    return bool((os.getenv("SUPABASE_URL") or "").strip() and (os.getenv("SUPABASE_SERVICE_KEY") or "").strip())


def upsert_snapshot(kind: str, payload: Dict[str, Any], item_count: int, duration_ms: int, status: str, error: Optional[str] = None) -> None:
    from datetime import datetime, timezone
    sb = get_client()
    sb.table("monday_snapshot").upsert(
        {
            "kind": kind,
            "payload": payload,
            "item_count": item_count,
            "duration_ms": duration_ms,
            "status": status,
            "error": error,
            "last_synced_at": datetime.now(timezone.utc).isoformat(),
        },
        on_conflict="kind",
    ).execute()


def load_snapshot(kind: str) -> Optional[Dict[str, Any]]:
    sb = get_client()
    result = sb.table("monday_snapshot").select("*").eq("kind", kind).limit(1).execute()
    rows = result.data or []
    return rows[0] if rows else None

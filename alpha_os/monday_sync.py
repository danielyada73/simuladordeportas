"""
Sync Monday → Supabase.

Filosofia: uma chamada pesada no Monday a cada N minutos, salva tudo no Supabase.
Painel le do Supabase (instantaneo, zero consumo Monday).

Uso:
    # via API (POST /api/sync) ou direto:
    from alpha_os.monday_sync import sync_tasks_full
    result = sync_tasks_full()
"""

from __future__ import annotations

import time
import logging
from typing import Any, Dict

from . import monday_client
from . import supabase_client


logger = logging.getLogger(__name__)


SNAPSHOT_KIND_TASKS = "tasks_full"


def sync_tasks_full() -> Dict[str, Any]:
    """Sincroniza TODAS as tarefas (list_all_tasks) pro Supabase em uma transacao."""
    start = time.time()
    error_msg = None
    item_count = 0
    payload: Dict[str, Any] = {"tasks": []}

    try:
        # invalida cache local do monday_client pra forcar query nova
        monday_client._TASKS_CACHE = None
        monday_client._TASKS_CACHE_AT = 0.0
        monday_client._BOARDS_CACHE = None
        monday_client._BOARDS_CACHE_AT = 0.0
        monday_client._ITEMS_CACHE.clear()

        tasks = monday_client.list_all_tasks()
        item_count = len(tasks)
        payload = {"tasks": tasks, "fetched_at": time.time()}
        status = "ok"
    except Exception as exc:
        status = "error"
        error_msg = str(exc)[:500]
        logger.error("sync_tasks_full failed: %s", exc, exc_info=True)

    duration_ms = int((time.time() - start) * 1000)

    if supabase_client.is_configured():
        try:
            supabase_client.upsert_snapshot(
                kind=SNAPSHOT_KIND_TASKS,
                payload=payload,
                item_count=item_count,
                duration_ms=duration_ms,
                status=status,
                error=error_msg,
            )
        except Exception as exc:
            logger.error("Falha ao salvar snapshot no Supabase: %s", exc, exc_info=True)
            return {"status": "error", "stage": "supabase_upsert", "error": str(exc), "monday_status": status, "item_count": item_count}
    else:
        logger.warning("Supabase nao configurado; resultado nao foi persistido.")

    return {
        "status": status,
        "item_count": item_count,
        "duration_ms": duration_ms,
        "error": error_msg,
        "supabase_persisted": supabase_client.is_configured(),
    }


def load_cached_tasks() -> Dict[str, Any]:
    """Le snapshot mais recente do Supabase. Levanta se vazio."""
    if not supabase_client.is_configured():
        raise RuntimeError("Supabase nao configurado; nao da pra ler cache")
    snap = supabase_client.load_snapshot(SNAPSHOT_KIND_TASKS)
    if not snap:
        raise RuntimeError("Cache vazio. Rode POST /api/sync uma vez pra popular.")
    payload = snap.get("payload") or {}
    tasks = payload.get("tasks") or []
    return {
        "tasks": tasks,
        "last_synced_at": snap.get("last_synced_at"),
        "item_count": snap.get("item_count", len(tasks)),
        "status": snap.get("status"),
        "duration_ms": snap.get("duration_ms"),
    }

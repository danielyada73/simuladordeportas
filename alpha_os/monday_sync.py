"""
Sync Monday → Supabase.

Filosofia: uma chamada pesada no Monday a cada N minutos, salva tudo no Supabase.
Painel le do Supabase (instantaneo, zero consumo Monday).

Multi-token: tenta MONDAY_TOKEN_DANIEL, depois JEFFERSON, depois GUSTAVO,
e por fim MONDAY_API_TOKEN como fallback. Se um token estiver rate-limited,
passa pro proximo automaticamente.

Uso:
    from alpha_os.monday_sync import sync_tasks_full
    result = sync_tasks_full()
"""

from __future__ import annotations

import os
import time
import logging
from typing import Any, Dict, List, Tuple

from . import monday_client
from . import supabase_client


logger = logging.getLogger(__name__)


SNAPSHOT_KIND_TASKS = "tasks_full"


def _candidate_tokens() -> List[Tuple[str, str]]:
    """Retorna [(label, token)] em ordem de tentativa, sem duplicados."""
    pairs: List[Tuple[str, str]] = []
    seen: set[str] = set()
    for name in ("DANIEL", "JEFFERSON", "GUSTAVO"):
        token = os.getenv(f"MONDAY_TOKEN_{name}", "").strip()
        if token and token not in seen:
            pairs.append((name.capitalize(), token))
            seen.add(token)
    fallback = os.getenv("MONDAY_API_TOKEN", "").strip()
    if fallback and fallback not in seen:
        pairs.append(("default", fallback))
        seen.add(fallback)
    return pairs


def _clear_monday_cache() -> None:
    monday_client._TASKS_CACHE = None
    monday_client._TASKS_CACHE_AT = 0.0
    monday_client._BOARDS_CACHE = None
    monday_client._BOARDS_CACHE_AT = 0.0
    monday_client._ITEMS_CACHE.clear()


def _try_fetch_with_token(label: str, token: str) -> List[Dict[str, Any]]:
    original = os.environ.get("MONDAY_API_TOKEN", "")
    os.environ["MONDAY_API_TOKEN"] = token
    try:
        _clear_monday_cache()
        return monday_client.list_all_tasks()
    finally:
        if original:
            os.environ["MONDAY_API_TOKEN"] = original
        else:
            os.environ.pop("MONDAY_API_TOKEN", None)


def sync_tasks_full() -> Dict[str, Any]:
    """Sincroniza TODAS as tarefas (list_all_tasks) pro Supabase em uma transacao."""
    start = time.time()
    tokens = _candidate_tokens()

    if not tokens:
        result = {"status": "error", "error": "Nenhum token Monday configurado", "item_count": 0}
        _persist_result(result, start)
        return result

    tasks: List[Dict[str, Any]] = []
    error_msg = None
    used_token_label = None
    attempts: List[Dict[str, str]] = []

    for label, token in tokens:
        try:
            tasks = _try_fetch_with_token(label, token)
            used_token_label = label
            error_msg = None
            attempts.append({"token": label, "status": "ok"})
            break
        except Exception as exc:
            msg = str(exc)[:300]
            attempts.append({"token": label, "status": "error", "error": msg[:200]})
            error_msg = msg
            if "429" in msg or "Too Many Requests" in msg or "Daily limit" in msg:
                logger.warning("Token %s rate-limited, tentando proximo", label)
                continue
            logger.error("Token %s deu erro nao-recuperavel: %s", label, exc)
            break

    status = "ok" if tasks else "error"
    item_count = len(tasks)
    payload = {
        "tasks": tasks,
        "fetched_at": time.time(),
        "used_token": used_token_label,
        "attempts": attempts,
    }

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
            return {"status": "error", "stage": "supabase_upsert", "error": str(exc),
                    "monday_status": status, "item_count": item_count, "attempts": attempts}
    else:
        logger.warning("Supabase nao configurado; resultado nao foi persistido.")

    return {
        "status": status,
        "item_count": item_count,
        "duration_ms": duration_ms,
        "error": error_msg,
        "used_token": used_token_label,
        "attempts": attempts,
        "supabase_persisted": supabase_client.is_configured(),
    }


def _persist_result(result: Dict[str, Any], start_time: float) -> None:
    """Tenta persistir mesmo em caso de erro de configuracao."""
    if not supabase_client.is_configured():
        return
    try:
        supabase_client.upsert_snapshot(
            kind=SNAPSHOT_KIND_TASKS,
            payload={"tasks": [], "error": result.get("error")},
            item_count=0,
            duration_ms=int((time.time() - start_time) * 1000),
            status="error",
            error=result.get("error"),
        )
    except Exception as exc:
        logger.error("Falha ao persistir erro: %s", exc)


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

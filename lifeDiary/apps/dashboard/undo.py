from __future__ import annotations

import secrets
from datetime import datetime, timedelta


UNDO_SESSION_KEY = "dashboard_undo"
UNDO_TTL_SECONDS = 60
MAX_PENDING_SNAPSHOTS = 3


def save_snapshot(session, snapshot: dict, now: datetime) -> str:
    """스냅샷을 세션에 보관하고 토큰을 돌려준다.

    토큰을 전역 저장소가 아니라 세션에 두는 이유는 토큰만으로는 아무것도
    열리지 않게 하기 위해서다. 전역 저장소를 쓰면 토큰을 추측한 사람이 남의
    되돌리기를 재생할 수 있다.
    """
    stored = _sweep(session.get(UNDO_SESSION_KEY) or {}, now)

    token = secrets.token_urlsafe(16)
    stored[token] = {**snapshot, "created_at": now.isoformat()}

    session[UNDO_SESSION_KEY] = _evict_oldest(stored)
    return token


def pop_snapshot(session, token: str, now: datetime) -> dict | None:
    stored = session.get(UNDO_SESSION_KEY) or {}
    entry = stored.get(token)

    if entry is None or _is_expired(entry, now):
        session[UNDO_SESSION_KEY] = _sweep(stored, now)
        return None

    del stored[token]
    session[UNDO_SESSION_KEY] = _sweep(stored, now)

    return {key: value for key, value in entry.items() if key != "created_at"}


def _is_expired(entry: dict, now: datetime) -> bool:
    created_at = datetime.fromisoformat(entry["created_at"])
    return now - created_at >= timedelta(seconds=UNDO_TTL_SECONDS)


def _sweep(stored: dict, now: datetime) -> dict:
    return {
        token: entry for token, entry in stored.items() if not _is_expired(entry, now)
    }


def _evict_oldest(stored: dict) -> dict:
    if len(stored) <= MAX_PENDING_SNAPSHOTS:
        return stored

    by_age = sorted(stored.items(), key=lambda item: item[1]["created_at"])
    return dict(by_age[-MAX_PENDING_SNAPSHOTS:])

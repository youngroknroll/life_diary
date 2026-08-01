"""실행취소 스냅샷 보관소.

세션에 직전 상태를 담아 두고 짧은 시간 안에 한 번만 되돌릴 수 있게 한다.
세션 접근은 요청 관심사이므로 여기서 끝내고, 실제 복원은 use case가 맡는다.

보관 위치를 세션으로 두는 이유는 토큰이 그 자체로 권한이 되지 않게 하기
위해서다. 토큰만 알아도 열리는 전역 저장소를 쓰면 다른 사용자의 되돌리기를
재생할 수 있다.
"""

from __future__ import annotations

import secrets
from datetime import datetime, timedelta


UNDO_SESSION_KEY = "dashboard_undo"

# 되돌리기가 살아 있는 시간. 스낵바가 사라지는 시간과 맞춘다.
UNDO_TTL_SECONDS = 60

# 세션에 쌓아 둘 스냅샷 수. 탭을 여러 개 열어도 각자의 되돌리기가 살아 있되
# 세션 행이 무한정 커지지는 않도록 막는다.
MAX_PENDING_SNAPSHOTS = 3


def save_snapshot(session, snapshot: dict, now: datetime) -> str:
    """스냅샷을 보관하고 토큰을 돌려준다.

    토큰마다 별도 항목으로 담는다. 뒤이은 저장이 앞선 토큰을 조용히 덮어쓰면
    사용자가 되돌린다고 믿은 것과 실제로 되돌아가는 것이 어긋난다.
    """
    stored = _sweep(session.get(UNDO_SESSION_KEY) or {}, now)

    token = secrets.token_urlsafe(16)
    stored[token] = {**snapshot, "created_at": now.isoformat()}

    session[UNDO_SESSION_KEY] = _evict_oldest(stored)
    return token


def pop_snapshot(session, token: str, now: datetime) -> dict | None:
    """토큰에 해당하는 스냅샷을 꺼내고 지운다. 없거나 만료면 None."""
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

# services/activity.py
from datetime import datetime


async def log_activity(db, *, list_id: str, user_id: str, user_email: str, action: str, meta: dict | None = None):
    """
    Fire-and-forget activity record. Never raises — a logging failure must not
    break the actual request.
    """
    try:
        await db["activity_logs"].insert_one({
            "list_id": list_id,
            "user_id": user_id,
            "user_email": user_email,
            "action": action,
            "meta": meta or {},
            "created_at": datetime.utcnow(),
        })
    except Exception:
        pass

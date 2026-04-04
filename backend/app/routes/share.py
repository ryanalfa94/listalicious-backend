from fastapi import APIRouter, Depends, HTTPException
from app.database.database import get_database
from app.services.auth_service import get_current_user
from app.services.guards import ensure_list_owned
from app.schemas.share import ShareRequest, ShareResponse
from app.services import share_service
from app.services.activity import log_activity

router = APIRouter(prefix="/lists/{list_id}", tags=["Sharing"])

@router.post("/share", response_model=ShareResponse)
async def share_list(list_id: str, body: ShareRequest,
                     db=Depends(get_database), user=Depends(get_current_user)):
    # Only owner can share
    await ensure_list_owned(db, list_id, str(user["_id"]))

    # Resolve the email -> user_id
    target = await db["users"].find_one({"email": body.email}, {"_id": 1})
    if not target:
        raise HTTPException(status_code=404, detail="User not found")

    shared_with = await share_service.add_contributor(db, list_id, str(target["_id"]))
    await log_activity(db, list_id=list_id, user_id=str(user["_id"]), user_email=user["email"],
                       action="list_shared", meta={"shared_with_email": body.email})
    return {"list_id": list_id, "shared_with": shared_with}

@router.post("/unshare", response_model=ShareResponse)
async def unshare_list(list_id: str, body: ShareRequest,
                       db=Depends(get_database), user=Depends(get_current_user)):
    await ensure_list_owned(db, list_id, str(user["_id"]))
    target = await db["users"].find_one({"email": body.email}, {"_id": 1})
    if not target:
        raise HTTPException(status_code=404, detail="User not found")
    shared_with = await share_service.remove_contributor(db, list_id, str(target["_id"]))
    await log_activity(db, list_id=list_id, user_id=str(user["_id"]), user_email=user["email"],
                       action="list_unshared", meta={"unshared_email": body.email})
    return {"list_id": list_id, "shared_with": shared_with}

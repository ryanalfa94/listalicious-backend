# app/routes/account.py
from fastapi import APIRouter, Depends, status, HTTPException
from pydantic import BaseModel, ConfigDict, Field
from bson import ObjectId

from app.database.database import get_database
from app.services.auth_service import get_current_user, verify_password

router = APIRouter(prefix="/auth", tags=["Account"])


class DeleteAccountRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    password: str = Field(min_length=1)


@router.delete("/delete-account", status_code=status.HTTP_204_NO_CONTENT)
async def delete_account(
    body: DeleteAccountRequest,
    db = Depends(get_database),
    user = Depends(get_current_user),
):
    """
    Hard-delete the user and all of their data:
      - verify password (the typed "DELETE" confirmation is a UI-only guard, not a security boundary)
      - revoke tokens (token_version++)
      - delete items for lists they own
      - delete lists they own
      - remove them from other lists' shared_with
      - delete the user doc
    """
    if not verify_password(body.password, user.get("hashed_password", "")):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Password is incorrect")

    user_id = str(user["_id"])

    # 1) revoke tokens now
    await db["users"].update_one({"_id": ObjectId(user_id)}, {"$inc": {"token_version": 1}})

    # 2) cascade delete: list -> items -> list docs
    cursor = db["grocery_lists"].find({"owner_id": user_id}, {"_id": 1})
    owned_list_ids = [str(doc["_id"]) async for doc in cursor]

    if owned_list_ids:
        await db["items"].delete_many({"list_id": {"$in": owned_list_ids}})
    await db["grocery_lists"].delete_many({"owner_id": user_id})

    # 3) remove from other lists' shared_with
    await db["grocery_lists"].update_many(
        {"shared_with": user_id},
        {"$pull": {"shared_with": user_id}}
    )

    # 4) delete user record
    await db["users"].delete_one({"_id": ObjectId(user_id)})

    return

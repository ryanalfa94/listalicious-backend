# routes/list.py
from fastapi import APIRouter, Depends, Query, status, HTTPException
from app.database.database import get_database
from app.services.auth_service import get_current_user
from app.services.guards import ensure_list_access, ensure_list_owned, require_verified_email
from app.services import list_service
from app.schemas.list import GroceryListCreate, GroceryListResponse, GroceryListUpdate

router = APIRouter(prefix="/lists", tags=["Lists"])


@router.post("", response_model=GroceryListResponse, status_code=status.HTTP_201_CREATED)
async def create_list(list_data: GroceryListCreate, current_user: dict = Depends(require_verified_email)):
    return await list_service.create_grocery_list(
        title=list_data.title,
        owner_id=str(current_user["_id"])
    )


@router.get("", response_model=list[GroceryListResponse])
async def get_lists(
    skip: int = Query(0, ge=0, description="Number of lists to skip"),
    limit: int = Query(50, ge=1, le=100, description="Max lists to return"),
    db=Depends(get_database),
    user=Depends(get_current_user),
):
    return await list_service.get_my_lists(db, str(user["_id"]), skip=skip, limit=limit)


@router.get("/{list_id}", response_model=GroceryListResponse)
async def get_single_list(list_id: str, db=Depends(get_database), user=Depends(get_current_user)):
    await ensure_list_access(db, list_id, str(user["_id"]))
    doc = await list_service.get_list(db, list_id)
    if not doc:
        raise HTTPException(status_code=404, detail="List not found")
    return doc


@router.put("/{list_id}", response_model=GroceryListResponse)
async def update_list(list_id: str, payload: GroceryListUpdate,
                      db=Depends(get_database), user=Depends(get_current_user)):
    await ensure_list_owned(db, list_id, str(user["_id"]))
    updated = await list_service.update_list(db, list_id, payload.model_dump(exclude_unset=True))
    return updated


@router.delete("/{list_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_list(list_id: str, db=Depends(get_database), user=Depends(get_current_user)):
    await ensure_list_owned(db, list_id, str(user["_id"]))
    await list_service.delete_list(db, list_id)
    return

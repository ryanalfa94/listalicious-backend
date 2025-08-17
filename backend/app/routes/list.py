from fastapi import APIRouter, Depends, status
from app.schemas.list import GroceryListCreate, GroceryListResponse
from app.services.auth_service import get_current_user
from app.services import list_service

router = APIRouter()

@router.post("/lists", response_model=GroceryListResponse, status_code=status.HTTP_201_CREATED)
async def create_list(
    list_data: GroceryListCreate,
    current_user: dict = Depends(get_current_user)
):
    created_list = await list_service.create_grocery_list(
        title=list_data.title,
        owner_id=str(current_user["_id"])
    )
    return created_list

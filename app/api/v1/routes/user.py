from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_db
from app.repositories import user_repository
from app.schemas.user import UserListResponse, UserResponse

router = APIRouter(prefix="/users", tags=["users"])


@router.get("", response_model=UserListResponse)
async def list_users(db: AsyncSession = Depends(get_db)):
    """List all registered users."""
    users = await user_repository.get_all_users(db)
    return UserListResponse(total=len(users), users=users)


@router.get("/{employee_id}", response_model=UserResponse)
async def get_user_by_employee_id(
    employee_id: str, db: AsyncSession = Depends(get_db)
):
    """Get a user by their unique employee ID."""
    user = await user_repository.get_user_by_employee_id(db, employee_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.delete("/{employee_id}", status_code=204)
async def delete_user(employee_id: str, db: AsyncSession = Depends(get_db)):
    """Delete a user and all associated face encodings by employee ID."""
    deleted = await user_repository.delete_user_by_employee_id(db, employee_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="User not found")
    await db.commit()

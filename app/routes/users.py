from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.user_repo import UserRepository
from app.core.db import get_db

router = APIRouter(prefix="/users", tags=["Users"])

class UserCreateRequest(BaseModel):
    email: str
    password: str
    diet_type: list[str] | None = None
    allergies: list[str] | None = None
    dislikes: list[str] | None = None



# Add the user data and preferences with the same endpoint, save to 2 tables: user and user_prefs
@router.post("/")
async def create_user(data: UserCreateRequest, db: AsyncSession = Depends(get_db)):
    repo = UserRepository(db)
    return await repo.create_user_with_prefs(
        email=data.email, 
        password=data.password,
        diet_type=data.diet_type,
        allergies=data.allergies,
        dislikes=data.dislikes,
        )

@router.get("/")
async def list_users(db: AsyncSession = Depends(get_db)):
    repo = UserRepository(db)
    return await repo.list_users()

@router.get("/{user_id}/prefs")
async def get_user_prefs(user_id: int, db: AsyncSession = Depends(get_db)):
    repo = UserRepository(db)
    return await repo.get_user_prefs(user_id)

"""@router.post("/{user_id}/update-prefs")
async def update_user_prefs(data: UserPrefsUpdateRequest, user_id: int, db: AsyncSession = Depends(get_db)):
    repo = UserRepository(db)
    return await repo.update_prefs(
        user_id=user_id,
        diet_type=list(data.diet_type or []),
        allergies=list(data.allergies or []),
        dislikes=list(data.dislikes or []),
        )
"""

class UserPrefsReplaceRequest(BaseModel):
    diet_type: list[str] | None = None
    allergies: list[str] | None = None
    dislikes: list[str] | None = None

# PUT — Replace all preferences
@router.put("/{user_id}/prefs")
async def replace_user_prefs(user_id: int, data: UserPrefsReplaceRequest, db: AsyncSession = Depends(get_db)):
    repo = UserRepository(db)
    return await repo.replace_user_prefs(
        user_id=user_id,
        diet_type=data.diet_type,
        allergies=data.allergies,
        dislikes=data.dislikes,
    )

class UserPrefsPatchRequest(BaseModel):
    add: dict[str, list[str]] | None = None
    remove: dict[str, list[str]] | None = None

# 3️⃣ PATCH — Add or remove items
@router.patch("/{user_id}/prefs")
async def patch_user_prefs(user_id: int, data: UserPrefsPatchRequest, db: AsyncSession = Depends(get_db)):
    repo = UserRepository(db)
    return await repo.patch_user_prefs(
        user_id=user_id,
        add=data.add,
        remove=data.remove,
    )

# 4️⃣ DELETE — Clear all preferences
@router.delete("/{user_id}/prefs")
async def clear_user_prefs(user_id: int, db: AsyncSession = Depends(get_db)):
    repo = UserRepository(db)
    return await repo.clear_user_prefs(user_id)

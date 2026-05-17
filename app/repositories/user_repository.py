import numpy as np
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import FaceEncoding, User


async def get_user_by_employee_id(db: AsyncSession, employee_id: str) -> User | None:
    result = await db.execute(select(User).where(User.employee_id == employee_id))
    return result.scalar_one_or_none()


async def create_user(db: AsyncSession, name: str, employee_id: str) -> User:
    user = User(name=name, employee_id=employee_id)
    db.add(user)
    await db.flush()
    return user


async def save_encoding(db: AsyncSession, user_id: int, embedding: np.ndarray) -> None:
    db.add(FaceEncoding(user_id=user_id, encoding=embedding.astype(np.float64).tobytes()))


async def get_all_encodings(db: AsyncSession) -> list[tuple[int, np.ndarray]]:
    result = await db.execute(select(FaceEncoding))
    return [
        (row.user_id, np.frombuffer(row.encoding, dtype=np.float64))
        for row in result.scalars().all()
    ]


async def get_user_by_id(db: AsyncSession, user_id: int) -> User | None:
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


async def get_all_users(db: AsyncSession) -> list[User]:
    result = await db.execute(select(User).order_by(User.id))
    return list(result.scalars().all())


async def delete_user_by_employee_id(db: AsyncSession, employee_id: str) -> bool:
    user = await get_user_by_employee_id(db, employee_id)
    if user is None:
        return False
    await db.delete(user)
    return True

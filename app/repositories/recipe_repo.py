from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from passlib.hash import bcrypt
from app.core.sql_loader import load_query

class RecipeRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_top_recipes_by_cuisine(self, cuisine: str):
        sql = load_query("recipe_metadata.sql")
        result = await self.db.execute(text(sql), {"cuisine": f"%{cuisine}%"})
        return result.mappings().all()

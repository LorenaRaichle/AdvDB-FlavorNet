from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text, Integer
from passlib.hash import bcrypt
from app.core.sql_loader import load_query
from sqlalchemy import bindparam
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy import String
from fastapi import HTTPException

class UserRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_user_with_prefs(self, email, password, diet_type, allergies, dislikes):
        user_sql = load_query("insert_user.sql")
        pref_sql = load_query("insert_user_prefs.sql")

        async with self.db.begin():
            user_result = await self.db.execute(
                text(user_sql),
                {"email": email, "password_hash": bcrypt.hash(password)},
            )
            user = user_result.mappings().first()
            user_id = user["user_id"]

            # param needs to be bound with correct type for ARRAY
            await self.db.execute(
                text(pref_sql).bindparams(
                    bindparam("diet_type", type_=ARRAY(String)),
                    bindparam("allergies", type_=ARRAY(String)),
                    bindparam("dislikes", type_=ARRAY(String)),
                ),
                {
                    "user_id": user_id,
                    "diet_type": diet_type,
                    "allergies": allergies,
                    "dislikes": dislikes,
                },
            )

        return user

    async def get_user_prefs(self, user_id: int):
        sql = load_query("select_user_prefs.sql")
        result = await self.db.execute(text(sql), {"user_id": user_id})
        return result.mappings().first()

    async def list_users(self):
        sql = load_query("select_users.sql")
        result = await self.db.execute(text(sql))
        return result.mappings().all()

    # todo: delete later if not used
    async def update_prefs(self, user_id: int, diet_type=None, allergies=None, dislikes=None):
        # Build dynamic update set clauses
        fields = []
        params = {"user_id": user_id}

        if diet_type is not None:
            fields.append("diet_type = :diet_type")
            params["diet_type"] = diet_type
        if allergies is not None:
            fields.append("allergies = :allergies")
            params["allergies"] = allergies
        if dislikes is not None:
            fields.append("dislikes = :dislikes")
            params["dislikes"] = dislikes

        if not fields:
            # No updates provided
            return {"message": "No fields to update"}

        # Build SQL dynamically
        sql = f"""
        UPDATE user_prefs
        SET {', '.join(fields)}, updated_at = CURRENT_TIMESTAMP
        WHERE user_id = :user_id
        RETURNING *;
        """

        result = await self.db.execute(
            text(sql).bindparams(
                bindparam("diet_type", type_=ARRAY(String), required=False),
                bindparam("allergies", type_=ARRAY(String), required=False),
                bindparam("dislikes", type_=ARRAY(String), required=False),
            ),
            params,
        )
        await self.db.commit()
        return result.mappings().first()


    async def replace_user_prefs(self, user_id: int, diet_type, allergies, dislikes):
        sql = """
        UPDATE user_prefs
        SET 
            diet_type = CAST(:diet_type AS TEXT[]),
            allergies = CAST(:allergies AS TEXT[]),
            dislikes = CAST(:dislikes AS TEXT[]),
            updated_at = CURRENT_TIMESTAMP
        WHERE user_id = :user_id
        RETURNING *;
        """
        result = await self.db.execute(text(sql), {
            "user_id": user_id,
            "diet_type": diet_type or [],
            "allergies": allergies or [],
            "dislikes": dislikes or []
        })
        await self.db.commit()
        return result.mappings().first()

    async def patch_user_prefs(self, user_id: int, add: dict | None = None, remove: dict | None = None):
        # First fetch current prefs
        result = await self.db.execute(text("SELECT * FROM user_prefs WHERE user_id = :user_id"), {"user_id": user_id})
        current = result.mappings().first()
        if not current:
            raise HTTPException(status_code=404, detail="User not found")

        def modify(field, current_list):
            current_set = set(current_list or [])
            if add and field in add:
                current_set |= set(add[field])
            if remove and field in remove:
                current_set -= set(remove[field])
            return list(current_set)

        updated = {
            "diet_type": modify("diet_type", current["diet_type"]),
            "allergies": modify("allergies", current["allergies"]),
            "dislikes": modify("dislikes", current["dislikes"]),
        }

        sql = """
        UPDATE user_prefs
        SET 
            diet_type = CAST(:diet_type AS TEXT[]),
            allergies = CAST(:allergies AS TEXT[]),
            dislikes = CAST(:dislikes AS TEXT[]),
            updated_at = CURRENT_TIMESTAMP
        WHERE user_id = :user_id
        RETURNING *;
        """
        result = await self.db.execute(text(sql), {**updated, "user_id": user_id})
        await self.db.commit()
        return result.mappings().first()

    async def clear_user_prefs(self, user_id: int):
        sql = """
        UPDATE user_prefs
        SET diet_type = '{}', allergies = '{}', dislikes = '{}', updated_at = CURRENT_TIMESTAMP
        WHERE user_id = :user_id
        RETURNING *;
        """
        result = await self.db.execute(text(sql), {"user_id": user_id})
        await self.db.commit()
        return result.mappings().first()

import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from db.postrges_db.psql import get_db

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/")
async def auth(db: AsyncSession = Depends(get_db)):
    try:
        result = await db.execute(text("SELECT 1"))
        value = result.scalar()
        return {"res": value, "msg": "Database connection is working!"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

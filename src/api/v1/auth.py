import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from db.casher import AbstractCache, get_cacher
from db.postrges_db.psql import get_db

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/")
async def auth(
    db: AsyncSession = Depends(get_db),
    cacher: AbstractCache = Depends(get_cacher),
):
    try:
        result = await db.execute(text("SELECT 1"))
        await cacher.set("Try", "probe", 180)
        data = await cacher.get("Try")
        value = result.scalar()
        return {
            "res": value,
            "msg": "Database connection is working!",
            "from_cache": data,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

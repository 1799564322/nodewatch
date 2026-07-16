from typing import Literal

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.api.deps import DbSession

router = APIRouter(prefix="/health", tags=["health"])


class LiveResponse(BaseModel):
    status: Literal["ok"]
    service: Literal["nodewatch"]


class ReadyResponse(BaseModel):
    status: Literal["ready"]
    database: Literal["ok"]
    migration: str


@router.get("/live", response_model=LiveResponse)
def live() -> LiveResponse:
    """确认应用进程可以响应，不访问数据库或外部服务。"""
    return LiveResponse(status="ok", service="nodewatch")


@router.get("/ready", response_model=ReadyResponse)
def ready(session: DbSession) -> ReadyResponse:
    try:
        session.execute(text("SELECT 1"))
        revision = session.scalar(text("SELECT version_num FROM alembic_version"))
    except SQLAlchemyError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="服务尚未准备好"
        ) from exc
    if not revision:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="数据库迁移未完成"
        )
    return ReadyResponse(status="ready", database="ok", migration=str(revision))

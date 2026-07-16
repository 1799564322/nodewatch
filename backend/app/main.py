from contextlib import asynccontextmanager
import os
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.trustedhost import TrustedHostMiddleware

from app.api.v1.auth import router as auth_router
from app.api.v1.agent import router as agent_router
from app.api.v1.alerts import router as alerts_router
from app.api.v1.devices import dashboard_router, router as devices_router
from app.api.v1.health import router as health_router
from app.core.config import get_settings
from app.core.logging import configure_logging
from app.core.middleware import RequestIdMiddleware
from app.db.session import session_scope
from app.services.bootstrap import bootstrap_admin
from app.services.alerts import bootstrap_alert_rules
from app.services.scheduler import start_scheduler


@asynccontextmanager
async def lifespan(_: FastAPI):
    configure_logging()
    with session_scope() as session:
        bootstrap_admin(session)
        bootstrap_alert_rules(session)
    scheduler = start_scheduler()
    yield
    if scheduler:
        scheduler.shutdown(wait=False)

app = FastAPI(title="NodeWatch API", version="0.1.0", lifespan=lifespan)
app.add_middleware(RequestIdMiddleware)
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=[
        host.strip() for host in get_settings().allowed_hosts.split(",") if host.strip()
    ],
)
app.include_router(health_router, prefix="/api/v1")
app.include_router(auth_router, prefix="/api/v1")
app.include_router(devices_router, prefix="/api/v1")
app.include_router(dashboard_router, prefix="/api/v1")
app.include_router(agent_router, prefix="/api/v1")
app.include_router(alerts_router, prefix="/api/v1")

static_dir = Path(
    os.getenv("NODEWATCH_STATIC_DIR", Path(__file__).resolve().parent.parent / "static")
).resolve()
if static_dir.joinpath("index.html").is_file():
    assets_dir = static_dir / "assets"
    if assets_dir.is_dir():
        app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

    @app.get("/{full_path:path}", include_in_schema=False)
    def frontend(full_path: str) -> FileResponse:
        if full_path.startswith("api/"):
            raise HTTPException(status_code=404)
        candidate = (static_dir / full_path).resolve()
        if static_dir in candidate.parents and candidate.is_file():
            return FileResponse(candidate)
        return FileResponse(static_dir / "index.html")

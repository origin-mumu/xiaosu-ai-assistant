from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from xiaosu.api.documents import router as documents_router
from xiaosu.api.health import router as health_router
from xiaosu.api.mock import router as mock_router
from xiaosu.core.config import get_settings
from xiaosu.core.logging import setup_logging
from xiaosu.core.middleware import RequestContextMiddleware
from xiaosu.db.session import close_database, init_database


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    setup_logging(settings.log_dir)
    await init_database()
    yield
    await close_database()


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="小苏企业智能助手 API",
        version="0.1.0",
        description="知识库、Agent、钉钉机器人和管理后台的统一后端服务。",
        lifespan=lifespan,
    )
    app.add_middleware(RequestContextMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[settings.web_origin],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(health_router, prefix="/api/v1")
    app.include_router(documents_router, prefix="/api/v1")
    app.include_router(mock_router, prefix="/api/v1")
    return app


app = create_app()

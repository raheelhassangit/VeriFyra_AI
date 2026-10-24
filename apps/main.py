import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request

from app.agents import default_agents
from app.api.internal import router
from app.config import Settings
from app.logging_config import configure_logging
from app.services.gemma import GemmaClient
from app.services.runs import RunManager


def create_app(settings: Settings | None = None, agents=None, gemma=None) -> FastAPI:
    settings = settings or Settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        if not logging.getLogger().handlers:
            configure_logging()
        if len(settings.agent_service_token) < 32:
            raise RuntimeError("AGENT_SERVICE_TOKEN must be set to at least 32 characters.")
        settings.agent_work_dir.mkdir(parents=True, exist_ok=True)
        app.state.settings = settings
        app.state.runs = RunManager(settings, agents if agents is not None else default_agents(),
                                    gemma or GemmaClient(settings))
        yield
        await app.state.runs.shutdown()

    app = FastAPI(title="VeriFyra Agent Service", version="1.0.0", lifespan=lifespan)
    app.include_router(router)

    @app.get("/health/", tags=["health"])
    async def health(request: Request):
        return {
            "status": "ok",
            "model_configured": bool(request.app.state.settings.ollama_api_key),
            "active_audits": request.app.state.runs.active_count(),
        }

    return app
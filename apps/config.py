from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT = Path(__file__).resolve().parents[2]  # same .env as Django


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=ROOT / ".env", extra="ignore")

    agent_service_token: str = ""

    ollama_api_key: str = ""
    ollama_base_url: str = "https://ollama.com"
    ollama_model: str = "gemma4:31b"
    ollama_timeout: float = 120
    ollama_max_retries: int = 3

    agent_max_concurrent_audits: int = 2
    agent_max_pending_audits: int = 20
    agent_max_audit_seconds: float = 1500
    agent_max_doc_bytes: int = 5 * 1024 * 1024
    agent_run_ttl_seconds: float = 3600
    agent_work_dir: Path = ROOT / "tmp_audits"
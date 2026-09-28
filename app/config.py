from __future__ import annotations

from pathlib import Path

from sqlalchemy.engine import URL, make_url
from pydantic_settings import BaseSettings, SettingsConfigDict

# Absolute path, not "./.env" -- a relative path only resolves correctly if
# the process's cwd happens to be this project's root, which isn't
# guaranteed when this is launched as a subprocess (e.g. by Claude
# Desktop's local mcpServers config).
_ENV_FILE = Path(__file__).resolve().parent.parent / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=_ENV_FILE, env_file_encoding="utf-8", extra="ignore")

    database_url: str
    database_url_ro: str | None = None
    mcp_server_name: str = "Rustler"
    log_level: str = "INFO"

    def _base_url(self) -> URL:
        raw = self.database_url_ro or self.database_url
        url = make_url(raw)
        if url.drivername in ("postgres", "postgresql"):
            url = url.set(drivername="postgresql+asyncpg")
        return url

    @property
    def resolved_database_url(self) -> str:
        """DB URL normalized to the asyncpg driver, with libpq-only query
        params (sslmode, channel_binding -- common in Neon connection
        strings) stripped out. asyncpg's connect() rejects those as
        unexpected keyword arguments; TLS is requested instead via
        `asyncpg_connect_args`, passed separately to create_async_engine."""
        url = self._base_url()
        query = dict(url.query)
        query.pop("sslmode", None)
        query.pop("channel_binding", None)
        return url.set(query=query).render_as_string(hide_password=False)

    @property
    def asyncpg_connect_args(self) -> dict:
        """Translate a libpq-style sslmode (if present) into what asyncpg's
        connect() actually accepts. Neon requires TLS, so this defaults to
        "require" even if the URL didn't specify sslmode explicitly."""
        sslmode = self._base_url().query.get("sslmode", "require")
        if sslmode == "disable":
            return {}
        return {"ssl": sslmode}


settings = Settings()

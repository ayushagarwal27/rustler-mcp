from __future__ import annotations

from fastapi import FastAPI

from app.mcp_server import mcp

# FastMCP's ASGI app for the streamable-HTTP transport. path="/" so that
# mounting it under "/mcp" below makes the final endpoint exactly "/mcp".
mcp_app = mcp.http_app(path="/")

# FastMCP's app owns some startup/shutdown state (the MCP session manager),
# so its lifespan must be passed through to FastAPI or the mounted app
# will fail on first request.
app = FastAPI(title="Rustler MCP", lifespan=mcp_app.lifespan)

app.mount("/mcp", mcp_app)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}

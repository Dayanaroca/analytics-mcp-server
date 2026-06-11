import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

from src.config import Settings
from src.logging_util import configure_logging
from src.mcp_instance import mcp
from src.utils.exceptions import validation_exception_handler
from src.utils.security import MaxBodySizeMiddleware

Settings.HOSTED_LOCATION = Settings.CONSTANT_LOCAL_HOSTED_LOCATION

import src.tools  # Registers MCP tools.

configure_logging(
    level="INFO",
    console_level="INFO",
    file_level="INFO",
    log_file="app.log",
    max_bytes=5 * 1024 * 1024,
    backup_count=3,
    library_levels={
        "docket": "WARNING",
        "mcp": "WARNING",
        "httpx": "WARNING",
    },
)


mcp_server = mcp.http_app(transport="streamable-http", path="/")


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with mcp_server.lifespan(app):
        yield


def create_app() -> FastAPI:
    app = FastAPI(lifespan=lifespan)
    app.add_middleware(
        MaxBodySizeMiddleware,
        max_body_size=1 * 1024 * 1024,
    )
    app.add_exception_handler(RequestValidationError, validation_exception_handler)

    @app.get("/")
    async def health():
        return JSONResponse({"status": "ok", "mcp_path": "/mcp"})

    app.mount("/mcp", mcp_server)
    return app


app = create_app()


def main():
    uvicorn.run(app, host="0.0.0.0", port=Settings.PORT)


if __name__ == "__main__":
    main()

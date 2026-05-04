from __future__ import annotations

import os
from copy import deepcopy
from pathlib import Path

import uvicorn
from uvicorn.config import LOGGING_CONFIG as UVICORN_LOGGING_CONFIG


def _uvicorn_log_config() -> dict:
    """Force Docker-friendly logging: no TTY colors; access lines on stderr (easier to tail in Compose)."""
    cfg = deepcopy(UVICORN_LOGGING_CONFIG)
    cfg["handlers"]["access"]["stream"] = "ext://sys.stderr"
    for key in ("default", "access"):
        fmt = cfg["formatters"].get(key)
        if isinstance(fmt, dict):
            fmt["use_colors"] = False
    return cfg


def _truthy(name: str, *, default: bool = False) -> bool:
    v = os.environ.get(name)
    if v is None:
        return default
    return v.strip().lower() in ("1", "true", "yes", "on")


def main() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    api_src = repo_root / "apps" / "backend" / "src"
    reload = os.environ.get("UVICORN_RELOAD", "true").lower() in ("1", "true", "yes")
    log_level = os.environ.get("UVICORN_LOG_LEVEL", "info").strip().lower()
    # Default True so Docker logs each request (`INFO: ... "GET ..." ...`).
    access_log = _truthy("UVICORN_ACCESS_LOG", default=True)
    use_colors = _truthy("UVICORN_USE_COLORS", default=False)

    uvicorn.run(
        "semantic_reasoning_agent.main:app",
        host="0.0.0.0",
        port=8000,
        reload=reload,
        app_dir=str(api_src),
        log_config=_uvicorn_log_config(),
        log_level=log_level,
        access_log=access_log,
        use_colors=use_colors,
    )


if __name__ == "__main__":
    main()

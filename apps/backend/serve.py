from __future__ import annotations

import os
from pathlib import Path

import uvicorn


def main() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    api_src = repo_root / "apps" / "backend" / "src"
    reload = os.environ.get("UVICORN_RELOAD", "true").lower() in ("1", "true", "yes")
    uvicorn.run(
        "semantic_reasoning_agent.main:app",
        host="0.0.0.0",
        port=8000,
        reload=reload,
        app_dir=str(api_src),
    )


if __name__ == "__main__":
    main()

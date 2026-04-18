from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


def main() -> int:
    repo_root = Path(__file__).resolve().parents[2]
    api_src = repo_root / "apps" / "backend" / "src"
    env = os.environ.copy()
    pythonpath = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = f"{api_src}{os.pathsep}{pythonpath}" if pythonpath else str(api_src)
    cmd = [
        sys.executable,
        "-m",
        "celery",
        "-A",
        "semantic_reasoning_agent.celery_app.celery_app",
        "worker",
        "--uid",
        "nobody",
        "--gid",
        "nogroup",
        "--loglevel",
        "INFO",
        "--pool",
        "solo",
    ]
    return subprocess.call(cmd, env=env)


if __name__ == "__main__":
    raise SystemExit(main())

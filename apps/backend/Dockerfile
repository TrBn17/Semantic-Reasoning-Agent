# syntax=docker/dockerfile:1

FROM python:3.11-slim

WORKDIR /workspace

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies first to maximize Docker layer cache hits.
# This layer is rebuilt only when dependency declarations change.
COPY pyproject.toml /tmp/pyproject.toml
# Persist pip download cache across builds (BuildKit). Layer still caches on unchanged pyproject.toml.
RUN --mount=type=cache,target=/root/.cache/pip \
    python -c "import tomllib, pathlib; p = pathlib.Path('/tmp/pyproject.toml'); data = tomllib.loads(p.read_text(encoding='utf-8')); deps = data.get('project', {}).get('dependencies', []); dev = data.get('project', {}).get('optional-dependencies', {}).get('dev', []); pathlib.Path('/tmp/requirements-docker.txt').write_text('\n'.join(deps + dev) + '\n', encoding='utf-8')" \
    && pip install -r /tmp/requirements-docker.txt

# Copy project files (build context is repo root)
COPY . .

# Install the local package (deps already installed above). --no-deps keeps builds fast when only code changed.
RUN pip install --no-deps -e .

# No entrypoint, let docker-compose handle it


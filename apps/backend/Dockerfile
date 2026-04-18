FROM python:3.11-slim

WORKDIR /workspace

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy project files (build context is root project)
COPY . .

# Install Python dependencies
RUN pip install --no-cache-dir -e '.[dev]'

# No entrypoint, let docker-compose handle it


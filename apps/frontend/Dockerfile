FROM node:20-alpine

WORKDIR /workspace/apps/frontend
ENV NEXT_TELEMETRY_DISABLED=1

# Minimal dev image.
# Source code and node_modules are mounted by docker-compose, and dependencies
# are installed by the container command at runtime.
RUN apk add --no-cache libc6-compat

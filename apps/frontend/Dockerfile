FROM node:20-alpine

WORKDIR /workspace

# Copy root level package files (nếu có monorepo)
COPY package*.json ./

# Copy frontend package files
COPY apps/frontend/package*.json ./apps/frontend/

# Install dependencies
RUN cd apps/frontend && npm install

# Copy entire codebase
COPY . .

# Dev mode sẽ chạy từ docker-compose command

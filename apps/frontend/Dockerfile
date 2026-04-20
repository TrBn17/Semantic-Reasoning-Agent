FROM node:20-alpine

WORKDIR /app
ENV NEXT_TELEMETRY_DISABLED=1

# Copy only frontend package files
COPY apps/frontend/package*.json ./

# Install dependencies
RUN npm install

# Copy frontend source code  
COPY apps/frontend/ ./

# Dev mode sẽ chạy từ docker-compose command

FROM node:20-alpine AS deps

WORKDIR /app
ENV NEXT_TELEMETRY_DISABLED=1

RUN apk add --no-cache libc6-compat

COPY apps/frontend/package.json apps/frontend/package-lock.json ./
RUN npm ci

FROM node:20-alpine AS builder

WORKDIR /app
ENV NEXT_TELEMETRY_DISABLED=1

RUN apk add --no-cache libc6-compat

COPY --from=deps /app/node_modules ./node_modules
COPY apps/frontend ./

RUN npm run build

FROM node:20-alpine AS runner

WORKDIR /app
ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1

RUN apk add --no-cache libc6-compat

COPY --from=builder /app/package.json ./package.json
COPY --from=builder /app/public ./public
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/.next ./.next

EXPOSE 3000

CMD ["npm", "run", "start"]

# Build context: repository root (see docker-compose.yml)
FROM node:24-bookworm-slim AS deps
WORKDIR /app/frontend
COPY frontend/package.json frontend/package-lock.json ./
# package-lock.json is out of sync with the "sharp" override in package.json, so `npm ci` refuses it
RUN npm install --no-audit --no-fund

FROM deps AS build
COPY frontend/ ./
ARG NEXT_PUBLIC_API_URL=/api/bff
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL NEXT_TELEMETRY_DISABLED=1
RUN npm run build

FROM node:24-bookworm-slim
WORKDIR /app/frontend
ENV NODE_ENV=production NEXT_TELEMETRY_DISABLED=1 PORT=3000
COPY --from=build /app/frontend ./
# Better Auth CLI (migrations) and tsx (scripts/seed-admin.ts) are baked in so first boot needs no network.
# The CLI must match the installed better-auth exactly, otherwise it migrates a different schema.
RUN npm install -g --no-audit --no-fund "auth@$(node -p 'require("./node_modules/better-auth/package.json").version')" tsx@4.23.15 \
 && npm cache clean --force
COPY docker/frontend-entrypoint.sh /usr/local/bin/freedom-frontend-entrypoint
RUN chmod +x /usr/local/bin/freedom-frontend-entrypoint
EXPOSE 3000
CMD ["freedom-frontend-entrypoint"]

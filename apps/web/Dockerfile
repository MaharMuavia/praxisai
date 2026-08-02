FROM node:22.16.0-bookworm-slim AS dependencies
WORKDIR /workspace
COPY package.json package-lock.json ./
COPY apps/web/package.json apps/web/package.json
COPY packages/api-client/package.json packages/api-client/package.json
RUN npm ci --ignore-scripts

FROM dependencies AS builder
COPY apps/web apps/web
COPY packages/api-client packages/api-client
COPY openapi.json openapi.json
RUN npm --workspace @praxisai/api-client run build && npm --workspace @praxisai/web run build

FROM node:22.16.0-bookworm-slim AS runtime
ENV NODE_ENV=production
WORKDIR /app
COPY --from=builder /workspace/apps/web/.next/standalone ./
COPY --from=builder /workspace/apps/web/.next/static ./apps/web/.next/static
USER node
EXPOSE 3000
CMD ["node", "apps/web/server.js"]


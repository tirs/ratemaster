# Build stage
FROM node:20-alpine AS builder

WORKDIR /app

# Copy package files
COPY package.json package-lock.json* ./

# Install dependencies
RUN npm ci

# Copy source
COPY . .

# Build-time env: API_BACKEND for server-side proxy (baked in at build)
ARG NEXT_PUBLIC_API_BACKEND=
ARG API_BACKEND=http://backend:30080
ENV NEXT_PUBLIC_API_BACKEND=$NEXT_PUBLIC_API_BACKEND
ENV API_BACKEND=$API_BACKEND

# Build
RUN npm run build

# Production stage
FROM node:20-alpine AS runner

WORKDIR /app

ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1

# Create non-root user
RUN addgroup --system --gid 1001 nodejs
RUN adduser --system --uid 1001 nextjs

# Copy built assets
COPY --from=builder /app/public ./public
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

USER nextjs

EXPOSE 30000

ENV PORT=30000
ENV HOSTNAME="0.0.0.0"

CMD ["node", "server.js"]

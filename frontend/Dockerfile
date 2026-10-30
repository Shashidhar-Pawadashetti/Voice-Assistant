# Stage 1: Build the React + TypeScript PWA application
FROM node:20-alpine AS builder

WORKDIR /app

# Install dependencies with frozen lockfile for deterministic builds
COPY package.json package-lock.json ./
RUN npm ci

# Copy application source code
COPY . ./

# Build production assets
RUN npm run build

# Stage 2: Serve with lightweight Nginx image
FROM nginx:1.27-alpine

# Remove default nginx static assets
RUN rm -rf /usr/share/nginx/html/*

# Copy built static assets from builder stage
COPY --from=builder /app/dist /usr/share/nginx/html

# Copy custom Nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Expose standard HTTP port
EXPOSE 80

# Run Nginx as daemon off
CMD ["nginx", "-g", "daemon off;"]

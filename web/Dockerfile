# ---- Build the Angular app ----
FROM node:22-slim AS build
WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci --ignore-scripts

COPY . .
RUN npm run build

# ---- Serve the static output ----
# nginx-unprivileged runs as a non-root user out of the box, listening on
# 8080 instead of 80 (binding <1024 requires root).
FROM nginxinc/nginx-unprivileged:1.27-alpine
COPY --from=build /app/dist/web/browser /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 8080

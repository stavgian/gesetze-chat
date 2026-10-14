# ---- Build the Angular app ----
FROM node:22-slim AS build
WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci

COPY . .
RUN npm run build

# ---- Serve the static output ----
FROM nginx:1.27-alpine
COPY --from=build /app/dist/web/browser /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

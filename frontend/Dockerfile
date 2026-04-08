FROM node:20-alpine AS build
ARG VITE_DEPLOYMENT_MODE=saas
ENV VITE_DEPLOYMENT_MODE=$VITE_DEPLOYMENT_MODE
WORKDIR /app
COPY package*.json ./
ENV PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD=1
RUN npm ci
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80

# Dockerfile para React frontend

ARG NODE_IMAGE=node:20-alpine
FROM $NODE_IMAGE AS build

WORKDIR /app
COPY apps/frontend/package*.json ./
COPY apps/frontend/.env.local ./
RUN npm install
COPY apps/frontend/ .
RUN npm run build

ARG NGINX_IMAGE=nginx:alpine
FROM $NGINX_IMAGE
COPY --from=build /app/dist /usr/share/nginx/html
COPY infra/nginx.conf /etc/nginx/conf.d/default.conf

ARG NGINX_PORT=80
EXPOSE $NGINX_PORT

CMD ["nginx", "-g", "daemon off;"]

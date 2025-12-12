FROM node:20-alpine AS build

WORKDIR /app

COPY package*.json ./


RUN npm ci

COPY . .
ARG API_URL
RUN sed -i "s|http://stafftrace.xyz:8080/api|${API_URL}|g" src/environments/environment.ts


RUN npm run build

FROM nginx:alpine

COPY --from=build /app/dist/frontend/browser /usr/share/nginx/html
COPY nginx.conf /etc/nginx/nginx.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]

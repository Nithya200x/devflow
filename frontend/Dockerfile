# Stage 1: Build the React Application
FROM node:22-alpine AS builder

WORKDIR /app

COPY package*.json ./
RUN npm install

COPY . .

# Build the app. The environment variable connects Axios to the backend in Docker Compose.
# Wait, if we use a relative URL or map it to a specific domain, we could inject it here.
# For simplicity, we assume Nginx reverse proxy or localhost:5000.
# Actually, the user accesses the frontend from their host browser, so the browser sends requests.
# The browser needs to reach the backend on localhost:5000 or through the Nginx proxy.
# We will just use http://localhost:5000 for local demo, which matches API_URL in our React code.
RUN npm run build

# Stage 2: Serve with Nginx
FROM nginx:alpine

# Copy custom nginx config if necessary, but default works for static sites
# We just copy the built assets
COPY --from=builder /app/dist /usr/share/nginx/html

# Copy a custom nginx configuration to handle React Router
RUN printf '%s\n' \
    'server {' \
    '    listen 80;' \
    '    server_name localhost;' \
    '    location / {' \
    '        root /usr/share/nginx/html;' \
    '        index index.html index.htm;' \
    '        try_files $uri $uri/ /index.html;' \
    '    }' \
    '}' > /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]

# STAGE 1: Build the React application
FROM node:20-alpine AS build

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install ALL dependencies (including devDependencies needed for build)
RUN npm ci

# Copy source code
COPY . .

# Build the application (uses .env.production automatically)
RUN npm run build

# STAGE 2: Serve with Nginx
FROM nginx:stable-alpine

# Copy custom nginx config
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copy built files
COPY --from=build /app/dist /usr/share/nginx/html

# Cloud Run expects the service to listen on port 8080
EXPOSE 8080

# Start nginx
CMD ["nginx", "-g", "daemon off;"]
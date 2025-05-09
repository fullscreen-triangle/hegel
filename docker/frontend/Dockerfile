# Build stage
FROM node:18-alpine as build

WORKDIR /app

# Install dependencies
COPY frontend/package.json frontend/yarn.lock ./
RUN yarn install --frozen-lockfile

# Copy source code
COPY frontend/ ./

# Build for production
ARG NODE_ENV=production
ENV NODE_ENV=${NODE_ENV}
ENV REACT_APP_API_URL=/api
ENV REACT_APP_LLM_SERVICE_URL=/llm

RUN yarn build

# Production stage
FROM nginx:alpine

# Copy built files from build stage
COPY --from=build /app/build /usr/share/nginx/html

# Copy nginx configuration
COPY docker/frontend/nginx.conf /etc/nginx/conf.d/default.conf

# Expose port
EXPOSE 80

# Start Nginx
CMD ["nginx", "-g", "daemon off;"] 
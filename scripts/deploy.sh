#!/bin/bash
set -e

# Hegel Deployment Script
# This script deploys Hegel in production mode

echo "====================================================="
echo "Deploying Hegel in production mode"
echo "====================================================="

# Load environment variables if .env exists
if [ -f "$(dirname "$0")/../.env" ]; then
    source "$(dirname "$0")/../.env"
else
    echo "Error: .env file not found. Please run setup.sh first."
    exit 1
fi

# Check if running as root (required for some server deployments)
if [ "$(id -u)" != "0" ]; then
   echo "Warning: This script may need to be run as root for some operations."
   read -p "Continue anyway? (y/n) " -n 1 -r
   echo
   if [[ ! $REPLY =~ ^[Yy]$ ]]; then
       exit 1
   fi
fi

# Check for Docker and Docker Compose
if ! command -v docker &> /dev/null || ! command -v docker-compose &> /dev/null; then
    echo "Error: Docker and Docker Compose are required for deployment."
    exit 1
fi

# Set environment to production
export ENVIRONMENT=production

# Check if SSL certificates exist, create self-signed if not
SSL_DIR="$(dirname "$0")/../docker/nginx/ssl"
mkdir -p "$SSL_DIR"

if [ ! -f "$SSL_DIR/cert.pem" ] || [ ! -f "$SSL_DIR/key.pem" ]; then
    echo "SSL certificates not found. Creating self-signed certificates..."
    openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
        -keyout "$SSL_DIR/key.pem" \
        -out "$SSL_DIR/cert.pem" \
        -subj "/C=US/ST=State/L=City/O=Organization/CN=localhost"
    
    echo "Self-signed certificates created. Replace with real certificates for production."
fi

# Create necessary directories
echo "Creating necessary directories..."
mkdir -p "$(dirname "$0")/../data/neo4j"
mkdir -p "$(dirname "$0")/../logs/nginx"
mkdir -p "$(dirname "$0")/../logs/backend"
mkdir -p "$(dirname "$0")/../logs/llm-service"
mkdir -p "$(dirname "$0")/../logs/neo4j"
mkdir -p "$(dirname "$0")/../models"

# Set secure password for Neo4j
if [ -z "$NEO4J_PASSWORD" ]; then
    # Generate a random password if not set
    NEO4J_PASSWORD=$(openssl rand -base64 12)
    echo "Generated random Neo4j password: $NEO4J_PASSWORD"
    echo "NEO4J_PASSWORD=$NEO4J_PASSWORD" >> "$(dirname "$0")/../.env"
fi

# Set secure JWT secret
if [ -z "$JWT_SECRET_KEY" ]; then
    # Generate a random JWT secret if not set
    JWT_SECRET_KEY=$(openssl rand -base64 32)
    echo "Generated random JWT secret key"
    echo "JWT_SECRET_KEY=$JWT_SECRET_KEY" >> "$(dirname "$0")/../.env"
fi

# Build and deploy with Docker Compose
echo "Building and deploying with Docker Compose..."
cd "$(dirname "$0")/.."
docker-compose -f docker/docker-compose.prod.yml build

# Stop any existing containers
docker-compose -f docker/docker-compose.prod.yml down

# Start the services in production mode
docker-compose -f docker/docker-compose.prod.yml up -d

# Wait for services to start
echo "Waiting for services to start..."
sleep 15

# Check if services are running
echo "Checking deployed services..."
if ! docker-compose -f docker/docker-compose.prod.yml ps | grep -q "Up"; then
    echo "Error: Some services failed to start. Check the logs with 'docker-compose -f docker/docker-compose.prod.yml logs'."
    exit 1
fi

echo "====================================================="
echo "Hegel has been deployed in production mode!"
echo ""
echo "Frontend: https://your-server-ip"
echo "Backend API: https://your-server-ip/api"
echo "LLM Service: https://your-server-ip/llm"
echo ""
echo "Neo4j Database:"
echo "  URL: bolt://your-server-ip:7687"
echo "  Username: neo4j"
echo "  Password: $NEO4J_PASSWORD"
echo ""
echo "To check logs: docker-compose -f docker/docker-compose.prod.yml logs -f [service_name]"
echo "To stop all services: docker-compose -f docker/docker-compose.prod.yml down"
echo "====================================================="

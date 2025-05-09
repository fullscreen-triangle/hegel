#!/bin/bash
set -e

# Hegel Setup Script
# This script prepares the development environment for Hegel

echo "====================================================="
echo "Setting up Hegel development environment"
echo "====================================================="

# Check for required system dependencies
echo "Checking for required dependencies..."

# Check for Docker
if ! command -v docker &> /dev/null; then
    echo "Docker is not installed. Please install Docker first."
    echo "Visit https://docs.docker.com/get-docker/ for installation instructions."
    exit 1
fi

# Check for Docker Compose
if ! command -v docker-compose &> /dev/null; then
    echo "Docker Compose is not installed. Please install Docker Compose first."
    echo "Visit https://docs.docker.com/compose/install/ for installation instructions."
    exit 1
fi

# Check for Python
if ! command -v python3 &> /dev/null; then
    echo "Python 3 is not installed. Please install Python 3.8 or higher."
    exit 1
fi

# Check for Node.js
if ! command -v node &> /dev/null; then
    echo "Node.js is not installed. Please install Node.js 18 or higher."
    echo "Visit https://nodejs.org/ for installation instructions."
    exit 1
fi

# Check for yarn
if ! command -v yarn &> /dev/null; then
    echo "Yarn is not installed. Installing yarn..."
    npm install -g yarn
fi

# Create Python virtual environment for backend
echo "Setting up Python virtual environment for backend..."
cd "$(dirname "$0")/../backend"
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
deactivate

# Install frontend dependencies
echo "Setting up frontend dependencies..."
cd "$(dirname "$0")/../frontend"
yarn install

# Pull Neo4j image if not already present
echo "Setting up Neo4j..."
if ! docker image inspect neo4j:latest &> /dev/null; then
    docker pull neo4j:latest
fi

# Create necessary directories
echo "Creating necessary directories..."
cd "$(dirname "$0")/.."
mkdir -p data/neo4j
mkdir -p logs

# Generate sample configuration files if they don't exist
echo "Setting up configuration files..."
if [ ! -f .env ]; then
    echo "Creating sample .env file..."
    cat > .env << EOF
# Hegel Environment Configuration
NEO4J_AUTH=neo4j/password
NEO4J_HOST=localhost
NEO4J_PORT=7687
NEO4J_BROWSER_PORT=7474
BACKEND_PORT=8080
FRONTEND_PORT=3000
LLM_SERVICE_PORT=5000
DEVELOPMENT_MODE=true
EOF
fi

# Set up git hooks
echo "Setting up git hooks..."
cp "$(dirname "$0")/hooks/pre-commit" "$(dirname "$0")/../.git/hooks/"
chmod +x "$(dirname "$0")/../.git/hooks/pre-commit"

echo "====================================================="
echo "Setup complete! You can now start the development environment with:"
echo "./scripts/dev.sh"
echo "====================================================="

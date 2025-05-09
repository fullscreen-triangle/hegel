#!/bin/bash
set -e

# Hegel Development Script
# This script starts all necessary services for development

echo "====================================================="
echo "Starting Hegel development environment"
echo "====================================================="

# Load environment variables if .env exists
if [ -f "$(dirname "$0")/../.env" ]; then
    source "$(dirname "$0")/../.env"
else
    echo "Warning: .env file not found. Using default settings."
    # Set default environment variables
    export NEO4J_AUTH=neo4j/password
    export NEO4J_HOST=localhost
    export NEO4J_PORT=7687
    export NEO4J_BROWSER_PORT=7474
    export BACKEND_PORT=8080
    export FRONTEND_PORT=3000
    export LLM_SERVICE_PORT=5000
    export DEVELOPMENT_MODE=true
fi

# Function to start services in tmux sessions
start_service() {
    local service_name=$1
    local command=$2
    
    if command -v tmux &> /dev/null; then
        if tmux has-session -t "hegel-$service_name" 2>/dev/null; then
            echo "Session hegel-$service_name already exists, killing it..."
            tmux kill-session -t "hegel-$service_name"
        fi
        
        echo "Starting $service_name in tmux session..."
        tmux new-session -d -s "hegel-$service_name" "$command"
        echo "$service_name started in tmux session 'hegel-$service_name'"
        echo "To attach: tmux attach-session -t hegel-$service_name"
    else
        echo "tmux not found, starting $service_name in background..."
        eval "$command &"
        echo "$service_name started in background"
    fi
}

# Check if Docker is running
if ! docker info &>/dev/null; then
    echo "Docker is not running. Please start Docker and try again."
    exit 1
fi

# Start Neo4j if not using docker-compose
if [ "${USE_DOCKER_COMPOSE:-false}" != "true" ]; then
    echo "Starting Neo4j..."
    docker run -d \
        --name hegel-neo4j \
        -p "${NEO4J_BROWSER_PORT}:7474" \
        -p "${NEO4J_PORT}:7687" \
        -v "$(dirname "$0")/../data/neo4j:/data" \
        -e "NEO4J_AUTH=${NEO4J_AUTH}" \
        neo4j:latest
    
    echo "Neo4j started at http://localhost:${NEO4J_BROWSER_PORT}"
    echo "Neo4j Bolt available at bolt://localhost:${NEO4J_PORT}"
fi

# Start backend
echo "Starting backend service..."
cd "$(dirname "$0")/../backend"
start_service "backend" "cd $(dirname "$0")/../backend && source venv/bin/activate && python -m uvicorn app.main:app --reload --port ${BACKEND_PORT}"

# Start LLM service if it exists
if [ -d "$(dirname "$0")/../llm-service" ]; then
    echo "Starting LLM service..."
    start_service "llm" "cd $(dirname "$0")/../llm-service && source venv/bin/activate && python -m uvicorn app.main:app --reload --port ${LLM_SERVICE_PORT}"
fi

# Start frontend
echo "Starting frontend..."
cd "$(dirname "$0")/../frontend"
start_service "frontend" "cd $(dirname "$0")/../frontend && yarn dev --port ${FRONTEND_PORT}"

# Start Docker Compose if enabled
if [ "${USE_DOCKER_COMPOSE:-false}" = "true" ]; then
    echo "Starting all services with Docker Compose..."
    cd "$(dirname "$0")/.."
    docker-compose up -d
fi

echo "====================================================="
echo "Development environment started!"
echo ""
echo "Frontend: http://localhost:${FRONTEND_PORT}"
echo "Backend API: http://localhost:${BACKEND_PORT}"
echo "LLM Service: http://localhost:${LLM_SERVICE_PORT}"
echo "Neo4j Browser: http://localhost:${NEO4J_BROWSER_PORT}"
echo ""
echo "To stop all services: ./scripts/stop.sh"
echo "====================================================="

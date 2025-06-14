#!/bin/bash
set -e

# Hegel Stop Script
# This script stops all running Hegel services

echo "====================================================="
echo "Stopping Hegel services"
echo "====================================================="

# Check if Docker is running
if command -v docker &> /dev/null && docker info &>/dev/null; then
    # Stop Docker containers if Docker is running
    if [ -f "$(dirname "$0")/../docker-compose.yml" ]; then
        echo "Stopping Docker Compose services..."
        cd "$(dirname "$0")/.."
        docker-compose down
    fi

    # Stop individual container if it exists
    if docker ps -a | grep -q "hegel-neo4j"; then
        echo "Stopping Neo4j container..."
        docker stop hegel-neo4j
        docker rm hegel-neo4j
    fi
fi

# Kill tmux sessions if they exist
if command -v tmux &> /dev/null; then
    for session in $(tmux list-sessions -F "#{session_name}" 2>/dev/null | grep "^hegel-" || true); do
        echo "Stopping tmux session: $session"
        tmux kill-session -t "$session"
    done
fi

# Kill background processes (for systems without tmux)
echo "Checking for background processes..."

# Check for running uvicorn processes
pkill -f "uvicorn app.main:app" || true

# Check for running yarn dev processes
pkill -f "yarn dev" || true

echo "====================================================="
echo "All Hegel services have been stopped"
echo "=====================================================" 
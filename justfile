# Justfile for Hegel Biological Computing Platform
# Modern command runner for development workflows

# Default recipe
default:
    @just --list

# Development setup and initialization
setup:
    #!/usr/bin/env bash
    echo "🧬 Setting up Hegel Biological Computing Platform..."
    
    # Install Rust toolchain
    if ! command -v rustc &> /dev/null; then
        echo "Installing Rust..."
        curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
        source ~/.cargo/env
    fi
    
    # Install required targets and components
    rustup target add wasm32-unknown-unknown
    rustup component add rustfmt clippy rust-analyzer
    
    # Install cargo tools
    cargo install cargo-make cargo-audit cargo-outdated wasm-pack
    
    # Setup database
    just db-setup
    
    echo "✅ Hegel development environment ready!"

# Database operations
db-setup:
    #!/usr/bin/env bash
    echo "🗄️  Setting up biological computing database..."
    docker-compose up -d postgres redis
    sleep 10
    cargo run --bin setup-database

db-migrate:
    cargo run --bin migrate-database

db-reset:
    docker-compose down postgres
    docker volume rm hegel_postgres_data
    just db-setup

# Build operations
build:
    echo "🔧 Building all biological computing modules..."
    cargo build --workspace --all-features

build-release:
    echo "🚀 Building optimized biological computing release..."
    cargo build --workspace --profile biological-release

build-oxygen:
    echo "💨 Building oxygen substrate module..."
    cargo build --package oxygen-substrate --all-features

build-membrane:
    echo "🧠 Building membrane quantum computer module..."
    cargo build --package membrane-quantum --all-features

build-evidence:
    echo "📊 Building evidence processing modules..."
    cargo build --package fuzzy-bayesian --package evidence-rectification --all-features

build-intelligence:
    echo "🤖 Building AI intelligence modules..."
    cargo build --package mzekezeke --package diggiden --package hatata --package spectacular --package nicotine --all-features

build-wasm:
    echo "🌐 Building WebAssembly bindings..."
    wasm-pack build src/wasm/frontend-bindings --target web --out-dir ../../frontend/pkg

# Testing operations
test:
    echo "🧪 Running all biological computing tests..."
    cargo test --workspace --all-features

test-oxygen:
    echo "💨 Testing oxygen substrate processing..."
    cargo test --package oxygen-substrate --all-features -- --nocapture

test-membrane:
    echo "🧠 Testing membrane quantum computers..."
    cargo test --package membrane-quantum --all-features -- --nocapture

test-evidence:
    echo "📊 Testing evidence networks..."
    cargo test --package fuzzy-bayesian --package evidence-rectification --all-features

test-intelligence:
    echo "🤖 Testing AI intelligence modules..."
    cargo test --package mzekezeke --package diggiden --package hatata --package spectacular --package nicotine --all-features

test-integration:
    echo "🔗 Running integration tests..."
    cargo test --test integration --all-features

# Benchmarking operations
bench:
    echo "📈 Running biological computing benchmarks..."
    cargo bench --workspace

bench-oxygen:
    echo "💨 Benchmarking oxygen processing..."
    cargo bench --package oxygen-substrate

bench-membrane:
    echo "🧠 Benchmarking membrane quantum performance..."
    cargo bench --package membrane-quantum

bench-evidence:
    echo "📊 Benchmarking evidence networks..."
    cargo bench --package fuzzy-bayesian

# Code quality operations
fmt:
    echo "🎨 Formatting biological computing code..."
    cargo fmt --all

clippy:
    echo "📎 Running clippy lints..."
    cargo clippy --workspace --all-features -- -D warnings

check:
    echo "✅ Quick code checks..."
    cargo check --workspace --all-features

audit:
    echo "🔒 Security audit..."
    cargo audit

outdated:
    echo "📅 Checking outdated dependencies..."
    cargo outdated

fix:
    echo "🔧 Auto-fixing code issues..."
    cargo clippy --workspace --all-features --fix --allow-dirty

# Documentation operations
docs:
    echo "📚 Generating documentation..."
    cargo doc --workspace --all-features --no-deps

docs-open:
    echo "📖 Opening documentation..."
    cargo doc --workspace --all-features --no-deps --open

# Development server operations
dev:
    echo "🚀 Starting development server..."
    cargo run --bin hegel-server

dev-watch:
    echo "👀 Starting development server with hot reload..."
    cargo watch -x "run --bin hegel-server"

dev-frontend:
    echo "🌐 Starting frontend development server..."
    cd frontend && npm run dev

# Docker operations
docker-build:
    echo "🐳 Building Docker image..."
    docker build -t hegel-biological-computing:latest .

docker-run:
    echo "🐳 Running Docker container..."
    docker run -p 8080:8080 hegel-biological-computing:latest

docker-compose-up:
    echo "🐳 Starting full stack with Docker Compose..."
    docker-compose up -d

docker-compose-down:
    echo "🐳 Stopping Docker Compose stack..."
    docker-compose down

docker-compose-logs:
    echo "📋 Viewing Docker Compose logs..."
    docker-compose logs -f

# Simulation and testing operations
simulate-oxygen:
    echo "💨 Running oxygen processing simulation..."
    cargo run --package oxygen-substrate --bin simulate_processing

test-membrane-coherence:
    echo "🧠 Testing membrane quantum coherence..."
    cargo run --package membrane-quantum --bin test_coherence

benchmark-evidence-network:
    echo "📊 Benchmarking evidence network..."
    cargo run --package evidence-rectification --bin benchmark_network

validate-biological-constraints:
    echo "🧬 Validating biological constraints..."
    cargo run --bin validate-constraints

# Deployment operations
deploy-staging:
    echo "🚀 Deploying to staging..."
    just build-release
    docker build -t hegel-staging .
    # Add staging deployment commands here

deploy-production:
    echo "🌍 Deploying to production..."
    just build-release
    just test
    docker build -t hegel-production .
    # Add production deployment commands here

# Monitoring operations
metrics:
    echo "📊 Viewing metrics..."
    open http://localhost:3000  # Grafana

logs:
    echo "📋 Viewing application logs..."
    tail -f logs/hegel.log

health-check:
    echo "🏥 Running health check..."
    curl -f http://localhost:8080/health || echo "❌ Health check failed"

# Maintenance operations
clean:
    echo "🧹 Cleaning build artifacts..."
    cargo clean

clean-docker:
    echo "🧹 Cleaning Docker images..."
    docker system prune -f

clean-all: clean clean-docker
    echo "🧹 Deep cleaning everything..."
    docker-compose down -v
    rm -rf target/
    rm -rf frontend/node_modules/

# CI/CD operations
ci:
    echo "🔄 Running CI pipeline locally..."
    just fmt
    just clippy
    just test
    just audit
    echo "✅ CI pipeline completed"

pre-commit:
    echo "📝 Running pre-commit checks..."
    just fmt
    just clippy
    just test-oxygen
    just test-membrane

# Research and experimentation
research-mode:
    echo "🔬 Starting research mode..."
    RESEARCH_MODE=true cargo run --bin hegel-research

experiment *ARGS:
    echo "⚗️  Running experiment: {{ARGS}}"
    cargo run --bin experiments -- {{ARGS}}

# Utility operations
backup:
    echo "💾 Creating backup..."
    timestamp=$(date +%Y%m%d_%H%M%S)
    pg_dump $DATABASE_URL > backups/hegel_${timestamp}.sql
    tar -czf backups/data_${timestamp}.tar.gz data/

restore BACKUP:
    echo "♻️  Restoring from backup: {{BACKUP}}"
    psql $DATABASE_URL < {{BACKUP}}

version:
    echo "📋 Hegel Biological Computing Platform"
    cargo --version
    rustc --version
    echo "Biological Computing Mode: $(cargo run --bin version)"

# Help and information
info:
    echo "🧬 Hegel Biological Computing Platform Information"
    echo "=============================================="
    echo "🔬 Revolutionary oxygen-enhanced molecular evidence networks"
    echo "🧠 Membrane quantum computers for biological processing"
    echo "⚡ Electron cascade communication systems"
    echo "🧬 Genome consultation with cellular information supremacy"
    echo "🤖 AI intelligence modules for evidence rectification"
    echo "=============================================="
    just --list

# Multi-stage Dockerfile for Hegel Biological Computing Platform
# Optimized for biological computer modules and evidence processing

# Build stage
FROM rust:1.75-bullseye as builder

# Install required system dependencies for biological computing
RUN apt-get update && apt-get install -y \
    pkg-config \
    libssl-dev \
    libpq-dev \
    cmake \
    protobuf-compiler \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy dependency files first for better caching
COPY Cargo.toml Cargo.lock ./
COPY rust-toolchain.toml ./
COPY .cargo/ ./.cargo/

# Create dummy source files to build dependencies
RUN mkdir -p src/core/oxygen-substrate/src \
    src/core/electron-cascade/src \
    src/core/membrane-quantum/src \
    src/core/genome-consultation/src \
    src/evidence/fuzzy-bayesian/src \
    src/evidence/evidence-rectification/src \
    src/evidence/temporal-decay/src \
    src/intelligence/mzekezeke/src \
    src/intelligence/diggiden/src \
    src/intelligence/hatata/src \
    src/intelligence/spectacular/src \
    src/intelligence/nicotine/src \
    src/federated/privacy-preserving/src \
    src/federated/consensus-protocol/src \
    src/federated/bloodhound-sync/src \
    src/api/rest-interface/src \
    src/wasm/frontend-bindings/src \
    src/utils/s-distance/src \
    src/utils/zero-computation/src \
    src/utils/oscillatory-dynamics/src

# Create dummy Cargo.toml files for each module
RUN for dir in src/core/* src/evidence/* src/intelligence/* src/federated/* src/api/* src/wasm/* src/utils/*; do \
    echo '[package]' > $dir/Cargo.toml && \
    echo 'name = "'$(basename $dir)'"' >> $dir/Cargo.toml && \
    echo 'version = "0.1.0"' >> $dir/Cargo.toml && \
    echo 'edition = "2021"' >> $dir/Cargo.toml && \
    echo 'fn main() {}' > $dir/src/main.rs && \
    echo 'pub fn add(left: usize, right: usize) -> usize { left + right }' > $dir/src/lib.rs; \
    done

# Build dependencies (this layer will be cached)
RUN cargo build --workspace --release

# Remove dummy source code
RUN rm -rf src/

# Copy actual source code
COPY src/ ./src/

# Build the actual application with biological computing optimizations
RUN cargo build --workspace --profile biological-release

# Runtime stage
FROM debian:bullseye-slim as runtime

# Install runtime dependencies for biological computing
RUN apt-get update && apt-get install -y \
    ca-certificates \
    libssl1.1 \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Create application user for security
RUN useradd -r -s /bin/false -m -d /app hegel

# Set working directory
WORKDIR /app

# Copy built binaries from builder stage
COPY --from=builder /app/target/biological-release/ ./bin/
COPY --from=builder /app/target/biological-release/deps/ ./deps/

# Copy configuration files
COPY configs/ ./configs/
COPY docs/ ./docs/

# Set ownership and permissions
RUN chown -R hegel:hegel /app && \
    chmod +x ./bin/*

# Switch to application user
USER hegel

# Expose ports for biological computing services
EXPOSE 8080 8081 8082

# Health check for biological computing services
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# Environment variables for biological computing
ENV BIOLOGICAL_COMPUTING_MODE=production
ENV RUST_LOG=info
ENV OXYGEN_PROCESSING_THREADS=8
ENV MEMBRANE_QUANTUM_COHERENCE_TIME=150000
ENV ELECTRON_CASCADE_TIMEOUT=1000

# Default command to run the biological computing platform
CMD ["./bin/hegel-server"]

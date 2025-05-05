FROM rust:1.72-slim

WORKDIR /app

# Install dependencies
RUN apt-get update && \
    apt-get install -y pkg-config libssl-dev libsqlite3-dev && \
    rm -rf /var/lib/apt/lists/*

# Copy Cargo.toml and Cargo.lock
COPY Cargo.toml Cargo.lock ./

# Create empty source file to cache dependencies
RUN mkdir -p src/bin && \
    echo "fn main() {}" > src/main.rs && \
    echo "pub fn dummy() {}" > src/lib.rs && \
    echo "fn main() {}" > src/bin/api.rs && \
    cargo build --bin hegel-api && \
    rm -rf src

# Copy the actual source code
COPY . .

# Build the application in release mode
RUN cargo build --release --bin hegel-api

# Expose the port
EXPOSE 8080

# Start the application
CMD ["./target/release/hegel-api"] 
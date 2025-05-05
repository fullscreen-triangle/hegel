# Hegel Project: Setup Guide

This document provides comprehensive instructions for setting up the Hegel molecular identity validation and visualization platform.

## Table of Contents
- [Project Structure](#project-structure)
- [Environment Setup](#environment-setup)
- [Backend Installation](#backend-installation)
- [Frontend Installation](#frontend-installation)
- [Configuration Files](#configuration-files)
- [Development Workflow](#development-workflow)
- [Deployment](#deployment)

## Project Structure

Create the following folder structure for the Hegel project:

```
hegel/
├── .github/                     # GitHub workflows for CI/CD
│   └── workflows/
│       ├── ci.yml               # Continuous integration configuration
│       └── release.yml          # Release workflow
├── core/                        # Core Rust-based orchestration layer
│   ├── src/
│   │   ├── bin/                 # Binary executables
│   │   │   └── hegel.rs         # Main CLI entry point
│   │   ├── metacognition/       # Metacognitive orchestration layer
│   │   │   ├── mod.rs
│   │   │   ├── memory.rs        # Memory persistence
│   │   │   ├── llm.rs           # LLM integration
│   │   │   └── decision.rs      # Decision engine
│   │   ├── processing/          # Data processing components
│   │   │   ├── mod.rs
│   │   │   ├── ingest.rs        # Data ingestion
│   │   │   └── pipeline.rs      # Processing pipelines
│   │   ├── graph/               # Graph database components
│   │   │   ├── mod.rs
│   │   │   ├── neo4j.rs         # Neo4j driver
│   │   │   └── schema.rs        # Graph schema definitions
│   │   ├── lib.rs               # Core library exports
│   │   └── main.rs              # Library main entry point
│   ├── Cargo.toml               # Rust dependencies
│   └── Cargo.lock               # Rust lock file
├── backend/                     # Python backend services
│   ├── api/                     # FastAPI service
│   │   ├── main.py              # Main API entry point
│   │   ├── routes/              # API routes
│   │   │   ├── __init__.py
│   │   │   ├── molecules.py     # Molecule-related endpoints
│   │   │   ├── experiments.py   # Experiment-related endpoints
│   │   │   └── visualization.py # Visualization endpoints
│   │   ├── models/              # API data models
│   │   │   ├── __init__.py
│   │   │   └── schemas.py       # Pydantic schemas
│   │   └── services/            # Service layer
│   │       ├── __init__.py
│   │       └── graph.py         # Graph database service
│   ├── ml/                      # Machine learning components
│   │   ├── __init__.py
│   │   ├── models/              # ML model definitions
│   │   │   ├── __init__.py
│   │   │   ├── spectranet.py    # MS/MS spectra analysis model
│   │   │   └── molecule_mapper.py # Molecule similarity model
│   │   └── training/            # Model training scripts
│   │       ├── __init__.py
│   │       └── train.py         # Training pipeline
│   ├── processing/              # Data processing modules
│   │   ├── __init__.py
│   │   ├── ingest.py            # Data ingestion
│   │   ├── extract.py           # Feature extraction
│   │   └── annotate.py          # Annotation
│   ├── tests/                   # Backend tests
│   │   ├── __init__.py
│   │   ├── conftest.py          # Test configuration
│   │   └── test_api.py          # API tests
│   ├── pyproject.toml           # Python project config
│   └── requirements.txt         # Python dependencies
├── frontend/                    # React frontend
│   ├── public/                  # Static assets
│   ├── src/                     # Source code
│   │   ├── components/          # React components
│   │   │   ├── Dashboard.jsx    # Main dashboard
│   │   │   ├── NetworkGraph.jsx # Graph visualization
│   │   │   └── SpectrumViewer.jsx # Spectrum visualization
│   │   ├── hooks/               # React hooks
│   │   ├── services/            # API services
│   │   ├── types/               # TypeScript types
│   │   ├── utils/               # Utilities
│   │   ├── App.jsx              # Main app component
│   │   └── index.jsx            # Entry point
│   ├── package.json             # NPM dependencies
│   ├── package-lock.json        # NPM lock file
│   └── tsconfig.json            # TypeScript configuration
├── docker/                      # Docker configurations
│   ├── core/                    # Core service Dockerfile
│   ├── backend/                 # Backend service Dockerfile
│   ├── frontend/                # Frontend Dockerfile
│   └── docker-compose.yml       # Docker Compose config
├── docs/                        # Documentation
│   ├── api/                     # API documentation
│   ├── architecture/            # Architecture diagrams
│   └── user-guide/              # User guide
├── scripts/                     # Development and deployment scripts
│   ├── setup.sh                 # Environment setup script
│   ├── dev.sh                   # Development startup script
│   └── deploy.sh                # Deployment script
├── .gitignore                   # Git ignore file
├── README.md                    # Project readme
├── LICENSE                      # License file
└── docker-compose.yml           # Root Docker Compose file
```

## Environment Setup

### Prerequisites

- Python 3.9+
- Rust 1.68+
- Node.js 18+
- Docker and Docker Compose

### Development Environment Setup

1. Clone the repository and create the basic directory structure:

```bash
# Clone or create the project
mkdir -p hegel
cd hegel

# Create the basic directory structure
mkdir -p core/src/{bin,metacognition,processing,graph}
mkdir -p backend/{api/{routes,models,services},ml/{models,training},processing,tests}
mkdir -p frontend/{public,src/{components,hooks,services,types,utils}}
mkdir -p docker/{core,backend,frontend}
mkdir -p docs/{api,architecture,user-guide}
mkdir -p scripts
mkdir -p .github/workflows
```

2. Create a setup script to automate the environment configuration:

```bash
# Create setup script
cat > scripts/setup.sh << 'EOF'
#!/bin/bash
set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}Setting up Hegel development environment...${NC}"

# Create Python virtual environment
echo -e "${GREEN}Creating Python virtual environment...${NC}"
python -m venv venv
source venv/bin/activate

# Install Python dependencies
echo -e "${GREEN}Installing Python dependencies...${NC}"
pip install -r backend/requirements.txt

# Set up Rust
echo -e "${GREEN}Setting up Rust components...${NC}"
cd core
cargo build
cd ..

# Install JavaScript dependencies
echo -e "${GREEN}Installing JavaScript dependencies...${NC}"
cd frontend
npm install
cd ..

# Set up Docker containers
echo -e "${GREEN}Setting up Docker containers...${NC}"
docker-compose -f docker/docker-compose.yml up -d neo4j elasticsearch redis

echo -e "${BLUE}Setup complete! You can now start developing Hegel.${NC}"
echo -e "${BLUE}To activate the virtual environment: source venv/bin/activate${NC}"
EOF

chmod +x scripts/setup.sh
```

## Backend Installation

### Rust Core (Metacognitive Layer)

1. Create the Cargo.toml file for the core:

```toml
[package]
name = "hegel-core"
version = "0.1.0"
edition = "2021"
authors = ["Your Name <your.email@example.com>"]
description = "Metacognitive orchestration layer for Hegel molecular identity platform"

[dependencies]
# CLI and interface
clap = { version = "4.3.0", features = ["derive"] }
crossterm = "0.26.1"
ratatui = "0.22.0"

# Async runtime
tokio = { version = "1.28.2", features = ["full"] }
futures = "0.3.28"

# Serialization
serde = { version = "1.0.163", features = ["derive"] }
serde_json = "1.0.96"

# Logging
tracing = "0.1.37"
tracing-subscriber = { version = "0.3.17", features = ["env-filter"] }

# Database interfaces
neo4rs = "0.6.2"
elasticsearch = "8.5.0-alpha.1"
redis = { version = "0.23.0", features = ["tokio-comp"] }

# HTTP client
reqwest = { version = "0.11.18", features = ["json"] }

# ML interfaces
tch = "0.13.0"  # PyTorch C++ bindings
ndarray = "0.15.6"

# Utilities
chrono = { version = "0.4.24", features = ["serde"] }
uuid = { version = "1.3.3", features = ["v4", "serde"] }
anyhow = "1.0.71"
thiserror = "1.0.40"
async-trait = "0.1.68"
derive_more = "0.99.17"

# Memory persistence
sled = "0.34.7"

[lib]
name = "hegel_core"
path = "src/lib.rs"

[[bin]]
name = "hegel"
path = "src/bin/hegel.rs"
```

2. Create the main library entry point (src/lib.rs):

```rust
pub mod metacognition;
pub mod processing;
pub mod graph;

pub use metacognition::Orchestrator;
```

3. Create the metacognition module (src/metacognition/mod.rs):

```rust
mod memory;
mod llm;
mod decision;

pub use memory::{Memory, MemoryStore};
pub use llm::LLMClient;
pub use decision::{Decision, DecisionEngine};

use crate::graph::GraphClient;
use crate::processing::ProcessingEngine;

pub struct Orchestrator {
    memory_store: memory::MemoryStore,
    llm_client: llm::LLMClient,
    decision_engine: decision::DecisionEngine,
    graph_client: GraphClient,
    processing_engine: ProcessingEngine,
}

impl Orchestrator {
    pub fn new() -> Self {
        Self {
            memory_store: memory::MemoryStore::new("data/memory"),
            llm_client: llm::LLMClient::new(),
            decision_engine: decision::DecisionEngine::new(),
            graph_client: GraphClient::new(),
            processing_engine: ProcessingEngine::new(),
        }
    }

    pub async fn process_command(&mut self, command: &str) -> anyhow::Result<String> {
        // Log the command
        tracing::info!("Processing command: {}", command);

        // Create a memory context for this interaction
        let memory_id = uuid::Uuid::new_v4().to_string();
        let memory = Memory::new(memory_id.clone(), command);
        self.memory_store.store(&memory_id, &memory)?;

        // Ask LLM for decision
        let context = self.prepare_context(&memory);
        let decision = self.llm_client.decide(command, &context).await?;

        // Execute the decision
        let result = self.execute_decision(decision, &memory_id).await?;

        // Update memory with the result
        let updated_memory = self.memory_store.get(&memory_id)?
            .ok_or_else(|| anyhow::anyhow!("Memory not found"))?
            .with_result(result.clone());
        self.memory_store.store(&memory_id, &updated_memory)?;

        Ok(result)
    }

    async fn execute_decision(&self, decision: Decision, memory_id: &str) -> anyhow::Result<String> {
        match decision {
            Decision::ProcessFile(path) => {
                self.processing_engine.process_file(&path).await
            },
            Decision::QueryMolecule(id) => {
                self.graph_client.query_molecule(&id).await
            },
            Decision::RunAnalysis(params) => {
                self.processing_engine.run_analysis(&params).await
            },
            // Add more decision types as needed
        }
    }

    fn prepare_context(&self, memory: &Memory) -> String {
        // Prepare context from memory
        format!("Previous interactions: {}", memory.history_summary())
    }
}
```

4. Create the main CLI entry point (src/bin/hegel.rs):

```rust
use clap::{Parser, Subcommand};
use hegel_core::Orchestrator;
use std::path::PathBuf;

#[derive(Parser)]
#[command(author, version, about, long_about = None)]
struct Cli {
    #[command(subcommand)]
    command: Commands,
}

#[derive(Subcommand)]
enum Commands {
    /// Process an experimental data file
    Process {
        /// Path to the experiment file
        #[arg(value_name = "FILE")]
        file: PathBuf,
    },
    /// Query information about a molecule
    Query {
        /// Molecule identifier
        #[arg(value_name = "MOLECULE_ID")]
        molecule_id: String,
    },
    /// Start an interactive session
    Interactive,
}

#[tokio::main]
async fn main() -> anyhow::Result<()> {
    // Initialize logging
    tracing_subscriber::fmt::init();

    // Parse command line arguments
    let cli = Cli::parse();

    // Create orchestrator
    let mut orchestrator = Orchestrator::new();

    // Process commands
    match cli.command {
        Commands::Process { file } => {
            let command = format!("process file {}", file.display());
            let result = orchestrator.process_command(&command).await?;
            println!("Processing result: {}", result);
        },
        Commands::Query { molecule_id } => {
            let command = format!("query molecule {}", molecule_id);
            let result = orchestrator.process_command(&command).await?;
            println!("Query result: {}", result);
        },
        Commands::Interactive => {
            println!("Starting interactive session. Type 'exit' to quit.");
            
            loop {
                print!("> ");
                std::io::Write::flush(&mut std::io::stdout())?;
                
                let mut input = String::new();
                std::io::stdin().read_line(&mut input)?;
                
                let input = input.trim();
                if input == "exit" {
                    break;
                }
                
                match orchestrator.process_command(input).await {
                    Ok(result) => println!("{}", result),
                    Err(e) => println!("Error: {}", e),
                }
            }
        },
    }

    Ok(())
}
```

### Python Backend

1. Create the requirements.txt file for the Python backend:

```
# API and Web
fastapi==0.95.2
uvicorn==0.22.0
starlette==0.27.0
httpx==0.24.1
pydantic==1.10.8
python-multipart==0.0.6

# Database
neo4j==5.9.0
elasticsearch==8.8.0
redis==4.5.5

# Machine Learning
torch==2.0.1
transformers==4.29.2
huggingface-hub==0.14.1
scikit-learn==1.2.2
numpy==1.24.3
pandas==2.0.2
scipy==1.10.1

# Processing
pyarrow==12.0.0
polars==0.18.0
h5py==3.8.0
zarr==2.14.2
numba==0.57.0

# Visualization
plotly==5.14.1
matplotlib==3.7.1
seaborn==0.12.2
networkx==3.1

# Utilities
tqdm==4.65.0
pyyaml==6.0
python-dotenv==1.0.0
loguru==0.7.0
typer==0.9.0
rich==13.3.5

# Testing
pytest==7.3.1
pytest-asyncio==0.21.0
pytest-cov==4.1.0

# Rust integration
maturin==1.0.0

```

2. Create a basic FastAPI application (backend/api/main.py):

```python
import os
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Create FastAPI app
app = FastAPI(
    title="Hegel API",
    description="API for the Hegel molecular identity validation platform",
    version="0.1.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For development, restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Import routers
from routes.molecules import router as molecules_router
from routes.experiments import router as experiments_router
from routes.visualization import router as visualization_router

# Include routers
app.include_router(molecules_router, prefix="/api/molecules", tags=["molecules"])
app.include_router(experiments_router, prefix="/api/experiments", tags=["experiments"])
app.include_router(visualization_router, prefix="/api/visualization", tags=["visualization"])

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
```

3. Create a molecule routes file (backend/api/routes/molecules.py):

```python
from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional
from pydantic import BaseModel, Field

# Import services
from services.graph import GraphService

# Create router
router = APIRouter()

# Define models
class Property(BaseModel):
    name: str
    value: str
    confidence: float = Field(ge=0.0, le=1.0)

class Experiment(BaseModel):
    id: str
    name: str
    technique: str
    confidence: float = Field(ge=0.0, le=1.0)

class Molecule(BaseModel):
    id: str
    name: str
    formula: Optional[str] = None
    properties: List[Property] = []
    experiments: List[Experiment] = []
    evidence_score: float = Field(ge=0.0, le=1.0)

# Dependency
def get_graph_service():
    return GraphService()

@router.get("", response_model=List[Molecule])
async def list_molecules(
    search: Optional[str] = None,
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    graph_service: GraphService = Depends(get_graph_service)
):
    """List molecules with optional search"""
    try:
        result = await graph_service.list_molecules(search, limit, offset)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{molecule_id}", response_model=Molecule)
async def get_molecule(
    molecule_id: str,
    graph_service: GraphService = Depends(get_graph_service)
):
    """Get details for a specific molecule"""
    try:
        molecule = await graph_service.get_molecule(molecule_id)
        if not molecule:
            raise HTTPException(status_code=404, detail="Molecule not found")
        return molecule
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{molecule_id}/evidence", response_model=dict)
async def get_molecule_evidence(
    molecule_id: str,
    graph_service: GraphService = Depends(get_graph_service)
):
    """Get evidence details for a specific molecule"""
    try:
        evidence = await graph_service.get_molecule_evidence(molecule_id)
        if not evidence:
            raise HTTPException(status_code=404, detail="Evidence not found")
        return evidence
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

4. Create a graph service (backend/api/services/graph.py):

```python
from neo4j import AsyncGraphDatabase
import os
from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class GraphService:
    def __init__(self):
        uri = os.getenv("NEO4J_URI", "neo4j://localhost:7687")
        user = os.getenv("NEO4J_USER", "neo4j")
        password = os.getenv("NEO4J_PASSWORD", "password")
        self.driver = AsyncGraphDatabase.driver(uri, auth=(user, password))
    
    async def close(self):
        await self.driver.close()
    
    async def list_molecules(self, search: Optional[str], limit: int, offset: int) -> List[Dict[str, Any]]:
        async with self.driver.session() as session:
            if search:
                query = """
                MATCH (m:Molecule)
                WHERE m.name CONTAINS $search OR m.id CONTAINS $search
                RETURN m
                ORDER BY m.evidence_score DESC
                SKIP $offset
                LIMIT $limit
                """
                params = {"search": search, "limit": limit, "offset": offset}
            else:
                query = """
                MATCH (m:Molecule)
                RETURN m
                ORDER BY m.evidence_score DESC
                SKIP $offset
                LIMIT $limit
                """
                params = {"limit": limit, "offset": offset}
            
            result = await session.run(query, params)
            records = await result.data()
            
            return [self._molecule_from_record(record["m"]) for record in records]
    
    async def get_molecule(self, molecule_id: str) -> Optional[Dict[str, Any]]:
        async with self.driver.session() as session:
            query = """
            MATCH (m:Molecule {id: $id})
            OPTIONAL MATCH (m)-[:HAS_PROPERTY]->(p:Property)
            OPTIONAL MATCH (m)-[:IDENTIFIED_IN]->(e:Experiment)
            RETURN m, collect(distinct p) as properties, collect(distinct e) as experiments
            """
            params = {"id": molecule_id}
            
            result = await session.run(query, params)
            record = await result.single()
            
            if not record:
                return None
            
            return self._detailed_molecule_from_record(record)
    
    async def get_molecule_evidence(self, molecule_id: str) -> Optional[Dict[str, Any]]:
        async with self.driver.session() as session:
            query = """
            MATCH (m:Molecule {id: $id})-[:IDENTIFIED_IN]->(e:Experiment)
            OPTIONAL MATCH (e)-[:USED_TECHNIQUE]->(t:Technique)
            RETURN e, t
            """
            params = {"id": molecule_id}
            
            result = await session.run(query, params)
            records = await result.data()
            
            if not records:
                return None
            
            # Process evidence data
            evidence = {
                "molecule_id": molecule_id,
                "experiments": [],
                "technique_distribution": {}
            }
            
            for record in records:
                exp = record["e"]
                tech = record.get("t", {"name": "Unknown"})
                
                evidence["experiments"].append({
                    "id": exp["id"],
                    "name": exp["name"],
                    "technique": tech["name"],
                    "confidence": exp.get("confidence", 0.0),
                    "timestamp": exp.get("timestamp", None)
                })
                
                # Update technique distribution
                tech_name = tech["name"]
                if tech_name in evidence["technique_distribution"]:
                    evidence["technique_distribution"][tech_name] += 1
                else:
                    evidence["technique_distribution"][tech_name] = 1
            
            return evidence
    
    def _molecule_from_record(self, record):
        # Convert Neo4j node to dict
        props = dict(record)
        return {
            "id": props.get("id"),
            "name": props.get("name"),
            "formula": props.get("formula"),
            "evidence_score": props.get("evidence_score", 0.0),
            "properties": [],
            "experiments": []
        }
    
    def _detailed_molecule_from_record(self, record):
        molecule = self._molecule_from_record(record["m"])
        
        # Add properties
        molecule["properties"] = [
            {
                "name": p.get("name"),
                "value": p.get("value"),
                "confidence": p.get("confidence", 0.0)
            }
            for p in record["properties"] if p
        ]
        
        # Add experiments
        molecule["experiments"] = [
            {
                "id": e.get("id"),
                "name": e.get("name"),
                "technique": e.get("technique", "Unknown"),
                "confidence": e.get("confidence", 0.0)
            }
            for e in record["experiments"] if e
        ]
        
        return molecule
```

## Frontend Installation

1. Create the package.json file for the React frontend:

```json
{
  "name": "hegel-frontend",
  "version": "0.1.0",
  "private": true,
  "dependencies": {
    "@emotion/react": "^11.11.0",
    "@emotion/styled": "^11.11.0",
    "@mui/icons-material": "^5.11.16",
    "@mui/material": "^5.13.2",
    "@testing-library/jest-dom": "^5.16.5",
    "@testing-library/react": "^14.0.0",
    "@testing-library/user-event": "^14.4.3",
    "@types/d3": "^7.4.0",
    "@types/jest": "^29.5.1",
    "@types/node": "^20.2.5",
    "@types/react": "^18.2.7",
    "@types/react-dom": "^18.2.4",
    "@types/three": "^0.152.1",
    "axios": "^1.4.0",
    "d3": "^7.8.5",
    "dayjs": "^1.11.7",
    "notistack": "^3.0.1",
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "react-router-dom": "^6.11.2",
    "react-scripts": "5.0.1",
    "recharts": "^2.6.2",
    "three": "^0.152.2",
    "ts-loader": "^9.4.3",
    "typescript": "^5.0.4",
    "web-vitals": "^3.3.1",
    "zustand": "^4.3.8"
  },
  "scripts": {
    "start": "react-scripts start",
    "build": "react-scripts build",
    "test": "react-scripts test",
    "eject": "react-scripts eject"
  },
  "eslintConfig": {
    "extends": [
      "react-app",
      "react-app/jest"
    ]
  },
  "browserslist": {
    "production": [
      ">0.2%",
      "not dead",
      "not op_mini all"
    ],
    "development": [
      "last 1 chrome version",
      "last 1 firefox version",
      "last 1 safari version"
    ]
  },
  "proxy": "http://localhost:8000"
}
```

2. Create a basic NetworkGraph component (frontend/src/components/NetworkGraph.jsx):

```jsx
import React, { useEffect, useRef } from 'react';
import * as d3 from 'd3';

const NetworkGraph = ({ data, width = 800, height = 600, onNodeSelect }) => {
  const d3Container = useRef(null);

  useEffect(() => {
    if (data && d3Container.current) {
      // Clear previous graph
      d3.select(d3Container.current).selectAll("*").remove();
      
      // Create SVG container
      const svg = d3.select(d3Container.current)
        .append("svg")
        .attr("width", width)
        .attr("height", height)
        .append("g");
      
      // Add zoom behavior
      const zoom = d3.zoom()
        .scaleExtent([0.1, 8])
        .on("zoom", (event) => {
          svg.attr("transform", event.transform);
        });
      
      d3.select(d3Container.current).select("svg")
        .call(zoom);
      
      // Create force simulation
      const simulation = d3.forceSimulation(data.nodes)
        .force("link", d3.forceLink(data.links).id(d => d.id).distance(100))
        .force("charge", d3.forceManyBody().strength(-400))
        .force("center", d3.forceCenter(width / 2, height / 2));
      
      // Define node colors based on type
      const color = d3.scaleOrdinal(d3.schemeCategory10);
      
      // Add links
      const link = svg.append("g")
        .selectAll("line")
        .data(data.links)
        .enter()
        .append("line")
        .attr("stroke", "#999")
        .attr("stroke-opacity", 0.6)
        .attr("stroke-width", d => Math.sqrt(d.value || 1));
      
      // Add nodes
      const node = svg.append("g")
        .selectAll("circle")
        .data(data.nodes)
        .enter()
        .append("circle")
        .attr("r", 10)
        .attr("fill", d => color(d.type))
        .attr("stroke", "#fff")
        .attr("stroke-width", 1.5)
        .on("click", (event, d) => {
          if (onNodeSelect) {
            onNodeSelect(d);
          }
        })
        .call(d3.drag()
          .on("start", dragstarted)
          .on("drag", dragged)
          .on("end", dragended));
      
      // Add labels
      const label = svg.append("g")
        .selectAll("text")
        .data(data.nodes)
        .enter()
        .append("text")
        .attr("dx", 12)
        .attr("dy", ".35em")
        .text(d => d.name || d.id)
        .style("font-size", "10px")
        .style("fill", "#333");
      
      // Update simulation on tick
      simulation.on("tick", () => {
        link
          .attr("x1", d => d.source.x)
          .attr("y1", d => d.source.y)
          .attr("x2", d => d.target.x)
          .attr("y2", d => d.target.y);
        
        node
          .attr("cx", d => d.x)
          .attr("cy", d => d.y);
        
        label
          .attr("x", d => d.x)
          .attr("y", d => d.y);
      });
      
      // Drag functions
      function dragstarted(event, d) {
        if (!event.active) simulation.alphaTarget(0.3).restart();
        d.fx = d.x;
        d.fy = d.y;
      }
      
      function dragged(event, d) {
        d.fx = event.x;
        d.fy = event.y;
      }
      
      function dragended(event, d) {
        if (!event.active) simulation.alphaTarget(0);
        d.fx = null;
        d.fy = null;
      }
    }
  }, [data, width, height, onNodeSelect]);

  return (
    <div className="network-graph-container" ref={d3Container} style={{ width, height }} />
  );
};

export default NetworkGraph;
```

## Configuration Files

### Docker Compose File (docker-compose.yml)

```yaml
version: '3.8'

services:
  neo4j:
    image: neo4j:5.9.0
    ports:
      - "7474:7474"  # HTTP
      - "7687:7687"  # Bolt
    environment:
      - NEO4J_AUTH=neo4j/password
      - NEO4J_dbms_memory_heap_max__size=4G
    volumes:
      - neo4j-data:/data
      - neo4j-logs:/logs
    networks:
      - hegel-network

  elasticsearch:
    image: elasticsearch:8.8.0
    ports:
      - "9200:9200"
      - "9300:9300"
    environment:
      - discovery.type=single-node
      - xpack.security.enabled=false
      - "ES_JAVA_OPTS=-Xms1g -Xmx1g"
    volumes:
      - es-data:/usr/share/elasticsearch/data
    networks:
      - hegel-network

  redis:
    image: redis:7.0.11
    ports:
      - "6379:6379"
    volumes:
      - redis-data:/data
    networks:
      - hegel-network

  backend:
    build:
      context: .
      dockerfile: docker/backend/Dockerfile
    ports:
      - "8000:8000"
    environment:
      - NEO4J_URI=neo4j://neo4j:7687
      - NEO4J_USER=neo4j
      - NEO4J_PASSWORD=password
      - ELASTICSEARCH_URL=http://elasticsearch:9200
      - REDIS_URL=redis://redis:6379
    volumes:
      - ./backend:/app
    depends_on:
      - neo4j
      - elasticsearch
      - redis
    networks:
      - hegel-network

  frontend:
    build:
      context: .
      dockerfile: docker/frontend/Dockerfile
    ports:
      - "3000:80"
    depends_on:
      - backend
    networks:
      - hegel-network

networks:
  hegel-network:
    driver: bridge

volumes:
  neo4j-data:
  neo4j-logs:
  es-data:
  redis-data:
```

### Environment File (.env)

```
# Database connections
NEO4J_URI=neo4j://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=password
ELASTICSEARCH_URL=http://localhost:9200
REDIS_URL=redis://localhost:6379

# API settings
API_PORT=8000
API_HOST=0.0.0.0

# HuggingFace API
HUGGINGFACE_TOKEN=your_token_here

# LLM settings
LLM_API_URL=http://localhost:11434/api/generate
LLM_MODEL=llama2

# Development settings
DEBUG=true
LOG_LEVEL=debug
```

### Dockerfile for Backend (docker/backend/Dockerfile)

```dockerfile
FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Rust for maturin
RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
ENV PATH="/root/.cargo/bin:${PATH}"

# Copy requirements and install dependencies
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY backend/ .

# Expose port
EXPOSE 8000

# Command to run the API
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Dockerfile for Frontend (docker/frontend/Dockerfile)

```dockerfile
# Build stage
FROM node:18-alpine AS build

WORKDIR /app

# Copy package files and install dependencies
COPY frontend/package*.json ./
RUN npm ci

# Copy source files and build
COPY frontend/ ./
RUN npm run build

# Production stage
FROM nginx:alpine

# Copy built assets from build stage
COPY --from=build /app/build /usr/share/nginx/html

# Add nginx configuration
COPY docker/frontend/nginx.conf /etc/nginx/conf.d/default.conf

# Expose port
EXPOSE 80

# Start nginx
CMD ["nginx", "-g", "daemon off;"]
```

### Nginx Configuration for Frontend (docker/frontend/nginx.conf)

```nginx
server {
    listen 80;
    server_name localhost;

    root /usr/share/nginx/html;
    index index.html;

    # Serve static files
    location / {
        try_files $uri $uri/ /index.html;
    }

    # Proxy API requests to backend
    location /api/ {
        proxy_pass http://backend:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## Development Workflow

1. Setup the development environment:

```bash
# Clone the repository
git clone https://github.com/yourusername/hegel.git
cd hegel

# Run the setup script
./scripts/setup.sh

# Activate the Python virtual environment
source venv/bin/activate
```

2. Start the databases:

```bash
docker-compose up -d neo4j elasticsearch redis
```

3. Start the backend:

```bash
cd backend
uvicorn api.main:app --reload
```

4. Start the frontend:

```bash
cd frontend
npm start
```

5. Build and run the Rust core:

```bash
cd core
cargo build
cargo run -- interactive
```

## Initial Data Setup

1. Create a script to initialize the Neo4j database with a basic schema (scripts/init_neo4j.py):

```python
from neo4j import GraphDatabase
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Connect to Neo4j
uri = os.getenv("NEO4J_URI", "neo4j://localhost:7687")
user = os.getenv("NEO4J_USER", "neo4j")
password = os.getenv("NEO4J_PASSWORD", "password")
driver = GraphDatabase.driver(uri, auth=(user, password))

def create_schema():
    with driver.session() as session:
        # Create constraints
        session.run("CREATE CONSTRAINT molecule_id IF NOT EXISTS FOR (m:Molecule) REQUIRE m.id IS UNIQUE")
        session.run("CREATE CONSTRAINT experiment_id IF NOT EXISTS FOR (e:Experiment) REQUIRE e.id IS UNIQUE")
        session.run("CREATE CONSTRAINT technique_name IF NOT EXISTS FOR (t:Technique) REQUIRE t.name IS UNIQUE")
        
        # Create indices
        session.run("CREATE INDEX molecule_name IF NOT EXISTS FOR (m:Molecule) ON (m.name)")
        session.run("CREATE INDEX experiment_name IF NOT EXISTS FOR (e:Experiment) ON (e.name)")
        
        print("Schema created successfully")

def create_sample_data():
    with driver.session() as session:
        # Create techniques
        techniques = [
            {"name": "MS/MS", "description": "Tandem Mass Spectrometry"},
            {"name": "NMR", "description": "Nuclear Magnetic Resonance"},
            {"name": "Chromatography", "description": "Separation technique"},
            {"name": "Microscopy", "description": "Visual observation technique"}
        ]
        
        for tech in techniques:
            session.run(
                "MERGE (t:Technique {name: $name}) SET t.description = $description",
                tech
            )
        
        # Create molecules
        molecules = [
            {
                "id": "M001", 
                "name": "Glucose", 
                "formula": "C6H12O6",
                "evidence_score": 0.92
            },
            {
                "id": "M002", 
                "name": "Hemoglobin", 
                "formula": "C2932H4724N828O840S8Fe4",
                "evidence_score": 0.87
            },
            {
                "id": "M003", 
                "name": "Adenosine triphosphate", 
                "formula": "C10H16N5O13P3",
                "evidence_score": 0.78
            }
        ]
        
        for mol in molecules:
            session.run(
                """
                MERGE (m:Molecule {id: $id}) 
                SET m.name = $name,
                    m.formula = $formula,
                    m.evidence_score = $evidence_score
                """,
                mol
            )
        
        # Create experiments
        experiments = [
            {
                "id": "E001", 
                "name": "Blood plasma MS analysis", 
                "technique": "MS/MS",
                "confidence": 0.89
            },
            {
                "id": "E002", 
                "name": "Cell culture metabolomics", 
                "technique": "Chromatography",
                "confidence": 0.76
            },
            {
                "id": "E003", 
                "name": "Protein structure analysis", 
                "technique": "NMR",
                "confidence": 0.92
            },
            {
                "id": "E004", 
                "name": "Cell imaging", 
                "technique": "Microscopy",
                "confidence": 0.85
            }
        ]
        
        for exp in experiments:
            session.run(
                """
                MERGE (e:Experiment {id: $id}) 
                SET e.name = $name,
                    e.confidence = $confidence
                WITH e
                MATCH (t:Technique {name: $technique})
                MERGE (e)-[:USED_TECHNIQUE]->(t)
                """,
                exp
            )
        
        # Connect molecules to experiments
        relationships = [
            {"molecule": "M001", "experiment": "E001"},
            {"molecule": "M001", "experiment": "E002"},
            {"molecule": "M002", "experiment": "E001"},
            {"molecule": "M002", "experiment": "E003"},
            {"molecule": "M002", "experiment": "E004"},
            {"molecule": "M003", "experiment": "E002"}
        ]
        
        for rel in relationships:
            session.run(
                """
                MATCH (m:Molecule {id: $molecule})
                MATCH (e:Experiment {id: $experiment})
                MERGE (m)-[:IDENTIFIED_IN]->(e)
                """,
                rel
            )
        
        # Add properties to molecules
        properties = [
            {"molecule": "M001", "name": "Molecular weight", "value": "180.16 g/mol", "confidence": 0.99},
            {"molecule": "M001", "name": "Solubility", "value": "Water soluble", "confidence": 0.95},
            {"molecule": "M002", "name": "Molecular weight", "value": "64458 g/mol", "confidence": 0.92},
            {"molecule": "M002", "name": "Function", "value": "Oxygen transport", "confidence": 0.98},
            {"molecule": "M003", "name": "Molecular weight", "value": "507.18 g/mol", "confidence": 0.97},
            {"molecule": "M003", "name": "Function", "value": "Energy storage", "confidence": 0.96}
        ]
        
        for prop in properties:
            session.run(
                """
                MATCH (m:Molecule {id: $molecule})
                MERGE (p:Property {name: $name, value: $value, molecule_id: $molecule})
                SET p.confidence = $confidence
                MERGE (m)-[:HAS_PROPERTY]->(p)
                """,
                prop
            )
        
        # Add molecule relationships
        molecule_relationships = [
            {"source": "M001", "target": "M003", "type": "METABOLIC_PRECURSOR", "confidence": 0.82},
            {"source": "M002", "target": "M001", "type": "BINDS_TO", "confidence": 0.67}
        ]
        
        for rel in molecule_relationships:
            session.run(
                """
                MATCH (m1:Molecule {id: $source})
                MATCH (m2:Molecule {id: $target})
                MERGE (m1)-[r:RELATED_TO {type: $type}]->(m2)
                SET r.confidence = $confidence
                """,
                rel
            )
        
        print("Sample data created successfully")

if __name__ == "__main__":
    try:
        create_schema()
        create_sample_data()
    except Exception as e:
        print(f"Error: {e}")
    finally:
        driver.close()
```

Run the initialization script:

```bash
python scripts/init_neo4j.py
```

## Next Steps

1. Implement the remaining core functionality in Rust
2. Set up the ML models in the Python backend
3. Complete the frontend visualizations
4. Integrate the three layers: core, backend, and frontend

This setup provides a strong foundation for developing the Hegel platform with a Rust-based metacognitive orchestration layer, Python backend services, and a React frontend for visualization.

# Hugging Face Integration

This section outlines how to integrate specialized AI models from Hugging Face with the Hegel platform.

## ML Models Configuration

1. Create a specialized ML model manager (backend/ml/models/model_manager.py):

```python
import os
import torch
import logging
from transformers import AutoModel, AutoTokenizer, pipeline
from huggingface_hub import login, HfApi

logger = logging.getLogger(__name__)

class ModelManager:
    def __init__(self):
        # Initialize with empty models dictionary
        self.models = {}
        self.tokenizers = {}
        
        # Login to Hugging Face if token is available
        hf_token = os.getenv("HUGGINGFACE_TOKEN")
        if hf_token:
            login(token=hf_token)
            logger.info("Logged in to Hugging Face Hub")
        else:
            logger.warning("No Hugging Face token found. Some models may not be available.")
    
    def load_model(self, model_name, model_id, task=None):
        """Load a model from Hugging Face Hub"""
        try:
            logger.info(f"Loading model {model_id} for {model_name}")
            
            if task:
                # Use pipeline for specific tasks
                self.models[model_name] = pipeline(task, model=model_id)
                logger.info(f"Loaded {model_name} using pipeline for task: {task}")
            else:
                # Load model and tokenizer directly
                self.tokenizers[model_name] = AutoTokenizer.from_pretrained(model_id)
                self.models[model_name] = AutoModel.from_pretrained(model_id)
                logger.info(f"Loaded {model_name} model and tokenizer")
            
            return True
        except Exception as e:
            logger.error(f"Failed to load model {model_id}: {str(e)}")
            return False
    
    def get_model(self, model_name):
        """Get a loaded model by name"""
        return self.models.get(model_name)
    
    def get_tokenizer(self, model_name):
        """Get a loaded tokenizer by name"""
        return self.tokenizers.get(model_name)
    
    def run_inference(self, model_name, inputs, **kwargs):
        """Run inference with a specific model"""
        model = self.get_model(model_name)
        
        if not model:
            raise ValueError(f"Model {model_name} not found or not loaded")
        
        # Handle different model types
        if isinstance(model, pipeline):
            # For pipeline models
            return model(inputs, **kwargs)
        else:
            # For raw models with tokenizers
            tokenizer = self.get_tokenizer(model_name)
            if not tokenizer:
                raise ValueError(f"Tokenizer for {model_name} not found")
            
            # Prepare inputs
            tokenized = tokenizer(inputs, return_tensors="pt", padding=True, truncation=True)
            
            # Run model
            with torch.no_grad():
                outputs = model(**tokenized)
            
            return outputs
    
    def initialize_default_models(self):
        """Initialize default models used by the system"""
        # Spectrum analysis model
        self.load_model(
            "spectra_analyzer", 
            "specialized/ms-spectra-model",  # Replace with actual model ID
            task="zero-shot-classification"
        )
        
        # Molecule similarity model
        self.load_model(
            "molecule_mapper",
            "specialized/molecule-similarity",  # Replace with actual model ID
        )
        
        # Evidence evaluator
        self.load_model(
            "evidence_evaluator",
            "specialized/evidence-transformer",  # Replace with actual model ID
            task="text-classification"
        )
        
        # Confidence estimator
        self.load_model(
            "confidence_estimator",
            "specialized/confidence-bert",  # Replace with actual model ID
            task="text-classification"
        )
        
        logger.info("Initialized default models")

# Singleton instance
model_manager = ModelManager()
```

2. Create a specialized ML model for MS/MS spectra analysis (backend/ml/models/spectranet.py):

```python
import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
from typing import Tuple, List, Dict, Any

class SpectraNet(nn.Module):
    def __init__(self, input_dim=2048, hidden_dims=[1024, 512, 256], num_classes=1000):
        super().__init__()
        self.input_dim = input_dim
        self.hidden_dims = hidden_dims
        self.num_classes = num_classes
        
        # Feature extraction layers
        layers = []
        prev_dim = input_dim
        
        for hidden_dim in hidden_dims:
            layers.append(nn.Linear(prev_dim, hidden_dim))
            layers.append(nn.BatchNorm1d(hidden_dim))
            layers.append(nn.ReLU())
            layers.append(nn.Dropout(0.2))
            prev_dim = hidden_dim
        
        self.feature_extractor = nn.Sequential(*layers)
        
        # Classification head
        self.classifier = nn.Linear(hidden_dims[-1], num_classes)
    
    def forward(self, x: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        # Extract features
        features = self.feature_extractor(x)
        
        # Predict classes
        logits = self.classifier(features)
        
        return logits, features

class SpectraProcessor:
    def __init__(self, model_path: str = None):
        """Initialize with a pre-trained model or create a new one"""
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        
        if model_path:
            self.model = self._load_model(model_path)
        else:
            self.model = SpectraNet().to(self.device)
        
        # Class mapping (replace with actual molecule names)
        self.idx_to_molecule = {i: f"Molecule_{i}" for i in range(1000)}
    
    def _load_model(self, model_path: str) -> SpectraNet:
        """Load a pre-trained model"""
        model = SpectraNet()
        model.load_state_dict(torch.load(model_path, map_location=self.device))
        model = model.to(self.device)
        model.eval()
        return model
    
    def preprocess_spectrum(self, spectrum_data: np.ndarray) -> torch.Tensor:
        """Preprocess raw spectrum data for the model"""
        # Convert to tensor
        tensor = torch.from_numpy(spectrum_data).float()
        
        # Normalize
        if tensor.dim() == 1:
            tensor = tensor.unsqueeze(0)  # Add batch dimension
        
        # Resize if necessary
        if tensor.shape[1] != self.model.input_dim:
            # Resample to match input dimensions
            tensor = F.interpolate(tensor.unsqueeze(1), size=self.model.input_dim, mode='linear').squeeze(1)
        
        return tensor.to(self.device)
    
    def analyze(self, spectrum_data: np.ndarray) -> Dict[str, Any]:
        """Analyze a spectrum and identify molecules"""
        # Preprocess
        tensor = self.preprocess_spectrum(spectrum_data)
        
        # Run inference
        with torch.no_grad():
            logits, features = self.model(tensor)
            probabilities = F.softmax(logits, dim=1)
        
        # Get top k predictions
        k = 5
        top_probs, top_indices = torch.topk(probabilities, k)
        
        # Prepare results
        results = {
            "molecules": [
                {
                    "id": self.idx_to_molecule[idx.item()],
                    "name": self.idx_to_molecule[idx.item()],
                    "confidence": prob.item()
                }
                for idx, prob in zip(top_indices[0], top_probs[0])
            ],
            "features": features[0].cpu().numpy().tolist()
        }
        
        return results
```

3. Create a training script for the SpectraNet model (backend/ml/training/train_spectranet.py):

```python
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, Dataset
import numpy as np
import os
import argparse
from tqdm import tqdm
import json
from pathlib import Path

# Import our model
from models.spectranet import SpectraNet

class SpectraDataset(Dataset):
    def __init__(self, data_dir, transform=None):
        """
        Args:
            data_dir: Directory with subdirectories for each class containing spectra files
            transform: Optional transform to be applied on a sample
        """
        self.data_dir = Path(data_dir)
        self.transform = transform
        self.samples = []
        self.class_to_idx = {}
        
        # Scan directory for classes
        for i, class_dir in enumerate(sorted([d for d in self.data_dir.iterdir() if d.is_dir()])):
            class_name = class_dir.name
            self.class_to_idx[class_name] = i
            
            # Add all spectrum files in this class
            for spectrum_file in class_dir.glob("*.npy"):
                self.samples.append((spectrum_file, i))
        
        print(f"Loaded dataset with {len(self.samples)} samples across {len(self.class_to_idx)} classes")
    
    def __len__(self):
        return len(self.samples)
    
    def __getitem__(self, idx):
        spectrum_path, label = self.samples[idx]
        
        # Load spectrum data
        spectrum = np.load(spectrum_path)
        
        # Apply transforms if any
        if self.transform:
            spectrum = self.transform(spectrum)
        
        # Convert to tensor
        spectrum = torch.from_numpy(spectrum).float()
        
        return spectrum, label

def train(args):
    # Set device
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Using device: {device}")
    
    # Create datasets and dataloaders
    train_dataset = SpectraDataset(args.train_dir)
    val_dataset = SpectraDataset(args.val_dir)
    
    train_loader = DataLoader(train_dataset, batch_size=args.batch_size, shuffle=True, num_workers=4)
    val_loader = DataLoader(val_dataset, batch_size=args.batch_size, shuffle=False, num_workers=4)
    
    # Create model
    model = SpectraNet(
        input_dim=args.input_dim, 
        hidden_dims=args.hidden_dims, 
        num_classes=len(train_dataset.class_to_idx)
    ).to(device)
    
    # Define loss function and optimizer
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(model.parameters(), lr=args.learning_rate)
    scheduler = optim.lr_scheduler.ReduceLROnPlateau(optimizer, 'min', patience=5)
    
    # Save class to index mapping
    os.makedirs(args.output_dir, exist_ok=True)
    with open(os.path.join(args.output_dir, 'class_to_idx.json'), 'w') as f:
        json.dump(train_dataset.class_to_idx, f)
    
    # Training loop
    best_val_loss = float('inf')
    
    for epoch in range(args.epochs):
        # Training phase
        model.train()
        train_loss = 0.0
        correct = 0
        total = 0
        
        progress_bar = tqdm(train_loader, desc=f"Epoch {epoch+1}/{args.epochs}")
        for inputs, labels in progress_bar:
            inputs, labels = inputs.to(device), labels.to(device)
            
            # Zero the parameter gradients
            optimizer.zero_grad()
            
            # Forward
            logits, _ = model(inputs)
            loss = criterion(logits, labels)
            
            # Backward + optimize
            loss.backward()
            optimizer.step()
            
            # Statistics
            train_loss += loss.item() * inputs.size(0)
            _, predicted = torch.max(logits, 1)
            total += labels.size(0)
            correct += (predicted == labels).sum().item()
            
            progress_bar.set_postfix({'loss': loss.item(), 'acc': 100 * correct / total})
        
        train_loss = train_loss / len(train_loader.dataset)
        train_acc = 100 * correct / total
        
        # Validation phase
        model.eval()
        val_loss = 0.0
        correct = 0
        total = 0
        
        with torch.no_grad():
            for inputs, labels in val_loader:
                inputs, labels = inputs.to(device), labels.to(device)
                
                # Forward
                logits, _ = model(inputs)
                loss = criterion(logits, labels)
                
                # Statistics
                val_loss += loss.item() * inputs.size(0)
                _, predicted = torch.max(logits, 1)
                total += labels.size(0)
                correct += (predicted == labels).sum().item()
        
        val_loss = val_loss / len(val_loader.dataset)
        val_acc = 100 * correct / total
        
        # Update scheduler
        scheduler.step(val_loss)
        
        print(f"Epoch {epoch+1}/{args.epochs} => Train Loss: {train_loss:.4f}, Train Acc: {train_acc:.2f}%, Val Loss: {val_loss:.4f}, Val Acc: {val_acc:.2f}%")
        
        # Save best model
        if val_loss < best_val_loss:
            best_val_loss = val_loss
            torch.save(model.state_dict(), os.path.join(args.output_dir, 'best_model.pth'))
            print(f"Saved best model with validation loss: {val_loss:.4f}")
    
    # Save final model
    torch.save(model.state_dict(), os.path.join(args.output_dir, 'final_model.pth'))
    print("Training completed!")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train SpectraNet model")
    parser.add_argument('--train_dir', type=str, required=True, help='Directory with training data')
    parser.add_argument('--val_dir', type=str, required=True, help='Directory with validation data')
    parser.add_argument('--output_dir', type=str, default='./models', help='Output directory for model')
    parser.add_argument('--input_dim', type=int, default=2048, help='Input dimension for spectra')
    parser.add_argument('--hidden_dims', type=int, nargs='+', default=[1024, 512, 256], help='Hidden dimensions')
    parser.add_argument('--batch_size', type=int, default=32, help='Batch size')
    parser.add_argument('--learning_rate', type=float, default=0.001, help='Learning rate')
    parser.add_argument('--epochs', type=int, default=50, help='Number of epochs')
    
    args = parser.parse_args()
    train(args)
```

## Metacognitive Orchestration Integration

1. Create the main Rust orchestration module for integrating with HuggingFace (core/src/metacognition/llm.rs):

```rust
use anyhow::{anyhow, Result};
use reqwest::Client;
use serde::{Deserialize, Serialize};
use std::env;
use std::time::Duration;

#[derive(Debug, Serialize, Deserialize)]
pub struct LLMRequest {
    pub model: String,
    pub prompt: String,
    pub temperature: f32,
    pub max_tokens: u32,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct LLMResponse {
    pub text: String,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct OllamaRequest {
    pub model: String,
    pub prompt: String,
    pub options: OllamaOptions,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct OllamaOptions {
    pub temperature: f32,
    pub num_predict: u32,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct OllamaResponse {
    pub response: String,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct HuggingFaceRequest {
    pub inputs: String,
    pub parameters: HuggingFaceParameters,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct HuggingFaceParameters {
    pub temperature: f32,
    pub max_new_tokens: u32,
    pub return_full_text: bool,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct HuggingFaceResponse {
    pub generated_text: String,
}

pub struct LLMClient {
    client: Client,
    ollama_url: String,
    hf_url: String,
    hf_token: Option<String>,
}

impl LLMClient {
    pub fn new() -> Self {
        let client = Client::builder()
            .timeout(Duration::from_secs(60))
            .build()
            .expect("Failed to create HTTP client");
        
        let ollama_url = env::var("LLM_API_URL")
            .unwrap_or_else(|_| "http://localhost:11434/api/generate".to_string());
        
        let hf_url = env::var("HUGGINGFACE_API_URL")
            .unwrap_or_else(|_| "https://api-inference.huggingface.co/models".to_string());
        
        let hf_token = env::var("HUGGINGFACE_TOKEN").ok();
        
        Self {
            client,
            ollama_url,
            hf_url,
            hf_token,
        }
    }
    
    pub async fn decide(&self, command: &str, context: &str) -> Result<crate::metacognition::decision::Decision> {
        let prompt = format!(
            "Based on the command and context, determine the appropriate action to take.
            
            Command: {}
            
            Context: {}
            
            Respond with a JSON object containing the decision type and parameters.
            Decision types: ProcessFile, QueryMolecule, RunAnalysis
            
            Example:
            {{
                \"type\": \"ProcessFile\",
                \"parameters\": {{
                    \"path\": \"/path/to/file.mzML\"
                }}
            }}
            ",
            command, context
        );
        
        // Get response from LLM
        let llm_response = self.query_ollama("llama2", &prompt, 0.7, 500).await?;
        
        // Try to parse the decision
        let json_start = llm_response.find('{').ok_or_else(|| anyhow!("No JSON found in response"))?;
        let json_end = llm_response.rfind('}').ok_or_else(|| anyhow!("No JSON end found in response"))?;
        let json_str = &llm_response[json_start..=json_end];
        
        // Parse the decision
        let decision: crate::metacognition::decision::Decision = serde_json::from_str(json_str)?;
        
        Ok(decision)
    }
    
    pub async fn query_ollama(&self, model: &str, prompt: &str, temperature: f32, max_tokens: u32) -> Result<String> {
        let request = OllamaRequest {
            model: model.to_string(),
            prompt: prompt.to_string(),
            options: OllamaOptions {
                temperature,
                num_predict: max_tokens,
            },
        };
        
        let response = self.client
            .post(&self.ollama_url)
            .json(&request)
            .send()
            .await?;
        
        if !response.status().is_success() {
            return Err(anyhow!("Ollama API error: {}", response.status()));
        }
        
        let ollama_response: OllamaResponse = response.json().await?;
        Ok(ollama_response.response)
    }
    
    pub async fn query_huggingface(&self, model_id: &str, prompt: &str, temperature: f32, max_tokens: u32) -> Result<String> {
        let request = HuggingFaceRequest {
            inputs: prompt.to_string(),
            parameters: HuggingFaceParameters {
                temperature,
                max_new_tokens: max_tokens,
                return_full_text: false,
            },
        };
        
        let mut req_builder = self.client
            .post(&format!("{}/{}", self.hf_url, model_id))
            .json(&request);
        
        // Add token if available
        if let Some(token) = &self.hf_token {
            req_builder = req_builder.header("Authorization", format!("Bearer {}", token));
        }
        
        let response = req_builder.send().await?;
        
        if !response.status().is_success() {
            return Err(anyhow!("HuggingFace API error: {}", response.status()));
        }
        
        let hf_response: HuggingFaceResponse = response.json().await?;
        Ok(hf_response.generated_text)
    }
}
```

2. Create the decision engine module (core/src/metacognition/decision.rs):

```rust
use serde::{Deserialize, Serialize};
use std::path::PathBuf;

#[derive(Debug, Serialize, Deserialize)]
#[serde(tag = "type", content = "parameters")]
pub enum Decision {
    #[serde(rename = "ProcessFile")]
    ProcessFile(ProcessFileParams),
    
    #[serde(rename = "QueryMolecule")]
    QueryMolecule(QueryMoleculeParams),
    
    #[serde(rename = "RunAnalysis")]
    RunAnalysis(RunAnalysisParams),
}

#[derive(Debug, Serialize, Deserialize)]
pub struct ProcessFileParams {
    pub path: String,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct QueryMoleculeParams {
    pub id: String,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct RunAnalysisParams {
    pub analysis_type: String,
    pub parameters: serde_json::Value,
}

pub struct DecisionEngine {
    // Configuration for the decision engine
}

impl DecisionEngine {
    pub fn new() -> Self {
        Self {}
    }
    
    pub fn validate_decision(&self, decision: &Decision) -> anyhow::Result<()> {
        match decision {
            Decision::ProcessFile(params) => {
                let path = PathBuf::from(&params.path);
                if !path.exists() {
                    return Err(anyhow::anyhow!("File not found: {}", params.path));
                }
            },
            Decision::QueryMolecule(params) => {
                if params.id.is_empty() {
                    return Err(anyhow::anyhow!("Molecule ID cannot be empty"));
                }
            },
            Decision::RunAnalysis(params) => {
                if params.analysis_type.is_empty() {
                    return Err(anyhow::anyhow!("Analysis type cannot be empty"));
                }
            },
        }
        
        Ok(())
    }
}
```

## Integration Testing

1. Create an integration test for the Rust core and Python backend (core/tests/integration_test.rs):

```rust
use hegel_core::Orchestrator;
use std::process::Command;
use std::thread;
use std::time::Duration;

#[tokio::test]
async fn test_core_with_backend() {
    // Start the backend in a separate process
    let backend_process = Command::new("python")
        .args(&["-m", "uvicorn", "backend.api.main:app", "--port", "8001"])
        .spawn()
        .expect("Failed to start backend");
    
    // Allow backend to start
    thread::sleep(Duration::from_secs(3));
    
    // Create orchestrator
    let mut orchestrator = Orchestrator::new();
    
    // Test command
    let result = orchestrator.process_command("list molecules").await;
    assert!(result.is_ok(), "Command failed: {:?}", result.err());
    
    // Check result
    let result_str = result.unwrap();
    assert!(result_str.contains("molecules"), "Unexpected result: {}", result_str);
    
    // Terminate backend
    backend_process.kill().expect("Failed to kill backend process");
}
```

## Deployment

### Production Deployment

1. Prepare your server environment:

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker and Docker Compose
sudo apt install -y docker.io docker-compose

# Install development tools
sudo apt install -y build-essential python3-dev
```

2. Clone the repository and build the containers:

```bash
git clone https://github.com/yourusername/hegel.git
cd hegel

# Build and start containers
docker-compose up -d
```

3. Set up HTTPS with Nginx and Let's Encrypt:

```bash
# Install Nginx and certbot
sudo apt install -y nginx certbot python3-certbot-nginx

# Configure Nginx
sudo nano /etc/nginx/sites-available/hegel
```

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /api/ {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

```bash
sudo ln -s /etc/nginx/sites-available/hegel /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx

# Set up SSL
sudo certbot --nginx -d your-domain.com
```

### Local Development with Docker

For local development with Docker:

```bash
# Build and start containers in development mode
docker-compose -f docker-compose.dev.yml up
```

## Troubleshooting

### Database Connection Issues

If you encounter Neo4j connection issues:

```bash
# Check if Neo4j is running
docker ps | grep neo4j

# Check Neo4j logs
docker logs hegel_neo4j_1

# Reset Neo4j password
docker exec -it hegel_neo4j_1 cypher-shell -u neo4j -p password
```

### Memory Issues with Large Files

If you encounter memory issues when processing large files:

1. Adjust the memory limits in docker-compose.yml:

```yaml
services:
  backend:
    # ...
    deploy:
      resources:
        limits:
          memory: 4G
```

2. Configure the streaming chunk size in the processing module:

```python
# In backend/processing/ingest.py
CHUNK_SIZE = 1024 * 1024 * 10  # 10MB chunks
```

### Rust Build Issues

If you encounter issues building the Rust core:

```bash
# Clear Cargo cache
cargo clean

# Update Rust
rustup update

# Check for dependency issues
cargo check -v
```

## Final Steps

After setting up the project, complete these final steps:

1. Initialize the graph database:

```bash
python scripts/init_neo4j.py
```

2. Initialize the default ML models:

```python
from backend.ml.models.model_manager import model_manager
model_manager.initialize_default_models()
```

3. Start the development environment:

```bash
# Start the backend
cd backend
uvicorn api.main:app --reload

# Start the frontend
cd frontend
npm start

# Start the Rust core
cd core
cargo run -- interactive
```

Your Hegel molecular identity validation platform is now set up and ready for development!
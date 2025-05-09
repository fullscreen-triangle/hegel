from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import logging
import os
from dotenv import load_dotenv
from neo4j import AsyncGraphDatabase

from .routes import molecules
from .routes import visualization
from .services.molecule_network import MoleculeNetworkBuilder, molecule_network
from .routes import experiments, auth

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Hegel API",
    description="API for Hegel - Evidence Rectification Framework for Biological Molecules",
    version="0.1.0",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins in development
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Include routers
app.include_router(molecules.router)
app.include_router(visualization.router)
app.include_router(experiments.router)
app.include_router(auth.router)

# Initialize Neo4j connection
@app.on_event("startup")
async def startup_db_client():
    """Initialize the Neo4j database connection and molecule network on startup."""
    global molecule_network
    
    # Get Neo4j connection details from environment
    neo4j_uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    neo4j_user = os.getenv("NEO4J_USER", "neo4j")
    neo4j_password = os.getenv("NEO4J_PASSWORD", "password")
    
    try:
        # Initialize the molecule network service
        molecule_network = MoleculeNetworkBuilder(neo4j_uri, neo4j_user, neo4j_password)
        
        # Test connection
        if not await molecule_network.check_connection():
            logger.error("Failed to connect to Neo4j database")
        else:
            logger.info("Successfully connected to Neo4j database")
            
    except Exception as e:
        logger.error(f"Error initializing Neo4j connection: {str(e)}")
        molecule_network = None

@app.on_event("shutdown")
async def shutdown_db_client():
    """Close the Neo4j database connection on shutdown."""
    global molecule_network
    
    if molecule_network:
        try:
            await molecule_network.driver.close()
            logger.info("Neo4j connection closed")
        except Exception as e:
            logger.error(f"Error closing Neo4j connection: {str(e)}")

@app.get("/health")
async def health_check():
    """Basic health check endpoint."""
    return {"status": "healthy", "db_connected": molecule_network is not None}

@app.get("/", tags=["status"])
async def root():
    """Root endpoint to check API status"""
    return {
        "status": "operational",
        "message": "Welcome to Hegel API - Evidence Rectification Framework for Biological Molecules",
        "version": "0.1.0"
    } 
"""
Database connection module for Neo4j integration
"""

import os
from neo4j import AsyncGraphDatabase, GraphDatabase
from fastapi import Depends
from typing import Optional, AsyncGenerator

# Neo4j connection settings
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://neo4j:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")

# Database connection class
class Database:
    def __init__(self):
        self.driver = None
        self.async_driver = None

    async def connect(self):
        """Connect to Neo4j database"""
        try:
            self.driver = GraphDatabase.driver(
                NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD)
            )
            self.async_driver = AsyncGraphDatabase.driver(
                NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD)
            )
            # Verify connection
            with self.driver.session() as session:
                result = session.run("RETURN 'Connected' AS status")
                record = result.single()
                if record and record["status"] == "Connected":
                    print("Connected to Neo4j database")
                else:
                    print("Failed to verify Neo4j connection")
        except Exception as e:
            print(f"Failed to connect to Neo4j: {e}")
            raise

    async def close(self):
        """Close the database connection"""
        if self.driver:
            self.driver.close()
        if self.async_driver:
            await self.async_driver.close()

    def get_session(self):
        """Get a synchronous session"""
        return self.driver.session()

    async def get_async_session(self):
        """Get an asynchronous session"""
        return self.async_driver.session()

    async def run_query(self, query, params=None):
        """Run a Cypher query"""
        async with self.async_driver.session() as session:
            result = await session.run(query, params or {})
            records = await result.values()
            return records

# Database instance
db = Database()

async def init_db():
    """Initialize the database connection"""
    await db.connect()
    await setup_constraints()

async def setup_constraints():
    """Set up database constraints and indexes"""
    # Create constraints for unique IDs
    constraints = [
        "CREATE CONSTRAINT molecule_id IF NOT EXISTS FOR (m:Molecule) REQUIRE m.id IS UNIQUE",
        "CREATE CONSTRAINT pathway_id IF NOT EXISTS FOR (p:Pathway) REQUIRE p.id IS UNIQUE",
        "CREATE CONSTRAINT reaction_id IF NOT EXISTS FOR (r:Reaction) REQUIRE r.id IS UNIQUE",
        "CREATE CONSTRAINT evidence_id IF NOT EXISTS FOR (e:Evidence) REQUIRE e.id IS UNIQUE",
    ]

    for constraint in constraints:
        try:
            await db.run_query(constraint)
        except Exception as e:
            print(f"Error creating constraint: {e}")

    # Create indexes for improved performance
    indexes = [
        "CREATE INDEX molecule_name IF NOT EXISTS FOR (m:Molecule) ON (m.name)",
        "CREATE INDEX molecule_formula IF NOT EXISTS FOR (m:Molecule) ON (m.formula)",
        "CREATE INDEX pathway_name IF NOT EXISTS FOR (p:Pathway) ON (p.name)",
    ]

    for index in indexes:
        try:
            await db.run_query(index)
        except Exception as e:
            print(f"Error creating index: {e}")

async def get_db():
    """Database dependency for routes"""
    try:
        yield db
    finally:
        # Connection is managed globally, so we don't close it here
        pass 
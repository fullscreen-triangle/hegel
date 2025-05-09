"""
Hegel API - Backend service for the Hegel Molecular Evidence Rectification Framework
"""

import os
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from .routes import molecules, evidence, rectification, visualization, auth
from .models.database import init_db, get_db

# Initialize FastAPI application
app = FastAPI(
    title="Hegel API",
    description="API for the Hegel Evidence Rectification Framework for Biological Molecules",
    version="0.1.0",
)

# Configure CORS
origins = [
    "http://localhost:3000",
    "http://localhost:8080",
    os.getenv("FRONTEND_URL", "http://localhost:3000"),
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(molecules.router, prefix="/api/molecules", tags=["Molecules"])
app.include_router(evidence.router, prefix="/api/evidence", tags=["Evidence"])
app.include_router(rectification.router, prefix="/api/rectification", tags=["Rectification"])
app.include_router(visualization.router, prefix="/api/visualization", tags=["Visualization"])

@app.on_event("startup")
async def startup_event():
    """Initialize the database connection on startup"""
    await init_db()

@app.on_event("shutdown")
async def shutdown_event():
    """Close the database connection on shutdown"""
    # Any cleanup operations can be added here
    pass

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "version": app.version}

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler"""
    return JSONResponse(
        status_code=500,
        content={"detail": str(exc)},
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)

"""
Pydantic schemas for API data validation
"""

from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any, Union
from enum import Enum
from datetime import datetime
import uuid

# Enum definitions
class EvidenceType(str, Enum):
    SPECTRAL = "spectral"
    SEQUENCE = "sequence"
    STRUCTURAL = "structural"
    PATHWAY = "pathway"
    LITERATURE = "literature"

class UserRole(str, Enum):
    ADMIN = "admin"
    RESEARCHER = "researcher"
    VIEWER = "viewer"

# Base schemas
class MoleculeBase(BaseModel):
    name: str
    formula: str
    smiles: Optional[str] = None
    inchi: Optional[str] = None
    description: Optional[str] = None

class EvidenceBase(BaseModel):
    source: str
    confidence: float = Field(ge=0.0, le=1.0)
    evidence_type: EvidenceType
    value: str
    metadata: Optional[Dict[str, Any]] = None

class PathwayBase(BaseModel):
    name: str
    description: Optional[str] = None
    source: Optional[str] = None

class ReactionBase(BaseModel):
    name: str
    description: Optional[str] = None
    reaction_type: Optional[str] = None

# Create schemas
class MoleculeCreate(MoleculeBase):
    pass

class EvidenceCreate(EvidenceBase):
    molecule_id: str

class PathwayCreate(PathwayBase):
    pass

class ReactionCreate(ReactionBase):
    pathway_id: str
    reactants: List[str]
    products: List[str]

# Response schemas
class Evidence(EvidenceBase):
    id: str
    molecule_id: str
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        orm_mode = True

class Molecule(MoleculeBase):
    id: str
    confidence_score: float = 0.0
    evidences: List[Evidence] = []
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        orm_mode = True

class Pathway(PathwayBase):
    id: str
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        orm_mode = True

class Reaction(ReactionBase):
    id: str
    pathway_id: str
    reactants: List[str]
    products: List[str]
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        orm_mode = True

# Update schemas
class MoleculeUpdate(BaseModel):
    name: Optional[str] = None
    formula: Optional[str] = None
    smiles: Optional[str] = None
    inchi: Optional[str] = None
    description: Optional[str] = None

class EvidenceUpdate(BaseModel):
    source: Optional[str] = None
    confidence: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    evidence_type: Optional[EvidenceType] = None
    value: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

# Rectification schemas
class RectificationRequest(BaseModel):
    molecule_id: str
    confidence_threshold: Optional[float] = 0.7
    explanation_required: bool = True

class RectificationResult(BaseModel):
    molecule_id: str
    original_confidence: float
    rectified_confidence: float
    explanation: Optional[str] = None
    conflicts_detected: int
    conflicts_resolved: int

# Visualization schemas
class MoleculeVisualizationRequest(BaseModel):
    molecule_id: str
    visualization_type: str = "3d"
    options: Optional[Dict[str, Any]] = None

class NetworkVisualizationRequest(BaseModel):
    central_molecule_id: Optional[str] = None
    pathway_id: Optional[str] = None
    similarity_threshold: Optional[float] = 0.6
    max_nodes: Optional[int] = 50

class VisualizationResponse(BaseModel):
    visualization_id: str
    visualization_type: str
    data: Any
    metadata: Optional[Dict[str, Any]] = None

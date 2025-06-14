from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
import asyncio
import json
from datetime import datetime

from ..database import Database, get_db
from ..auth import get_current_active_user
from ..models.schemas import UserResponse
from ..services.molecule_network import MoleculeNetworkBuilder

router = APIRouter(prefix="/fuzzy-evidence", tags=["fuzzy-evidence"])

# Pydantic models for fuzzy evidence API

class FuzzyEvidenceRequest(BaseModel):
    molecule_id: str
    evidence_items: List[Dict[str, Any]]
    integration_config: Optional[Dict[str, Any]] = None
    enable_prediction: bool = True
    enable_network_learning: bool = True

class FuzzyMembershipFunction(BaseModel):
    function_type: str = Field(..., description="Type of membership function: triangular, trapezoidal, gaussian, sigmoid")
    parameters: Dict[str, float] = Field(..., description="Parameters for the membership function")

class FuzzyLinguisticTerm(BaseModel):
    name: str
    membership_function: FuzzyMembershipFunction
    description: Optional[str] = None

class FuzzyEvidenceItem(BaseModel):
    id: str
    source: str
    evidence_type: str
    raw_value: float
    confidence_memberships: Dict[str, float]
    agreement_memberships: Dict[str, float]
    contextual_factors: Dict[str, float]
    temporal_decay: float
    uncertainty_bounds: tuple[float, float]

class EvidencePrediction(BaseModel):
    node_id: str
    predicted_value: float
    confidence: float
    supporting_evidence: List[str]
    reasoning: str

class EnhancedConfidence(BaseModel):
    original_confidence: float
    fuzzy_confidence: float
    bayesian_posterior: float
    network_influence: float
    final_confidence: float
    uncertainty_bounds: tuple[float, float]

class FuzzyIntegrationResult(BaseModel):
    original_evidence_count: int
    integrated_evidence_count: int
    predictions: List[EvidencePrediction]
    enhanced_confidences: Dict[str, EnhancedConfidence]
    integration_errors: List[str]
    network_coherence_score: float

class NetworkStatistics(BaseModel):
    node_count: int
    edge_count: int
    avg_confidence: float
    conflict_count: int
    coherence_score: float

class ObjectiveFunction(BaseModel):
    name: str
    components: List[Dict[str, Any]]
    weights: Dict[str, float]

@router.post("/integrate", response_model=FuzzyIntegrationResult)
async def integrate_fuzzy_evidence(
    request: FuzzyEvidenceRequest,
    db: Database = Depends(get_db),
    current_user: UserResponse = Depends(get_current_active_user)
):
    """
    Integrate evidence using hybrid fuzzy-Bayesian approach.
    
    This endpoint demonstrates the core innovation of Hegel's evidence rectification:
    - Converts binary confidence scores to fuzzy membership degrees
    - Builds evidence networks with relationship modeling
    - Applies Bayesian inference with fuzzy logic integration
    - Generates predictions for missing evidence
    - Optimizes using granular objective functions
    """
    try:
        # Simulate fuzzy evidence integration (in practice, would call Rust core)
        fuzzy_evidences = []
        
        for evidence_item in request.evidence_items:
            # Convert to fuzzy evidence representation
            fuzzy_evidence = convert_to_fuzzy_evidence(evidence_item)
            fuzzy_evidences.append(fuzzy_evidence)
        
        # Build evidence network
        network_builder = FuzzyEvidenceNetworkBuilder()
        network = await network_builder.build_network(fuzzy_evidences)
        
        # Apply fuzzy-Bayesian inference
        integration_result = await apply_fuzzy_bayesian_inference(
            network, 
            request.integration_config or {}
        )
        
        # Generate predictions if enabled
        predictions = []
        if request.enable_prediction:
            predictions = await generate_evidence_predictions(
                network, 
                [e["id"] for e in request.evidence_items]
            )
        
        # Calculate enhanced confidences
        enhanced_confidences = calculate_enhanced_confidences(
            network, 
            request.evidence_items
        )
        
        # Store results in database
        await store_fuzzy_integration_result(
            db, 
            request.molecule_id, 
            integration_result,
            current_user.id
        )
        
        return FuzzyIntegrationResult(
            original_evidence_count=len(request.evidence_items),
            integrated_evidence_count=len(fuzzy_evidences),
            predictions=predictions,
            enhanced_confidences=enhanced_confidences,
            integration_errors=[],
            network_coherence_score=integration_result.get("coherence_score", 0.0)
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Fuzzy integration failed: {str(e)}")

@router.get("/network-stats/{molecule_id}", response_model=NetworkStatistics)
async def get_network_statistics(
    molecule_id: str,
    db: Database = Depends(get_db),
    current_user: UserResponse = Depends(get_current_active_user)
):
    """Get statistics about the fuzzy evidence network for a molecule."""
    try:
        # Query network statistics from database
        stats_query = """
        MATCH (m:Molecule {id: $molecule_id})-[:HAS_EVIDENCE]->(e:Evidence)
        OPTIONAL MATCH (e)-[r:RELATES_TO]-(other:Evidence)
        WITH m, count(e) as node_count, count(r) as edge_count, 
             avg(e.fuzzy_confidence) as avg_confidence,
             sum(case when r.relationship_type = 'contradicts' then 1 else 0 end) as conflict_count
        RETURN node_count, edge_count, avg_confidence, conflict_count
        """
        
        result = await db.run_query(stats_query, {"molecule_id": molecule_id})
        
        if not result:
            raise HTTPException(status_code=404, detail="Molecule not found")
        
        stats = result[0]
        
        # Calculate coherence score
        coherence_score = calculate_network_coherence(stats)
        
        return NetworkStatistics(
            node_count=stats.get("node_count", 0),
            edge_count=stats.get("edge_count", 0),
            avg_confidence=stats.get("avg_confidence", 0.0),
            conflict_count=stats.get("conflict_count", 0),
            coherence_score=coherence_score
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get network statistics: {str(e)}")

@router.post("/predict-evidence/{molecule_id}", response_model=List[EvidencePrediction])
async def predict_missing_evidence(
    molecule_id: str,
    partial_evidence_ids: List[str],
    prediction_threshold: float = 0.7,
    db: Database = Depends(get_db),
    current_user: UserResponse = Depends(get_current_active_user)
):
    """
    Predict missing evidence using the fuzzy-Bayesian network.
    
    This demonstrates the network's ability to:
    - Expose parts of the evidence network
    - Predict missing evidence based on network structure
    - Provide reasoning for predictions
    """
    try:
        # Get existing evidence network
        network_query = """
        MATCH (m:Molecule {id: $molecule_id})-[:HAS_EVIDENCE]->(e:Evidence)
        OPTIONAL MATCH (e)-[r:RELATES_TO]-(connected:Evidence)
        WHERE NOT e.id IN $partial_evidence_ids
        RETURN e, collect({node: connected, relationship: r}) as connections
        """
        
        results = await db.run_query(network_query, {
            "molecule_id": molecule_id,
            "partial_evidence_ids": partial_evidence_ids
        })
        
        predictions = []
        
        for result in results:
            evidence_node = result["e"]
            connections = result["connections"]
            
            # Calculate prediction based on connected evidence
            prediction = calculate_evidence_prediction(
                evidence_node, 
                connections, 
                prediction_threshold
            )
            
            if prediction and prediction.confidence >= prediction_threshold:
                predictions.append(prediction)
        
        # Sort by confidence
        predictions.sort(key=lambda p: p.confidence, reverse=True)
        
        return predictions
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Evidence prediction failed: {str(e)}")

@router.post("/optimize-objective/{molecule_id}")
async def optimize_objective_function(
    molecule_id: str,
    objective_function: ObjectiveFunction,
    db: Database = Depends(get_db),
    current_user: UserResponse = Depends(get_current_active_user)
):
    """
    Optimize evidence network using granular objective functions.
    
    This demonstrates the system's ability to:
    - Define custom objective functions for evidence optimization
    - Apply multi-criteria optimization to evidence networks
    - Provide recommendations for evidence improvement
    """
    try:
        # Get current evidence network
        network = await get_evidence_network(db, molecule_id)
        
        # Apply objective function optimization
        optimization_result = await apply_objective_optimization(
            network, 
            objective_function
        )
        
        # Store optimization results
        await store_optimization_result(
            db, 
            molecule_id, 
            optimization_result,
            current_user.id
        )
        
        return {
            "molecule_id": molecule_id,
            "objective_function": objective_function.name,
            "optimization_score": optimization_result.get("total_score", 0.0),
            "component_scores": optimization_result.get("component_scores", {}),
            "recommendations": optimization_result.get("recommendations", []),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Objective optimization failed: {str(e)}")

@router.get("/linguistic-variables")
async def get_linguistic_variables():
    """Get available fuzzy linguistic variables for evidence evaluation."""
    return {
        "evidence_confidence": {
            "name": "evidence_confidence",
            "universe": [0.0, 1.0],
            "terms": {
                "very_low": {
                    "type": "triangular",
                    "parameters": {"low": 0.0, "peak": 0.0, "high": 0.2}
                },
                "low": {
                    "type": "triangular", 
                    "parameters": {"low": 0.0, "peak": 0.2, "high": 0.4}
                },
                "medium": {
                    "type": "triangular",
                    "parameters": {"low": 0.2, "peak": 0.5, "high": 0.8}
                },
                "high": {
                    "type": "triangular",
                    "parameters": {"low": 0.6, "peak": 0.8, "high": 1.0}
                },
                "very_high": {
                    "type": "triangular",
                    "parameters": {"low": 0.8, "peak": 1.0, "high": 1.0}
                }
            }
        },
        "evidence_agreement": {
            "name": "evidence_agreement",
            "universe": [0.0, 1.0],
            "terms": {
                "conflicting": {
                    "type": "trapezoidal",
                    "parameters": {"low": 0.0, "low_peak": 0.0, "high_peak": 0.3, "high": 0.5}
                },
                "neutral": {
                    "type": "triangular",
                    "parameters": {"low": 0.3, "peak": 0.5, "high": 0.7}
                },
                "supporting": {
                    "type": "trapezoidal",
                    "parameters": {"low": 0.5, "low_peak": 0.7, "high_peak": 1.0, "high": 1.0}
                }
            }
        }
    }

# Helper functions

def convert_to_fuzzy_evidence(evidence_item: Dict[str, Any]) -> FuzzyEvidenceItem:
    """Convert traditional evidence to fuzzy evidence representation."""
    raw_value = evidence_item.get("confidence", 0.5)
    
    # Calculate fuzzy memberships for confidence levels
    confidence_memberships = calculate_confidence_memberships(raw_value)
    
    # Calculate temporal decay
    timestamp = evidence_item.get("timestamp", datetime.utcnow().isoformat())
    temporal_decay = calculate_temporal_decay(timestamp)
    
    # Calculate uncertainty bounds based on evidence type
    evidence_type = evidence_item.get("evidence_type", "unknown")
    uncertainty_bounds = calculate_uncertainty_bounds(raw_value, evidence_type)
    
    return FuzzyEvidenceItem(
        id=evidence_item["id"],
        source=evidence_item.get("source", "unknown"),
        evidence_type=evidence_type,
        raw_value=raw_value,
        confidence_memberships=confidence_memberships,
        agreement_memberships={},  # Will be calculated during integration
        contextual_factors={},
        temporal_decay=temporal_decay,
        uncertainty_bounds=uncertainty_bounds
    )

def calculate_confidence_memberships(value: float) -> Dict[str, float]:
    """Calculate fuzzy membership degrees for confidence levels."""
    memberships = {}
    
    # Triangular membership functions for confidence levels
    memberships["very_low"] = max(0, min(1, (0.2 - value) / 0.2)) if value <= 0.2 else 0
    memberships["low"] = max(0, min((value - 0.0) / 0.2, (0.4 - value) / 0.2)) if 0 <= value <= 0.4 else 0
    memberships["medium"] = max(0, min((value - 0.2) / 0.3, (0.8 - value) / 0.3)) if 0.2 <= value <= 0.8 else 0
    memberships["high"] = max(0, min((value - 0.6) / 0.2, (1.0 - value) / 0.2)) if 0.6 <= value <= 1.0 else 0
    memberships["very_high"] = max(0, (value - 0.8) / 0.2) if value >= 0.8 else 0
    
    return memberships

def calculate_temporal_decay(timestamp_str: str) -> float:
    """Calculate temporal decay factor for evidence."""
    try:
        timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        age_hours = (datetime.utcnow() - timestamp.replace(tzinfo=None)).total_seconds() / 3600
        return max(0.1, (-age_hours / (24.0 * 30.0)).__exp__())  # Decay over ~30 days
    except:
        return 1.0  # Default to no decay if timestamp parsing fails

def calculate_uncertainty_bounds(value: float, evidence_type: str) -> tuple[float, float]:
    """Calculate uncertainty bounds based on evidence type."""
    uncertainty_factors = {
        "mass_spec": 0.05,
        "genomics": 0.10,
        "literature": 0.15,
        "proteomics": 0.08,
        "metabolomics": 0.12
    }
    
    factor = uncertainty_factors.get(evidence_type, 0.10)
    return (max(0.0, value * (1 - factor)), min(1.0, value * (1 + factor)))

class FuzzyEvidenceNetworkBuilder:
    """Builder for fuzzy evidence networks."""
    
    async def build_network(self, fuzzy_evidences: List[FuzzyEvidenceItem]) -> Dict[str, Any]:
        """Build a fuzzy evidence network from evidence items."""
        nodes = {}
        edges = []
        
        # Create nodes
        for evidence in fuzzy_evidences:
            nodes[evidence.id] = {
                "id": evidence.id,
                "evidence_type": evidence.evidence_type,
                "fuzzy_evidence": evidence,
                "prior_probability": 0.5,
                "posterior_probability": evidence.raw_value,
                "network_influence": 0.0
            }
        
        # Create edges based on evidence relationships
        evidence_list = list(fuzzy_evidences)
        for i in range(len(evidence_list)):
            for j in range(i + 1, len(evidence_list)):
                edge = self.determine_evidence_relationship(evidence_list[i], evidence_list[j])
                if edge:
                    edges.append(edge)
        
        return {
            "nodes": nodes,
            "edges": edges,
            "linguistic_variables": {},
            "objective_functions": {}
        }
    
    def determine_evidence_relationship(self, evidence_a: FuzzyEvidenceItem, evidence_b: FuzzyEvidenceItem) -> Optional[Dict[str, Any]]:
        """Determine relationship between two pieces of evidence."""
        confidence_diff = abs(evidence_a.raw_value - evidence_b.raw_value)
        
        if evidence_a.source == evidence_b.source:
            # Same source - likely corroborating or contradicting
            if confidence_diff < 0.2:
                return {
                    "from_node": evidence_a.id,
                    "to_node": evidence_b.id,
                    "relationship_type": "corroborates",
                    "strength": 0.8 - confidence_diff,
                    "fuzzy_strength": {"strong": 1.0 - confidence_diff}
                }
            else:
                return {
                    "from_node": evidence_a.id,
                    "to_node": evidence_b.id,
                    "relationship_type": "contradicts",
                    "strength": confidence_diff,
                    "fuzzy_strength": {"weak": confidence_diff}
                }
        else:
            # Different sources - analyze for support
            confidence_similarity = 1.0 - confidence_diff
            if confidence_similarity > 0.5:
                return {
                    "from_node": evidence_a.id,
                    "to_node": evidence_b.id,
                    "relationship_type": "supports",
                    "strength": confidence_similarity,
                    "fuzzy_strength": {"moderate": confidence_similarity}
                }
        
        return None

async def apply_fuzzy_bayesian_inference(network: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
    """Apply fuzzy-Bayesian inference to the evidence network."""
    # Simulate fuzzy-Bayesian inference
    nodes = network["nodes"]
    edges = network["edges"]
    
    # Update posterior probabilities using Bayesian inference
    for node_id, node in nodes.items():
        fuzzy_evidence = node["fuzzy_evidence"]
        likelihood = fuzzy_evidence.raw_value
        prior = node["prior_probability"]
        
        # Simplified Bayesian update
        posterior = (likelihood * prior) / (likelihood * prior + (1.0 - likelihood) * (1.0 - prior))
        node["posterior_probability"] = posterior
    
    # Calculate network influence
    for edge in edges:
        from_node = nodes[edge["from_node"]]
        to_node = nodes[edge["to_node"]]
        
        influence = from_node["posterior_probability"] * edge["strength"]
        to_node["network_influence"] += influence
    
    # Calculate coherence score
    coherence_score = calculate_network_coherence_from_network(network)
    
    return {
        "updated_network": network,
        "coherence_score": coherence_score,
        "inference_steps": len(edges)
    }

async def generate_evidence_predictions(network: Dict[str, Any], existing_evidence_ids: List[str]) -> List[EvidencePrediction]:
    """Generate predictions for missing evidence."""
    predictions = []
    nodes = network["nodes"]
    edges = network["edges"]
    
    # Find nodes not in existing evidence
    missing_nodes = [node_id for node_id in nodes.keys() if node_id not in existing_evidence_ids]
    
    for missing_node_id in missing_nodes:
        # Find connected evidence
        connected_evidence = []
        for edge in edges:
            if edge["to_node"] == missing_node_id:
                connected_evidence.append(nodes[edge["from_node"]])
            elif edge["from_node"] == missing_node_id:
                connected_evidence.append(nodes[edge["to_node"]])
        
        if connected_evidence:
            # Calculate prediction
            avg_confidence = sum(node["posterior_probability"] for node in connected_evidence) / len(connected_evidence)
            
            prediction = EvidencePrediction(
                node_id=missing_node_id,
                predicted_value=avg_confidence,
                confidence=min(0.9, avg_confidence * 0.8),  # Reduce confidence for predictions
                supporting_evidence=[node["id"] for node in connected_evidence],
                reasoning=f"Predicted based on {len(connected_evidence)} connected evidence nodes"
            )
            
            predictions.append(prediction)
    
    return predictions

def calculate_enhanced_confidences(network: Dict[str, Any], evidence_items: List[Dict[str, Any]]) -> Dict[str, EnhancedConfidence]:
    """Calculate enhanced confidence scores using the fuzzy network."""
    enhanced_confidences = {}
    nodes = network["nodes"]
    
    for evidence_item in evidence_items:
        evidence_id = evidence_item["id"]
        if evidence_id in nodes:
            node = nodes[evidence_id]
            fuzzy_evidence = node["fuzzy_evidence"]
            
            enhanced = EnhancedConfidence(
                original_confidence=evidence_item.get("confidence", 0.5),
                fuzzy_confidence=fuzzy_evidence.raw_value,  # In practice, would defuzzify
                bayesian_posterior=node["posterior_probability"],
                network_influence=node["network_influence"],
                final_confidence=calculate_final_confidence_score(node),
                uncertainty_bounds=fuzzy_evidence.uncertainty_bounds
            )
            
            enhanced_confidences[evidence_id] = enhanced
    
    return enhanced_confidences

def calculate_final_confidence_score(node: Dict[str, Any]) -> float:
    """Calculate final confidence score combining all factors."""
    fuzzy_weight = 0.4
    bayesian_weight = 0.4
    network_weight = 0.2
    
    fuzzy_confidence = node["fuzzy_evidence"].raw_value
    bayesian_posterior = node["posterior_probability"]
    network_influence = abs(node["network_influence"])
    
    final_confidence = (fuzzy_confidence * fuzzy_weight + 
                       bayesian_posterior * bayesian_weight + 
                       network_influence * network_weight)
    
    return max(0.0, min(1.0, final_confidence))

def calculate_network_coherence(stats: Dict[str, Any]) -> float:
    """Calculate network coherence score from statistics."""
    node_count = stats.get("node_count", 0)
    edge_count = stats.get("edge_count", 0)
    avg_confidence = stats.get("avg_confidence", 0.0)
    conflict_count = stats.get("conflict_count", 0)
    
    if node_count == 0:
        return 0.0
    
    # Calculate connectivity
    max_edges = node_count * (node_count - 1) / 2
    connectivity = edge_count / max_edges if max_edges > 0 else 0
    
    # Calculate conflict ratio
    conflict_ratio = conflict_count / edge_count if edge_count > 0 else 0
    
    # Combine factors
    coherence = (avg_confidence * 0.5 + connectivity * 0.3 + (1 - conflict_ratio) * 0.2)
    
    return max(0.0, min(1.0, coherence))

def calculate_network_coherence_from_network(network: Dict[str, Any]) -> float:
    """Calculate coherence score from network structure."""
    nodes = network["nodes"]
    edges = network["edges"]
    
    if not nodes:
        return 0.0
    
    # Calculate average confidence
    avg_confidence = sum(node["posterior_probability"] for node in nodes.values()) / len(nodes)
    
    # Calculate relationship consistency
    consistency_sum = 0.0
    for edge in edges:
        from_node = nodes[edge["from_node"]]
        to_node = nodes[edge["to_node"]]
        
        if edge["relationship_type"] in ["supports", "corroborates"]:
            consistency = 1.0 - abs(from_node["posterior_probability"] - to_node["posterior_probability"])
        elif edge["relationship_type"] == "contradicts":
            consistency = abs(from_node["posterior_probability"] - to_node["posterior_probability"])
        else:
            consistency = 0.5
        
        consistency_sum += consistency * edge["strength"]
    
    avg_consistency = consistency_sum / len(edges) if edges else 0.5
    
    return (avg_confidence * 0.6 + avg_consistency * 0.4)

def calculate_evidence_prediction(evidence_node: Dict[str, Any], connections: List[Dict[str, Any]], threshold: float) -> Optional[EvidencePrediction]:
    """Calculate evidence prediction based on connected nodes."""
    if not connections:
        return None
    
    # Calculate weighted average of connected evidence
    total_weight = 0.0
    weighted_sum = 0.0
    
    for connection in connections:
        connected_node = connection.get("node")
        relationship = connection.get("relationship")
        
        if connected_node and relationship:
            weight = relationship.get("strength", 0.5)
            confidence = connected_node.get("fuzzy_confidence", 0.5)
            
            weighted_sum += confidence * weight
            total_weight += weight
    
    if total_weight == 0:
        return None
    
    predicted_value = weighted_sum / total_weight
    prediction_confidence = min(0.9, predicted_value * 0.8)  # Reduce confidence for predictions
    
    if prediction_confidence < threshold:
        return None
    
    return EvidencePrediction(
        node_id=evidence_node["id"],
        predicted_value=predicted_value,
        confidence=prediction_confidence,
        supporting_evidence=[conn["node"]["id"] for conn in connections if conn.get("node")],
        reasoning=f"Predicted from {len(connections)} connected evidence nodes"
    )

async def get_evidence_network(db: Database, molecule_id: str) -> Dict[str, Any]:
    """Get evidence network for a molecule from database."""
    # This would query the actual network from Neo4j
    # For now, return a mock network
    return {
        "nodes": {},
        "edges": [],
        "molecule_id": molecule_id
    }

async def apply_objective_optimization(network: Dict[str, Any], objective_function: ObjectiveFunction) -> Dict[str, Any]:
    """Apply objective function optimization to the network."""
    # Simulate objective function optimization
    component_scores = {}
    
    for component in objective_function.components:
        component_name = component.get("name", "unknown")
        # Calculate component score based on network
        score = calculate_objective_component_score(network, component)
        component_scores[component_name] = score
    
    # Calculate total score
    total_score = 0.0
    for component_name, score in component_scores.items():
        weight = objective_function.weights.get(component_name, 1.0)
        total_score += score * weight
    
    # Generate recommendations
    recommendations = generate_optimization_recommendations(component_scores)
    
    return {
        "total_score": total_score,
        "component_scores": component_scores,
        "recommendations": recommendations
    }

def calculate_objective_component_score(network: Dict[str, Any], component: Dict[str, Any]) -> float:
    """Calculate score for an objective function component."""
    component_type = component.get("function_type", "maximize_confidence")
    nodes = network.get("nodes", {})
    
    if component_type == "maximize_confidence":
        if not nodes:
            return 0.0
        avg_confidence = sum(node["posterior_probability"] for node in nodes.values()) / len(nodes)
        return avg_confidence
    elif component_type == "minimize_uncertainty":
        # Calculate average uncertainty
        if not nodes:
            return 1.0
        uncertainties = []
        for node in nodes.values():
            fuzzy_evidence = node["fuzzy_evidence"]
            low, high = fuzzy_evidence.uncertainty_bounds
            uncertainties.append(high - low)
        avg_uncertainty = sum(uncertainties) / len(uncertainties)
        return 1.0 - avg_uncertainty  # Convert to maximization
    else:
        return 0.5  # Default score

def generate_optimization_recommendations(component_scores: Dict[str, float]) -> List[str]:
    """Generate optimization recommendations based on component scores."""
    recommendations = []
    
    for component_name, score in component_scores.items():
        if score < 0.5:
            recommendations.append(f"Improve {component_name} score from {score:.2f}")
    
    return recommendations

async def store_fuzzy_integration_result(db: Database, molecule_id: str, result: Dict[str, Any], user_id: str):
    """Store fuzzy integration result in database."""
    # This would store the result in Neo4j
    # For now, just log it
    pass

async def store_optimization_result(db: Database, molecule_id: str, result: Dict[str, Any], user_id: str):
    """Store optimization result in database."""
    # This would store the result in Neo4j
    # For now, just log it
    pass 
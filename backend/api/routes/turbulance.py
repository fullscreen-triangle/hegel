"""
Turbulance Script Compilation and Execution API
"""

from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import asyncio
import subprocess
import tempfile
import json
import os
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/turbulance", tags=["turbulance"])

class TurbulanceScript(BaseModel):
    """Turbulance script content"""
    name: str
    description: str
    script_content: str  # .trb file content
    fullscreen_content: Optional[str] = None  # .fs file content
    gerhard_content: Optional[str] = None     # .ghd file content
    harare_content: Optional[str] = None      # .hre file content

class TurbulanceCompilationRequest(BaseModel):
    """Request for compiling Turbulance script"""
    script: TurbulanceScript
    config: Dict[str, Any] = {
        "enable_semantic_validation": True,
        "enable_consciousness_tracking": True,
        "enable_decision_logging": True,
        "semantic_confidence_threshold": 0.85,
        "max_execution_time_seconds": 3600
    }

class TurbulanceExecutionRequest(BaseModel):
    """Request for executing compiled Turbulance script"""
    compiled_script_id: str
    execution_parameters: Dict[str, Any] = {}

class SemanticOperation(BaseModel):
    """Semantic operation in compiled script"""
    id: str
    operation_type: str
    inputs: List[str]
    outputs: List[str]
    semantic_context: Dict[str, str]
    confidence_threshold: float
    validation_method: str

class CompiledScript(BaseModel):
    """Compiled Turbulance script"""
    id: str
    metadata: Dict[str, Any]
    hypothesis: Dict[str, Any]
    operations: List[SemanticOperation]
    dependencies: Dict[str, Any]
    validation_criteria: Dict[str, Any]

class ExecutionResult(BaseModel):
    """Result of Turbulance script execution"""
    execution_id: str
    success: bool
    semantic_understanding: Dict[str, Any]
    scientific_insights: List[Dict[str, Any]]
    validation_results: Dict[str, Any]
    decision_trail: List[Dict[str, Any]]
    consciousness_evolution: List[Dict[str, Any]]
    execution_time_seconds: float
    error_message: Optional[str] = None

@router.post("/compile", response_model=CompiledScript)
async def compile_turbulance_script(request: TurbulanceCompilationRequest):
    """
    Compile Turbulance script into executable semantic operations.
    
    This endpoint:
    1. Parses the Turbulance script syntax
    2. Compiles semantic operations for Hegel's evidence network
    3. Validates semantic hypothesis framework
    4. Returns compiled script ready for execution
    """
    try:
        logger.info(f"Compiling Turbulance script: {request.script.name}")
        
        # Create temporary directory for four-file project
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Write the four files
            script_files = await write_project_files(temp_path, request.script)
            
            # Call Rust core for compilation
            compilation_result = await compile_with_rust_core(temp_path, request.config)
            
            if not compilation_result["success"]:
                raise HTTPException(
                    status_code=400,
                    detail=f"Compilation failed: {compilation_result['error']}"
                )
            
            # Extract compiled operations
            compiled_script = CompiledScript(
                id=compilation_result["script_id"],
                metadata=compilation_result["metadata"],
                hypothesis=compilation_result["hypothesis"],
                operations=[
                    SemanticOperation(**op) for op in compilation_result["operations"]
                ],
                dependencies=compilation_result["dependencies"],
                validation_criteria=compilation_result["validation_criteria"]
            )
            
            logger.info(f"Successfully compiled script with {len(compiled_script.operations)} semantic operations")
            return compiled_script
            
    except Exception as e:
        logger.error(f"Turbulance compilation error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/execute", response_model=ExecutionResult)
async def execute_turbulance_script(request: TurbulanceExecutionRequest):
    """
    Execute compiled Turbulance script with Hegel's evidence network.
    
    This endpoint:
    1. Loads the compiled semantic operations
    2. Initializes Hegel's fuzzy-Bayesian evidence network
    3. Executes semantic operations with genuine understanding
    4. Returns semantic insights and validation results
    """
    try:
        logger.info(f"Executing Turbulance script: {request.compiled_script_id}")
        
        # Execute with Rust core
        execution_result = await execute_with_rust_core(
            request.compiled_script_id,
            request.execution_parameters
        )
        
        if not execution_result["success"]:
            return ExecutionResult(
                execution_id=execution_result["execution_id"],
                success=False,
                semantic_understanding={},
                scientific_insights=[],
                validation_results={},
                decision_trail=[],
                consciousness_evolution=[],
                execution_time_seconds=execution_result.get("execution_time", 0.0),
                error_message=execution_result["error"]
            )
        
        # Convert execution result
        result = ExecutionResult(
            execution_id=execution_result["execution_id"],
            success=True,
            semantic_understanding=execution_result["semantic_understanding"],
            scientific_insights=execution_result["scientific_insights"],
            validation_results=execution_result["validation_results"],
            decision_trail=execution_result["decision_trail"],
            consciousness_evolution=execution_result["consciousness_evolution"],
            execution_time_seconds=execution_result["execution_time"]
        )
        
        logger.info(f"Execution completed successfully with {len(result.scientific_insights)} insights generated")
        return result
        
    except Exception as e:
        logger.error(f"Turbulance execution error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/compile-and-execute", response_model=ExecutionResult)
async def compile_and_execute_turbulance(
    script: TurbulanceScript,
    config: Dict[str, Any] = {
        "enable_semantic_validation": True,
        "enable_consciousness_tracking": True,
        "semantic_confidence_threshold": 0.85
    }
):
    """
    Compile and execute Turbulance script in one operation.
    
    This is a convenience endpoint that combines compilation and execution
    for rapid prototyping of semantic scientific workflows.
    """
    try:
        logger.info(f"Compile and execute Turbulance script: {script.name}")
        
        # Compile first
        compile_request = TurbulanceCompilationRequest(script=script, config=config)
        compiled_script = await compile_turbulance_script(compile_request)
        
        # Then execute
        execute_request = TurbulanceExecutionRequest(
            compiled_script_id=compiled_script.id,
            execution_parameters={}
        )
        execution_result = await execute_turbulance_script(execute_request)
        
        return execution_result
        
    except Exception as e:
        logger.error(f"Compile and execute error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/upload-project")
async def upload_turbulance_project(
    trb_file: UploadFile = File(..., description="Turbulance script (.trb)"),
    fs_file: Optional[UploadFile] = File(None, description="Fullscreen visualization (.fs)"),
    ghd_file: Optional[UploadFile] = File(None, description="Gerhard dependencies (.ghd)"),
    hre_file: Optional[UploadFile] = File(None, description="Harare decisions (.hre)"),
    config: str = Form('{"enable_semantic_validation": true}')
):
    """
    Upload complete four-file Turbulance project and execute.
    
    This endpoint accepts the complete Turbulance project structure:
    - .trb: Main semantic orchestration script
    - .fs: Real-time consciousness visualization
    - .ghd: Resource dependencies
    - .hre: Decision logging and metacognitive tracking
    """
    try:
        # Read uploaded files
        script_content = await trb_file.read()
        fs_content = await fs_file.read() if fs_file else None
        ghd_content = await ghd_file.read() if ghd_file else None
        hre_content = await hre_file.read() if hre_file else None
        
        # Parse config
        config_dict = json.loads(config)
        
        # Create script object
        script = TurbulanceScript(
            name=trb_file.filename.replace('.trb', ''),
            description=f"Uploaded project: {trb_file.filename}",
            script_content=script_content.decode('utf-8'),
            fullscreen_content=fs_content.decode('utf-8') if fs_content else None,
            gerhard_content=ghd_content.decode('utf-8') if ghd_content else None,
            harare_content=hre_content.decode('utf-8') if hre_content else None
        )
        
        # Compile and execute
        result = await compile_and_execute_turbulance(script, config_dict)
        
        return {
            "message": "Project uploaded and executed successfully",
            "execution_result": result
        }
        
    except Exception as e:
        logger.error(f"Project upload error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/example-script")
async def get_example_turbulance_script():
    """
    Get an example Turbulance script demonstrating semantic scientific processing.
    
    This example shows how to express a complete scientific experiment
    using Turbulance syntax with semantic understanding.
    """
    example_script = """// Example Turbulance Script: Diabetes Biomarker Discovery
// Demonstrates semantic scientific processing with Hegel's evidence network

import semantic.zangalewa_runtime
import metacognitive.v8_intelligence  
import semantic.proposition_validation

// SEMANTIC HYPOTHESIS - Framework for understanding
hypothesis DiabetesBiomarkerDiscovery:
    claim: "Metabolomic patterns contain SEMANTIC MEANING for diabetes prediction"
    semantic_validation:
        - biological_understanding: "pathway dysregulation semantics"
        - temporal_understanding: "6-month prediction window meaning"
        - clinical_understanding: "actionable intervention semantics"
    requires: "authentic_semantic_comprehension"

// MAIN SEMANTIC ORCHESTRATION
funxn semantic_diabetes_discovery():
    print("🧠 INITIALIZING SEMANTIC PROCESSING NETWORK")
    
    // Initialize consciousness with V8 intelligence modules
    item semantic_runtime = zangalewa.initialize_consciousness([
        mzekezeke.semantic_evidence_integration,
        zengeza.semantic_signal_understanding,
        diggiden.semantic_robustness_testing,
        champagne.semantic_dream_processing,
        spectacular.semantic_paradigm_detection,
        nicotine.semantic_context_preservation,
        pungwe.semantic_authenticity_validation
    ])
    
    // Phase 1: SEMANTIC DATA UNDERSTANDING
    print("🔍 Understanding data as meaningful content...")
    item raw_spectra = load_dataset("diabetes_metabolomics/")
    
    // Zengeza: Understand noise as semantic interference
    item semantic_data = semantic_runtime.zengeza.understand_interference_semantics(
        raw_data: raw_spectra,
        semantic_context: "metabolomic_biological_meaning",
        interference_understanding: "instrument_behavior_semantics"
    )
    
    // Phase 2: SEMANTIC EVIDENCE INTEGRATION
    print("🧠 Integrating semantic evidence...")
    item integrated_semantics = semantic_runtime.mzekezeke.integrate_semantic_evidence(
        experimental_understanding: semantic_data,
        prior_knowledge_semantics: gerhard.query_semantic_literature("diabetes_metabolomics"),
        temporal_semantic_validation: "meaning_consistency_over_time"
    )
    
    // Phase 3: DREAM-STATE SEMANTIC PROCESSING
    print("🎨 Generating novel semantic insights...")
    item dream_insights = semantic_runtime.champagne.dream_semantic_breakthroughs(
        current_understanding: integrated_semantics,
        dream_exploration: "deep_biological_meaning_networks",
        creativity_threshold: 0.8,
        scientific_validity: "maintain_biological_plausibility"
    )
    
    // Phase 4: AUTHENTICITY VALIDATION
    print("🔍 Validating authentic understanding...")
    item authentic_understanding = semantic_runtime.pungwe.validate_authentic_understanding(
        semantic_understanding: dream_insights,
        self_deception_detection: "semantic_wishful_thinking_check",
        truth_synthesis: "genuine_scientific_insight_validation"
    )
    
    return finalize_semantic_understanding(authentic_understanding)

// SCIENTIFIC PROPOSITION VALIDATION
funxn finalize_semantic_understanding(understanding):
    print("🧠 === SEMANTIC SCIENTIFIC REASONING ===")
    
    proposition SemanticValidation:
        motion SemanticSensitivity("Semantic understanding achieves predictive sensitivity")
        motion SemanticSpecificity("Semantic understanding achieves predictive specificity")
        motion SemanticBiologicalMeaning("Understanding has genuine biological meaning")
        motion SemanticAuthenticity("Understanding is authentic, not self-deceptive")
        
        within understanding.experimental_validation:
            given semantic_sensitivity >= 0.85 and semantic_specificity >= 0.80:
                support SemanticSensitivity with_confidence(understanding.validation_confidence)
                support SemanticSpecificity with_confidence(understanding.validation_confidence)
        
        within understanding.authenticity_validation:
            given authenticity_score > 0.9 and !self_deception_detected:
                support SemanticAuthenticity with_confidence(understanding.authenticity_score)
                print("🔍 AUTHENTIC UNDERSTANDING: Validated as genuine scientific insight")
    
    item final_evaluation = evaluate_semantic_hypothesis(
        proposition: SemanticValidation,
        understanding_context: understanding
    )
    
    return {
        "semantic_understanding_achieved": final_evaluation.understanding_validated,
        "scientific_breakthrough": final_evaluation.breakthrough_detected,
        "authentic_insights": final_evaluation.novel_insights
    }

// MAIN EXECUTION
funxn main():
    print("🚀 HEGEL TURBULANCE SEMANTIC PROCESSING")
    print("🧠 Expressing complete scientific method in executable code")
    
    item results = semantic_diabetes_discovery()
    
    print("🎯 === SEMANTIC UNDERSTANDING ACHIEVED ===")
    print("Understanding Quality: {:.1f}%", results.semantic_understanding_achieved * 100)
    print("Scientific Breakthrough: {}", results.scientific_breakthrough ? "YES ✅" : "NO ❌")
    
    if results.scientific_breakthrough:
        print("🎉 SEMANTIC SUCCESS: Genuine scientific understanding achieved!")
        print("💡 Novel biological insights discovered through semantic processing")
    
    return results
"""
    
    return {
        "script_name": "diabetes_biomarker_discovery",
        "description": "Example Turbulance script demonstrating semantic scientific processing",
        "script_content": example_script,
        "features": [
            "Semantic hypothesis framework",
            "V8 intelligence module orchestration", 
            "Dream-state insight generation",
            "Authenticity validation",
            "Scientific proposition validation",
            "Metacognitive decision tracking"
        ]
    }

# Helper functions

async def write_project_files(temp_path: Path, script: TurbulanceScript) -> Dict[str, str]:
    """Write Turbulance project files to temporary directory"""
    files = {}
    
    # Write main .trb file
    trb_file = temp_path / f"{script.name}.trb"
    trb_file.write_text(script.script_content)
    files["trb"] = str(trb_file)
    
    # Write optional files
    if script.fullscreen_content:
        fs_file = temp_path / f"{script.name}.fs"
        fs_file.write_text(script.fullscreen_content)
        files["fs"] = str(fs_file)
    
    if script.gerhard_content:
        ghd_file = temp_path / f"{script.name}.ghd"
        ghd_file.write_text(script.gerhard_content)
        files["ghd"] = str(ghd_file)
    
    if script.harare_content:
        hre_file = temp_path / f"{script.name}.hre"
        hre_file.write_text(script.harare_content)
        files["hre"] = str(hre_file)
    
    return files

async def compile_with_rust_core(project_path: Path, config: Dict[str, Any]) -> Dict[str, Any]:
    """Call Rust core for Turbulance compilation"""
    try:
        # Call the Rust binary for compilation
        cmd = [
            "cargo", "run", "--bin", "hegel",
            "compile-turbulance",
            "--project-path", str(project_path),
            "--config", json.dumps(config)
        ]
        
        # Change to core directory
        cwd = Path(__file__).parent.parent.parent / "core"
        
        process = await asyncio.create_subprocess_exec(
            *cmd,
            cwd=cwd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await process.communicate()
        
        if process.returncode != 0:
            return {
                "success": False,
                "error": stderr.decode() if stderr else "Unknown compilation error"
            }
        
        # Parse JSON result from Rust
        result = json.loads(stdout.decode())
        return result
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to call Rust compiler: {str(e)}"
        }

async def execute_with_rust_core(script_id: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
    """Call Rust core for Turbulance execution"""
    try:
        # Call the Rust binary for execution
        cmd = [
            "cargo", "run", "--bin", "hegel",
            "execute-turbulance", 
            "--script-id", script_id,
            "--parameters", json.dumps(parameters)
        ]
        
        # Change to core directory  
        cwd = Path(__file__).parent.parent.parent / "core"
        
        process = await asyncio.create_subprocess_exec(
            *cmd,
            cwd=cwd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await process.communicate()
        
        if process.returncode != 0:
            return {
                "success": False,
                "execution_id": f"exec_{script_id}",
                "error": stderr.decode() if stderr else "Unknown execution error"
            }
        
        # Parse JSON result from Rust
        result = json.loads(stdout.decode())
        return result
        
    except Exception as e:
        return {
            "success": False,
            "execution_id": f"exec_{script_id}",
            "error": f"Failed to call Rust executor: {str(e)}"
        } 
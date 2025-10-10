# Wilhelm Hegel Framework

Biological Computer Architecture for Molecular Evidence Networks

## Overview

The Wilhelm Hegel Framework implements a comprehensive biological analysis system based on novel theoretical foundations including:

- **Hierarchical Observer System**: Finite observers at each frequency scale with transcendent observer for gear-based navigation
- **S-Entropy Coordinate Transformation**: Complete molecular language mapping system
- **Oscillatory Bayesian Networks**: Multi-scale probabilistic inference
- **Biological Circuit Analysis**: Oscillatory hole semiconductor theory applied to biological systems
- **Fuzzy Evidence Processing**: Tri-dimensional windowing for molecular evidence
- **Pathway Optimization**: Multi-objective optimization with viability constraints
- **Cross-modal Validation**: Consistency verification across representation modes

## Quick Start

```bash
# Install the framework
pip install -e .

# NEW: Run analysis with online models (no local file needed!)
python analysis_pipeline.py --model-source example --model-id example_glycolysis

# Traditional: Run analysis on local SBML file
python analysis_pipeline.py your_model.xml --output results/

# NEW: List available online models
python analysis_pipeline.py --list-models

# NEW: Run with LLM comparison (requires Hugging Face API key)
python analysis_pipeline.py --model-source biomodels --hf-api-key YOUR_KEY
```

## NEW FEATURES 🚀

### 🧬 **Personal Pharmacology Theory Validation** ⭐ **BREAKTHROUGH**

- **Real Clinical Data**: Use YOUR lithium blood levels + genome sequencing
- **Theory Testing**: Validate oscillatory hole semiconductor theory with actual measurements
- **Genomic Integration**: Personal variants in lithium-response genes (GSK3B, CREB1, etc.)
- **BMD Validation**: Test Biological Maxwell Demon acceleration predictions
- **Statistical Comparison**: Your theory vs classical pharmacokinetics (R², MAE, RMSE)
- **Proof-of-Concept**: Potential breakthrough validation study for publication

```bash
# Validate your theory with your personal clinical data:
python validate_my_pharmacology_theory.py
```

### Online Database Integration

- **BiGG Models**: Genome-scale metabolic models
- **BioModels**: Curated computational models
- **Reactome**: Pathway database
- **Automatic Download**: No local files needed
- **Intelligent Caching**: Downloaded models cached for reuse

### LLM Conversion & Comparison

- **Network-to-Text**: Converts biological networks to natural language
- **Q&A Generation**: Creates training datasets from analysis results
- **Model Comparison**: Benchmarks against molecular LLMs:
  - ChemBERTa (chemical language)
  - BioBERT (biomedical text)
  - SciBERT (scientific literature)
  - PubMedBERT (biomedical abstracts)
- **Performance Metrics**: Semantic similarity, perplexity, benchmarks
- **Hugging Face Integration**: Direct API access to molecular models

## Architecture

### Core Components

1. **SBML Parser** (`src/processing/parse_sbml.py`)

   - Extracts species, reactions, parameters, compartments, and rules

2. **Network Analysis** (`src/biological_networks/`)

   - Molecular network construction
   - Pathway topology extraction
   - Regulatory network identification

3. **Coordinate Transformation** (`src/transform/`)

   - S-entropy molecular language system
   - Fuzzy evidence windowing
   - Biological circuit mapping

4. **Optimization** (`src/optimisation/`)

   - Hierarchical observer system
   - Oscillatory Bayesian networks
   - Pathway optimization algorithms

5. **Validation & Reporting** (`src/processing/`)

   - Cross-modal consistency validation
   - Comprehensive visualization suite

6. **Online Data Sources** (`src/data_sources/`) **NEW**

   - BiGG Models, BioModels, Reactome integration
   - Automatic SBML download and caching

7. **LLM Integration** (`src/biological_networks/network_model.py`) **NEW**
   - Network-to-LLM conversion
   - Hugging Face model comparison
   - Molecular language model benchmarking

### Theoretical Foundations

The framework integrates several breakthrough theoretical concepts:

- **Oscillatory Mechanics**: Molecular interactions as oscillatory resonance
- **Biological Maxwell Demons**: Information processing in biological systems
- **Positive Hole Analogy**: Biological pathways as semiconductor circuits
- **S-Entropy Coordinates**: Mathematical framework for molecular representation
- **Hierarchical Observers**: Finite observers with transcendent navigation

## Usage Examples

### ⭐ **NEW: Personal Theory Validation** ⭐

#### Standard Validation

```bash
# Edit your personal data templates
cd wilhelm/
python validate_my_pharmacology_theory.py
```

Tests core theoretical components:

- **Oscillatory hole semiconductor theory**
- **BMD equivalence framework**
- **Gear ratio predictions**

#### 🚀 **Advanced Validation** (NEW!)

```bash
# Full theoretical framework with advanced components
python validate_my_pharmacology_theory.py --advanced

# Custom environmental conditions
python validate_my_pharmacology_theory.py --advanced --temp 308 --oxygen 0.18
```

Advanced components tested:

- **🔬 Fuzzy Evidence Processing**: Genomic variants → fuzzy membership functions
- **🧠 Bayesian Molecular Networks**: Spectral + structural + pathway evidence integration
- **💨 Oxygen-Enhanced Information Processing**: Paramagnetic oscillatory information theory
- **⚛️ Quantum Membrane Transport**: Lithium transport via quantum mechanics

#### Python API Example

```python
# The ultimate test - validate your theory with YOUR clinical data!
from wilhelm.src.validation.pharmacology_validation import create_personal_pharmacology_validation

# Your real lithium measurements
lithium_data = [
    {'date': '2023-01-15', 'level_meq_l': 0.8, 'dose_mg': 600, 'time_since_dose': 12},
    {'date': '2023-03-20', 'level_meq_l': 0.9, 'dose_mg': 600, 'time_since_dose': 11},
    # ... your actual measurements
]

# Your genome sequencing results
genomic_data = {
    'GSK3B': [{'variant': 'rs334558', 'genotype': 'CT'}],  # Your actual variants
    'CREB1': [{'variant': 'rs2253206', 'genotype': 'TT'}],
    # ... your actual genomic variants
}

# Standard validation
results = create_personal_pharmacology_validation(lithium_data, genomic_data)

# Advanced validation with full theoretical framework
advanced_results = create_personal_pharmacology_validation(
    lithium_data, genomic_data,
    use_advanced_components=True,
    environmental_conditions={'temperature': 310, 'oxygen_availability': 0.21}
)

print(f"Standard validation: {results['summary']['theory_validation']['validation_rate']:.1%}")
print(f"Advanced score: {advanced_results['advanced_validation']['combined_prediction']['prediction_score']:.3f}")
```

### Online Model Analysis

```python
from wilhelm.analysis_pipeline import run_complete_sbml_analysis

# No local file needed - download from online database
results = run_complete_sbml_analysis(
    model_source='biomodels',
    model_id='BIOMD0000000001',
    optimization_targets=['metabolic_efficiency', 'robustness'],
    huggingface_api_key='your_hf_key',  # Optional for LLM comparison
    output_dir="results/"
)
```

### Traditional Local File Analysis

```python
results = run_complete_sbml_analysis(
    sbml_file_path="model.xml",
    optimization_targets=['metabolic_efficiency', 'robustness'],
    output_dir="results/"
)
```

### Hierarchical Observer Navigation

```python
from wilhelm.src.optimisation.finite_observer import FiniteObserver
from wilhelm.src.optimisation.transcendent_observer import TranscendentObserver

# Create observers
molecular_observer = FiniteObserver((1e12, 1e15), 'molecular', 1e-12)
cellular_observer = FiniteObserver((1e-3, 1e3), 'cellular', 1e-3)

# Create transcendent navigator
navigator = TranscendentObserver([molecular_observer, cellular_observer])

# Navigate therapeutic pathways
pathway = navigator.navigate_therapeutic_pathway(
    sbml_components, 'systemic', 0.1
)
```

### S-Entropy Coordinate Mapping

```python
from wilhelm.src.transform.molecular_language import create_molecular_language_system

# Transform to S-entropy coordinates
molecular_language = create_molecular_language_system(sbml_components)
s_coordinates = molecular_language['s_coordinates']
```

### NEW: LLM Conversion and Comparison

```python
from wilhelm.src.biological_networks.network_model import create_network_llm_comparison

# Convert network analysis to LLM format and compare with molecular models
llm_analysis = create_network_llm_comparison(
    analysis_results,
    huggingface_api_key='your_hf_key'
)

# Access generated text descriptions
network_texts = llm_analysis['network_texts']
model_summary = llm_analysis['model_summary']
performance_score = llm_analysis['metadata']['overall_performance_score']
```

## Output

The framework generates comprehensive analysis results including:

- **Network Topology Visualizations**: Bayesian networks, pathway maps, circuit diagrams
- **S-Entropy Space Plots**: 3D coordinate visualizations with clustering
- **Optimization Results**: Pathway improvements with recommendations
- **Validation Reports**: Cross-modal consistency analysis
- **Interactive Dashboard**: Web-based exploration interface
- **LLM Analysis Reports**: Network-to-text conversion, model comparisons, performance metrics **NEW**
- **Training Datasets**: Question-answer pairs for molecular LLM fine-tuning **NEW**

## Requirements

- Python 3.8+
- NumPy, SciPy, NetworkX
- SBML support (python-libsbml)
- Visualization libraries (matplotlib, plotly)
- Machine learning tools (scikit-learn)
- **NEW**: PyTorch, Transformers, Sentence-Transformers (for LLM features)
- **NEW**: Requests (for online database access)

See `requirements.txt` for complete dependencies.

## Installation

```bash
# Clone repository
git clone https://github.com/kundai-farai/hegel.git
cd hegel/wilhelm

# Install in development mode
pip install -e .

# Or install from PyPI (when available)
pip install wilhelm-hegel-framework
```

## Contributing

The Wilhelm Hegel Framework is actively developed. Contributions welcome for:

- Additional biological data formats
- Enhanced visualization methods
- Alternative optimization algorithms
- Validation frameworks
- Documentation improvements

## Citation

When using this framework, please cite:

```bibtex
@software{wilhelm_hegel_framework,
  title={Wilhelm Hegel Framework: Biological Computer Architecture for Molecular Evidence Networks},
  author={Sachikonye, Kundai Farai},
  year={2024},
  url={https://github.com/kundai-farai/hegel}
}
```

## License

MIT License - see LICENSE file for details.

## Author

**Kundai Farai Sachikonye**  
sachikonye@wzw.tum.de

Technical University of Munich  
Chair of Computational Systems Biology

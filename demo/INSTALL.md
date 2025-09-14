# Installation Instructions

## Quick Setup for Python 3.13

The demo package has been simplified to work with Python 3.13 and avoid complex dependencies.

### 1. Install Required Packages

```bash
cd demo
pip install -r requirements.txt
```

### 2. Install Demo Package

```bash
pip install -e .
```

### 3. Run Demonstrations

**Option A: Complete validation suite**

```bash
python run_all_demos.py
```

**Option B: Quick validation only**

```bash
python run_all_demos.py --quick
```

**Option C: Individual demonstrations**

```bash
python demos/01_oxygen_information_processing.py
```

**Option D: Using CLI**

```bash
hegel-demo run-all
hegel-demo oxygen
hegel-demo cascade
hegel-demo quantum
hegel-demo validate
hegel-demo summary
```

## Output Files

All results are saved as:

- **PNG files**: High-quality visualizations for papers/presentations
- **JSON files**: Comprehensive data for further analysis
- **GIF files**: Animations of dynamic processes
- **TXT files**: Detailed validation reports

### Generated Files:

- `oxygen_oid_supremacy.png` - Molecular OID comparison
- `cascade_speed_advantage.png` - Communication speed analysis
- `membrane_quantum_accuracy.png` - Resolution validation
- `oxygen_substrate_data.json` - Complete oxygen processing data
- `electron_cascade_data.json` - Cascade communication data
- `membrane_quantum_data.json` - Quantum computing data
- `hegel_validation_summary.png` - Integrated summary
- `hegel_validation_report.txt` - Comprehensive report

## Simplified Dependencies

The package now only requires:

- numpy, scipy, pandas (core scientific computing)
- matplotlib, seaborn (visualization)
- scikit-learn, networkx (basic ML and graphs)
- click (CLI interface)
- numba (performance)

No interactive dashboards, complex quantum simulators, or heavy 3D visualization libraries needed!

## Troubleshooting

If you still have installation issues:

1. **Use Python 3.10 or 3.11** instead of 3.13:

   ```bash
   conda create -n hegel python=3.10
   conda activate hegel
   ```

2. **Install minimal subset**:

   ```bash
   pip install numpy matplotlib seaborn pandas scikit-learn click
   ```

3. **Run simplified version**:
   ```bash
   python run_all_demos.py --quick
   ```

The demonstrations will still validate all revolutionary claims and generate comprehensive PNG/JSON outputs!

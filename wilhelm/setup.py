#!/usr/bin/env python3
"""
Wilhelm Hegel Framework Setup
Biological Computer Architecture for Molecular Evidence Networks
"""

from setuptools import setup, find_packages
import os

# Read the README file
def read_readme():
    """Read README.md for long description"""
    readme_path = os.path.join(os.path.dirname(__file__), 'README.md')
    if os.path.exists(readme_path):
        with open(readme_path, 'r', encoding='utf-8') as f:
            return f.read()
    return "Wilhelm Hegel Framework - Biological Computer Architecture for Molecular Evidence Networks"

# Read requirements
def read_requirements():
    """Read requirements.txt"""
    req_path = os.path.join(os.path.dirname(__file__), 'requirements.txt')
    requirements = []
    if os.path.exists(req_path):
        with open(req_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    requirements.append(line)
    return requirements

setup(
    name="wilhelm-hegel-framework",
    version="1.0.0",
    author="Kundai Farai Sachikonye",
    author_email="sachikonye@wzw.tum.de",
    description="Biological Computer Architecture for Molecular Evidence Networks",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    url="https://github.com/kundai-farai/hegel",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering :: Bio-Informatics",
        "Topic :: Scientific/Engineering :: Chemistry",
        "Topic :: Scientific/Engineering :: Physics",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
    install_requires=read_requirements(),
    extras_require={
        "dev": [
            "pytest>=6.0.0",
            "pytest-cov>=2.12.0",
            "black>=21.0.0",
            "flake8>=3.9.0",
            "mypy>=0.910",
        ],
        "docs": [
            "sphinx>=4.0.0",
            "sphinx-rtd-theme>=0.5.0",
            "myst-parser>=0.15.0",
        ],
        "jupyter": [
            "jupyter>=1.0.0",
            "ipywidgets>=7.6.0",
            "jupyterlab>=3.0.0",
        ],
        "visualization": [
            "plotly>=5.0.0",
            "pygraphviz>=1.7",
            "graphviz>=0.16",
        ]
    },
    entry_points={
        "console_scripts": [
            "wilhelm-analyze=analysis_pipeline:main",
        ],
    },
    include_package_data=True,
    package_data={
        "wilhelm": [
            "data/*.xml",
            "examples/*.ipynb",
            "docs/*.md",
        ]
    },
    project_urls={
        "Bug Reports": "https://github.com/kundai-farai/hegel/issues",
        "Source": "https://github.com/kundai-farai/hegel",
        "Documentation": "https://wilhelm-hegel-framework.readthedocs.io/",
    },
    keywords=[
        "bioinformatics",
        "systems biology",
        "SBML",
        "molecular networks",
        "Bayesian networks",
        "oscillatory mechanics",
        "S-entropy coordinates",
        "biological circuits",
        "semiconductor theory",
        "computational pharmacology",
        "fuzzy logic",
        "information theory",
        "biological maxwell demons",
        "hierarchical observers",
        "pathway optimization"
    ],
    zip_safe=False,
)

# Post-installation message
def post_install_message():
    """Display post-installation message"""
    print("\n" + "="*80)
    print("WILHELM HEGEL FRAMEWORK INSTALLATION COMPLETE")
    print("="*80)
    print()
    print("Biological Computer Architecture for Molecular Evidence Networks")
    print("Author: Kundai Farai Sachikonye")
    print()
    print("Key Features:")
    print("  • Hierarchical Observer System (Finite + Transcendent)")
    print("  • S-Entropy Coordinate Transformation")
    print("  • Oscillatory Bayesian Networks")
    print("  • Biological Circuit Analysis (Oscillatory Hole Semiconductor Theory)")
    print("  • Fuzzy Evidence Processing")
    print("  • Multi-scale Pathway Optimization")
    print("  • Cross-modal Validation Framework")
    print("  • Comprehensive Visualization and Reporting")
    print()
    print("Quick Start:")
    print("  python -m wilhelm.analysis_pipeline your_model.xml")
    print()
    print("For examples and documentation:")
    print("  https://wilhelm-hegel-framework.readthedocs.io/")
    print()
    print("="*80)

if __name__ == "__main__":
    post_install_message()

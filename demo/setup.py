#!/usr/bin/env python3
"""
Setup script for Hegel Biological Computer Architecture Demonstrations

This package provides Python demonstrations validating the theoretical claims
of oxygen-enhanced Bayesian molecular evidence networks.
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="hegel-bio-computer-demos",
    version="1.0.0",
    author="Kundai Farai Sachikonye",
    author_email="kundai.sachikonye@wzw.tum.de",
    description="Demonstrations validating oxygen-enhanced Bayesian molecular evidence networks",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/fullscreen-triangle/hegel",
    packages=find_packages(),
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
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=7.0",
            "pytest-cov>=4.0",
            "black>=23.0",
            "flake8>=6.0",
            "mypy>=1.0",
        ],
        "jupyter": [
            "jupyter>=1.0",
            "ipykernel>=6.0",
            "ipywidgets>=8.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "hegel-demo=hegel_demo.cli:main",
        ],
    },
    include_package_data=True,
    zip_safe=False,
)

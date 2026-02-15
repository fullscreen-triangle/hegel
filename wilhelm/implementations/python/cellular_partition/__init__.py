"""
Cellular Partition Computing Framework

Implements the derivation of cellular function from categorical partitioning.
The derivation IS the computation: observation = computing = process.

Based on: "Deriving the Complete Cell from Categorical Partitioning"
"""

from .s_entropy import SEntropyCoordinate, SEntropySpace
from .ternary import TritString, TernaryTree
from .primitives import project, complete, compose
from .constraints import Constraint, ChargeNeutrality, EnergyConservation, CategoricalCoherence
from .completion import BackwardCompletion
from .apertures import CategoricalAperture

__version__ = "0.1.0"
__all__ = [
    "SEntropyCoordinate",
    "SEntropySpace",
    "TritString",
    "TernaryTree",
    "project",
    "complete",
    "compose",
    "Constraint",
    "ChargeNeutrality",
    "EnergyConservation",
    "CategoricalCoherence",
    "BackwardCompletion",
    "CategoricalAperture",
]

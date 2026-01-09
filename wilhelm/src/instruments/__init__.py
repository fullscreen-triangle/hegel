"""
Virtual Categorical Spectrometry Suite

Instruments exist as categorical apertures only during measurement.
Between measurements, molecules occupy partition states without instrumentation.
"""

from .virtual_spectrometer import VirtualCategoricalSpectrometer
from .validation_suite import ValidationSuite

__all__ = [
    'VirtualCategoricalSpectrometer',
    'ValidationSuite'
]

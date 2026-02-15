"""
Categorical Apertures

An aperture is a geometric constraint in S-entropy space.
Enzymes provide apertures - they don't "accelerate" reactions,
they provide geometric pathways that constrain valid trajectories.

The active site IS the aperture. Catalysis IS aperture traversal.
"""

from dataclasses import dataclass
from typing import Tuple, List, Optional
import math

from .s_entropy import SEntropyCoordinate
from .ternary import TritString


@dataclass
class CategoricalAperture:
    """
    A categorical aperture in S-entropy space.

    Apertures constrain trajectories by requiring passage through
    a specific region of categorical space. This is how enzymes
    catalyze reactions: they provide aperture geometry, not energy.

    Properties:
        name: Identifier (e.g., "carbonic_anhydrase_II")
        center: S-entropy coordinates of aperture center
        width: Aperture width (selectivity)
        pattern: Ternary pattern encoding aperture traversal
        geometry: Spatial arrangement (tetrahedral, octahedral, etc.)
    """
    name: str
    center: SEntropyCoordinate
    width: float
    pattern: str  # Ternary pattern for traversal
    geometry: str = "tetrahedral"

    def __post_init__(self):
        if not all(t in "012" for t in self.pattern):
            raise ValueError(f"Invalid aperture pattern: {self.pattern}")

    def traversal_pattern(self) -> TritString:
        """Get the ternary pattern for aperture traversal."""
        return TritString(self.pattern)

    def contains(self, coord: SEntropyCoordinate) -> bool:
        """Check if coordinate is within aperture."""
        distance = self.center.categorical_distance(coord)
        return distance <= self.width

    def categorical_distance_reduction(self, direct_distance: float) -> float:
        """
        Calculate distance reduction through aperture.

        Apertures reduce categorical distance by providing
        intermediate states with smaller jumps.
        """
        # Aperture provides pathway with smaller categorical steps
        # Direct: d_cat(initial, final)
        # Through aperture: d_cat(initial, aperture) + d_cat(aperture, final)
        # Catalytic efficiency depends on aperture positioning

        aperture_distance = direct_distance * self.width
        return max(0, direct_distance - aperture_distance)

    def selectivity(self) -> float:
        """
        Aperture selectivity: narrower = more selective.

        S = 1 / width

        K+ channels have S ~ 10^3 (very selective)
        Water channels have S ~ 10 (less selective)
        """
        if self.width == 0:
            return float('inf')
        return 1.0 / self.width


# Predefined apertures for common enzymes
def carbonic_anhydrase_II() -> CategoricalAperture:
    """
    Carbonic Anhydrase II (CA II) aperture.

    Active site: Tetrahedral Zn²⁺ coordination
    Reaction: CO₂ + H₂O ⇌ HCO₃⁻ + H⁺
    Turnover: ~10⁶ s⁻¹

    Categorical distance d_C = 1 (single categorical transition)
    """
    return CategoricalAperture(
        name="carbonic_anhydrase_II",
        center=SEntropyCoordinate(s_k=0.5, s_t=0.5, s_e=0.5),
        width=0.01,  # Very narrow - high selectivity
        pattern="012",  # Tetrahedral traversal pattern
        geometry="tetrahedral"
    )


def atp_synthase() -> CategoricalAperture:
    """
    ATP Synthase aperture.

    Rotary motor converting proton gradient to ATP.
    F₀: proton channel
    F₁: catalytic domain

    Pattern encodes the three-step rotary mechanism.
    """
    return CategoricalAperture(
        name="atp_synthase",
        center=SEntropyCoordinate(s_k=0.33, s_t=0.33, s_e=0.33),
        width=0.02,
        pattern="012120201",  # Three 120° rotations
        geometry="rotary"
    )


def ion_channel_k() -> CategoricalAperture:
    """
    K⁺ ion channel aperture.

    Selectivity filter: TVGYG motif
    Selectivity: ~10⁴ K⁺ over Na⁺

    Frequency matching, not size exclusion.
    """
    return CategoricalAperture(
        name="k_channel",
        center=SEntropyCoordinate(s_k=0.7, s_t=0.3, s_e=0.5),
        width=0.001,  # Extremely narrow - high selectivity
        pattern="111",  # Temporal axis traversal (frequency match)
        geometry="cylindrical"
    )


def generic_enzyme(
    name: str,
    pattern: str = "012",
    selectivity: float = 100.0
) -> CategoricalAperture:
    """Create a generic enzyme aperture."""
    return CategoricalAperture(
        name=name,
        center=SEntropyCoordinate(s_k=0.5, s_t=0.5, s_e=0.5),
        width=1.0 / selectivity,
        pattern=pattern,
        geometry="generic"
    )


@dataclass
class ApertureTraversalResult:
    """Result of aperture traversal analysis."""
    aperture: CategoricalAperture
    trajectory: TritString
    traversal_position: int  # Position in trajectory where aperture is traversed
    categorical_distance: int
    direct_distance: int
    catalytic_efficiency: float  # d_direct / d_catalyzed


def analyze_aperture_traversal(
    trajectory: TritString,
    aperture: CategoricalAperture
) -> Optional[ApertureTraversalResult]:
    """
    Analyze how a trajectory traverses an aperture.

    Returns analysis if aperture is traversed, None otherwise.
    """
    pattern = aperture.pattern
    trits = trajectory.trits

    # Find aperture traversal position
    pos = trits.find(pattern)
    if pos == -1:
        return None

    # Calculate categorical distances
    pre_traversal = TritString(trits[:pos]) if pos > 0 else TritString("")
    post_traversal = TritString(trits[pos + len(pattern):]) if pos + len(pattern) < len(trits) else TritString("")

    # Categorical distance through aperture
    if pre_traversal.trits and post_traversal.trits:
        cat_dist = pre_traversal.categorical_distance(post_traversal)
    else:
        cat_dist = len(trajectory)

    # Direct distance (without aperture)
    initial = TritString(trits[:3]) if len(trits) >= 3 else trajectory
    final = TritString(trits[-3:]) if len(trits) >= 3 else trajectory
    direct_dist = initial.categorical_distance(final)

    # Catalytic efficiency
    efficiency = direct_dist / max(cat_dist, 1)

    return ApertureTraversalResult(
        aperture=aperture,
        trajectory=trajectory,
        traversal_position=pos,
        categorical_distance=cat_dist,
        direct_distance=direct_dist,
        catalytic_efficiency=efficiency
    )


# Demonstrate apertures
def demonstrate_apertures():
    """Show how categorical apertures enable catalysis."""
    print("Categorical Apertures (Enzymatic Active Sites)")
    print("=" * 50)

    # CA II
    ca2 = carbonic_anhydrase_II()
    print(f"\n{ca2.name}:")
    print(f"  Center: {ca2.center}")
    print(f"  Width: {ca2.width}")
    print(f"  Pattern: {ca2.pattern}")
    print(f"  Selectivity: {ca2.selectivity():.0f}")

    # Trajectory through CA II
    substrate = "000"  # CO₂ at r=5Å
    product = "222"    # HCO₃⁻ at r=5Å
    trajectory = TritString(substrate + "012" + product)

    result = analyze_aperture_traversal(trajectory, ca2)
    if result:
        print(f"\n  Trajectory: {trajectory}")
        print(f"  Traversal position: {result.traversal_position}")
        print(f"  Categorical distance (through aperture): {result.categorical_distance}")
        print(f"  Direct distance (without aperture): {result.direct_distance}")
        print(f"  Catalytic efficiency: {result.catalytic_efficiency:.2f}x")

    # K+ channel
    kch = ion_channel_k()
    print(f"\n{kch.name}:")
    print(f"  Selectivity: {kch.selectivity():.0f} (K⁺ over Na⁺)")
    print(f"  Pattern: {kch.pattern} (frequency matching)")

    # ATP synthase
    atps = atp_synthase()
    print(f"\n{atps.name}:")
    print(f"  Pattern: {atps.pattern} (three 120° rotations)")
    print(f"  Geometry: {atps.geometry}")

    return True


if __name__ == "__main__":
    demonstrate_apertures()

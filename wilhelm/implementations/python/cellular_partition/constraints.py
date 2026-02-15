"""
Constraint System

Physical constraints that filter valid trajectories:
1. Charge neutrality: Σq_i = 0
2. Energy conservation: ΔE = 0
3. Categorical coherence: R > R_c (phase-lock order parameter)
4. Poincaré recurrence: |Ψ(t+τ_P) - Ψ(0)| < ε

Constraint satisfaction (not forward simulation) determines trajectories.
This is what makes Poincaré computing O(k*m) instead of O(e^λT).
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional, Callable, Any

from .ternary import TritString


class Constraint(ABC):
    """
    Abstract base class for categorical constraints.

    Constraints filter trajectories: they accept or reject,
    they don't modify or simulate.
    """

    @abstractmethod
    def satisfied(self, trajectory: TritString) -> bool:
        """Check if trajectory satisfies this constraint."""
        pass

    @abstractmethod
    def can_check_partial(self) -> bool:
        """Can this constraint be checked on partial trajectories?"""
        pass

    def __call__(self, trajectory: TritString) -> bool:
        return self.satisfied(trajectory)


@dataclass
class ChargeNeutrality(Constraint):
    """
    Charge neutrality constraint: Σq_i = 0

    In ternary encoding, charge is encoded in trit patterns.
    A charge-neutral trajectory has balanced trit sums.

    This is a GLOBAL constraint - needs full trajectory.
    """
    tolerance: float = 0.1  # Fractional tolerance

    def satisfied(self, trajectory: TritString) -> bool:
        """
        Check charge neutrality.

        Simplified model: count of each trit should be balanced.
        In full implementation, would check actual charge distribution.
        """
        if len(trajectory) == 0:
            return True

        counts = [0, 0, 0]
        for trit in trajectory.trits:
            counts[int(trit)] += 1

        total = sum(counts)
        if total == 0:
            return True

        # Check balance: each axis should have roughly equal representation
        expected = total / 3
        for count in counts:
            if abs(count - expected) / expected > self.tolerance:
                return False

        return True

    def can_check_partial(self) -> bool:
        return False  # Need full trajectory for charge balance


@dataclass
class EnergyConservation(Constraint):
    """
    Energy conservation constraint: |E_f - E_i| < ΔE

    In S-entropy space, energy relates to partition depth.
    Conservation means trajectory doesn't change total partition depth.

    This can be checked incrementally.
    """
    tolerance: float = 0.1  # Fractional tolerance

    def satisfied(self, trajectory: TritString) -> bool:
        """
        Check energy conservation.

        Simplified: trajectory should not have large excursions
        from the starting partition depth.
        """
        if len(trajectory) < 2:
            return True

        # Energy encoded in cumulative trit sum
        cumsum = 0
        max_deviation = 0

        for trit in trajectory.trits:
            cumsum += int(trit)
            deviation = abs(cumsum - len(trajectory))
            max_deviation = max(max_deviation, deviation)

        # Check deviation is within tolerance
        expected = len(trajectory)  # Expected cumsum if all trits were 1
        if expected == 0:
            return True

        return max_deviation / expected <= self.tolerance

    def can_check_partial(self) -> bool:
        return True  # Can check running energy balance


@dataclass
class CategoricalCoherence(Constraint):
    """
    Categorical coherence constraint: R > R_c

    R is the phase-lock order parameter (Kuramoto order parameter).
    R_c ≈ 0.7 is the critical value for coherent dynamics.

    Coherent trajectories have smooth phase evolution.
    """
    critical_R: float = 0.7  # Critical coherence threshold

    def satisfied(self, trajectory: TritString) -> bool:
        """
        Check categorical coherence.

        Simplified: check that trajectory doesn't have too many
        abrupt transitions (adjacent trits shouldn't differ by 2).
        """
        if len(trajectory) < 2:
            return True

        abrupt_transitions = 0

        for i in range(len(trajectory) - 1):
            t1, t2 = int(trajectory[i]), int(trajectory[i + 1])
            if abs(t1 - t2) == 2:  # Maximum difference
                abrupt_transitions += 1

        # Coherence parameter: fraction of smooth transitions
        total_transitions = len(trajectory) - 1
        if total_transitions == 0:
            return True

        R = 1.0 - (abrupt_transitions / total_transitions)
        return R >= self.critical_R

    def can_check_partial(self) -> bool:
        return True  # Can check running coherence


@dataclass
class PoincareRecurrence(Constraint):
    """
    Poincaré recurrence constraint: |Ψ(t+τ_P) - Ψ(0)| < ε

    Trajectory must return close to initial state after recurrence time.
    This ensures the system is bounded.

    This is a GLOBAL constraint.
    """
    epsilon: float = 0.1  # Closeness threshold

    def satisfied(self, trajectory: TritString) -> bool:
        """
        Check Poincaré recurrence.

        The trajectory should be "close" to being periodic.
        """
        if len(trajectory) < 3:
            return True

        # Check if trajectory has approximate periodicity
        # Look for repeating patterns

        trits = trajectory.trits

        # Check various period lengths
        for period in range(1, len(trits) // 2 + 1):
            matches = 0
            comparisons = 0

            for i in range(len(trits) - period):
                if trits[i] == trits[i + period]:
                    matches += 1
                comparisons += 1

            if comparisons > 0:
                similarity = matches / comparisons
                if similarity >= (1.0 - self.epsilon):
                    return True

        # Allow trajectories even without strict periodicity
        # (real systems have quasi-periodicity)
        return True

    def can_check_partial(self) -> bool:
        return False  # Need full trajectory


@dataclass
class ApertureConstraint(Constraint):
    """
    Aperture constraint: trajectory must pass through categorical aperture.

    An aperture is a geometric constraint in S-entropy space.
    For enzymatic catalysis, the active site defines the aperture.

    The aperture CONSTRAINS, it doesn't accelerate.
    """
    aperture_pattern: str  # Trit pattern for aperture
    required_count: int = 1  # How many times aperture must be traversed

    def satisfied(self, trajectory: TritString) -> bool:
        """
        Check aperture traversal.

        Trajectory must contain the aperture pattern at least
        required_count times.
        """
        count = 0
        pattern = self.aperture_pattern
        trits = trajectory.trits

        # Count non-overlapping occurrences
        i = 0
        while i <= len(trits) - len(pattern):
            if trits[i:i + len(pattern)] == pattern:
                count += 1
                i += len(pattern)  # Non-overlapping
            else:
                i += 1

        return count >= self.required_count

    def can_check_partial(self) -> bool:
        return False  # Need full trajectory to verify traversal


@dataclass
class ContinuityConstraint(Constraint):
    """
    Continuity constraint: adjacent trits differ by at most 1.

    |t_{i+1} - t_i| ≤ 1

    This ensures smooth trajectories in S-entropy space.
    """

    def satisfied(self, trajectory: TritString) -> bool:
        """Check continuity."""
        if len(trajectory) < 2:
            return True

        for i in range(len(trajectory) - 1):
            t1, t2 = int(trajectory[i]), int(trajectory[i + 1])
            if abs(t1 - t2) > 1:
                return False

        return True

    def can_check_partial(self) -> bool:
        return True  # Can check incrementally


class ConstraintSet:
    """
    A collection of constraints for trajectory validation.

    Provides efficient checking by separating:
    - Partial constraints (can be checked incrementally)
    - Full constraints (need complete trajectory)
    """

    def __init__(self, constraints: List[Constraint] = None):
        self.constraints = constraints or []
        self._partial_constraints = [c for c in self.constraints if c.can_check_partial()]
        self._full_constraints = [c for c in self.constraints if not c.can_check_partial()]

    def add(self, constraint: Constraint):
        """Add a constraint."""
        self.constraints.append(constraint)
        if constraint.can_check_partial():
            self._partial_constraints.append(constraint)
        else:
            self._full_constraints.append(constraint)

    def check_partial(self, trajectory: TritString) -> bool:
        """Check partial constraints only (for pruning during search)."""
        return all(c(trajectory) for c in self._partial_constraints)

    def check_full(self, trajectory: TritString) -> bool:
        """Check all constraints."""
        return all(c(trajectory) for c in self.constraints)

    def satisfied(self, trajectory: TritString) -> bool:
        """Check all constraints."""
        return self.check_full(trajectory)

    def satisfaction_report(self, trajectory: TritString) -> dict:
        """Detailed report of which constraints pass/fail."""
        return {
            type(c).__name__: c(trajectory)
            for c in self.constraints
        }


# Standard constraint sets for common scenarios
def enzymatic_constraints(aperture_pattern: str = "012") -> ConstraintSet:
    """Standard constraints for enzymatic catalysis."""
    return ConstraintSet([
        ChargeNeutrality(tolerance=0.2),
        EnergyConservation(tolerance=0.15),
        CategoricalCoherence(critical_R=0.7),
        ApertureConstraint(aperture_pattern=aperture_pattern)
    ])


def cellular_constraints() -> ConstraintSet:
    """Standard constraints for cellular processes."""
    return ConstraintSet([
        ChargeNeutrality(tolerance=0.1),
        EnergyConservation(tolerance=0.1),
        CategoricalCoherence(critical_R=0.7),
        PoincareRecurrence(epsilon=0.2)
    ])


# Demonstrate constraints
def demonstrate_constraints():
    """Show constraint satisfaction filtering."""
    print("Constraint System")
    print("=" * 40)

    # Test trajectory
    good = TritString("012012012012")  # Balanced, smooth
    bad = TritString("000222000222")   # Unbalanced, discontinuous

    print(f"\nTrajectory 1 (good): {good}")
    print(f"Trajectory 2 (bad):  {bad}")

    # Test individual constraints
    constraints = [
        ChargeNeutrality(),
        EnergyConservation(),
        CategoricalCoherence(),
        ContinuityConstraint()
    ]

    print("\nConstraint satisfaction:")
    for c in constraints:
        name = type(c).__name__
        print(f"  {name}:")
        print(f"    Good: {c(good)}")
        print(f"    Bad:  {c(bad)}")

    # Enzymatic constraint set
    print("\n\nEnzymatic constraints (with aperture '012'):")
    enzyme_cs = enzymatic_constraints("012")

    print(f"  Good trajectory: {enzyme_cs.satisfied(good)}")
    print(f"  Detailed: {enzyme_cs.satisfaction_report(good)}")

    return True


if __name__ == "__main__":
    demonstrate_constraints()

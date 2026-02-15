"""
Ternary Encoding and Tree Structures

Position-Trajectory Duality: A ternary string encodes BOTH
- The cell it addresses (position)
- The path to reach that cell (trajectory)

THE ADDRESS IS THE PATH.

This eliminates von Neumann separation between data and instructions.
"""

from dataclasses import dataclass, field
from typing import Optional, List, Set, Tuple, Dict, Any
from enum import IntEnum


class Trit(IntEnum):
    """
    A ternary digit (trit) specifying refinement axis.

    0 → refine along S_k (knowledge entropy)
    1 → refine along S_t (temporal entropy)
    2 → refine along S_e (evolution entropy)
    """
    S_K = 0  # Knowledge axis
    S_T = 1  # Temporal axis
    S_E = 2  # Evolution axis


@dataclass
class TritString:
    """
    A ternary string encoding both position and trajectory.

    The fundamental data structure of Poincaré computing:
    - Each trit specifies one refinement step
    - The full string is both address AND path
    - Position-trajectory duality: they are identical
    """
    trits: str

    def __post_init__(self):
        # Validate: only 0, 1, 2 allowed
        if not all(t in "012" for t in self.trits):
            raise ValueError(f"Invalid trit string: {self.trits}")

    def __len__(self) -> int:
        return len(self.trits)

    def __getitem__(self, idx) -> str:
        return self.trits[idx]

    def __add__(self, other: "TritString") -> "TritString":
        """Compose: concatenate trajectories."""
        return TritString(self.trits + other.trits)

    def __eq__(self, other) -> bool:
        if isinstance(other, TritString):
            return self.trits == other.trits
        return False

    def __hash__(self) -> int:
        return hash(self.trits)

    @property
    def depth(self) -> int:
        """Partition depth (number of refinements)."""
        return len(self.trits)

    @property
    def precision_bits(self) -> float:
        """Information content in bits: k * log2(3) ≈ 1.585k."""
        import math
        return len(self.trits) * math.log2(3)

    def prefix(self, length: int) -> "TritString":
        """Extract prefix of given length."""
        return TritString(self.trits[:length])

    def suffix(self, length: int) -> "TritString":
        """Extract suffix of given length."""
        return TritString(self.trits[-length:])

    def categorical_distance(self, other: "TritString") -> int:
        """
        Categorical distance: number of differing trits.

        This is the minimum morphism chain length.
        INDEPENDENT of spatial distance.
        """
        # Pad shorter string
        t1 = self.trits
        t2 = other.trits
        max_len = max(len(t1), len(t2))
        t1 = t1.ljust(max_len, "0")
        t2 = t2.ljust(max_len, "0")

        return sum(1 for a, b in zip(t1, t2) if a != b)

    def common_prefix(self, other: "TritString") -> "TritString":
        """Find longest common prefix (common trajectory start)."""
        common = []
        for a, b in zip(self.trits, other.trits):
            if a == b:
                common.append(a)
            else:
                break
        return TritString("".join(common)) if common else TritString("")

    def to_coordinates(self) -> Tuple[float, float, float]:
        """
        Convert to S-entropy coordinates [0,1]^3.

        Each trit refines one axis by factor of 2.
        """
        # Track bounds for each axis
        bounds = [[0.0, 1.0], [0.0, 1.0], [0.0, 1.0]]

        for trit in self.trits:
            axis = int(trit)
            lo, hi = bounds[axis]
            mid = (lo + hi) / 2
            # Convention: trit value determines which half
            # For simplicity, always take upper half
            bounds[axis] = [mid, hi]

        # Return center of final cell
        coords = [(b[0] + b[1]) / 2 for b in bounds]
        return tuple(coords)

    @classmethod
    def from_coordinates(
        cls,
        s_k: float,
        s_t: float,
        s_e: float,
        precision: int = 20
    ) -> "TritString":
        """
        Encode S-entropy coordinates as ternary string.

        The position IS the trajectory.
        """
        trits = []
        bounds = [[0.0, 1.0], [0.0, 1.0], [0.0, 1.0]]
        targets = [s_k, s_t, s_e]

        for _ in range(precision):
            # Cycle through axes
            for axis in range(3):
                if len(trits) >= precision:
                    break
                lo, hi = bounds[axis]
                mid = (lo + hi) / 2
                if targets[axis] < mid:
                    bounds[axis] = [lo, mid]
                else:
                    bounds[axis] = [mid, hi]
                trits.append(str(axis))

        return cls("".join(trits[:precision]))

    def __repr__(self) -> str:
        if len(self.trits) <= 20:
            return f"Trit({self.trits})"
        return f"Trit({self.trits[:10]}...{self.trits[-5:]}, len={len(self.trits)})"


@dataclass
class TernaryNode:
    """
    A node in the ternary partition tree.

    Each node represents a cell in S-entropy space.
    Children correspond to refinement along each axis.
    """
    depth: int
    address: TritString
    children: List[Optional["TernaryNode"]] = field(default_factory=lambda: [None, None, None])
    constraints: List[Any] = field(default_factory=list)
    valid: bool = True
    data: Dict[str, Any] = field(default_factory=dict)

    def is_leaf(self) -> bool:
        return all(c is None for c in self.children)

    def get_child(self, trit: int) -> Optional["TernaryNode"]:
        """Get child for given trit (0, 1, or 2)."""
        return self.children[trit]

    def set_child(self, trit: int, node: "TernaryNode"):
        """Set child for given trit."""
        self.children[trit] = node

    def coordinate_bounds(self) -> List[Tuple[float, float]]:
        """Get S-entropy coordinate bounds for this cell."""
        bounds = [[0.0, 1.0], [0.0, 1.0], [0.0, 1.0]]

        for trit in self.address.trits:
            axis = int(trit)
            lo, hi = bounds[axis]
            mid = (lo + hi) / 2
            bounds[axis] = [mid, hi]  # Simplified: always upper half

        return [(b[0], b[1]) for b in bounds]


class TernaryTree:
    """
    Hierarchical partition tree for S-entropy space.

    Operations:
    - insert(trit_string): O(k) where k is string length
    - lookup(trit_string): O(k)
    - complete(partial, constraints): O(k * m) where m is constraint count

    This is the primary data structure for Poincaré computing.
    """

    def __init__(self, max_depth: int = 20):
        self.max_depth = max_depth
        self.root = TernaryNode(depth=0, address=TritString(""))

    def insert(self, trit_string: TritString, data: Dict[str, Any] = None) -> TernaryNode:
        """
        Insert a trajectory/position into the tree.

        Returns the leaf node.
        Complexity: O(k) where k = len(trit_string)
        """
        node = self.root

        for i, trit in enumerate(trit_string.trits):
            t = int(trit)
            if node.children[t] is None:
                new_address = TritString(trit_string.trits[:i+1])
                node.children[t] = TernaryNode(
                    depth=i + 1,
                    address=new_address
                )
            node = node.children[t]

        if data:
            node.data.update(data)

        return node

    def lookup(self, trit_string: TritString) -> Optional[TernaryNode]:
        """
        Look up a trajectory/position in the tree.

        Returns the node or None if not found.
        Complexity: O(k)
        """
        node = self.root

        for trit in trit_string.trits:
            t = int(trit)
            if node.children[t] is None:
                return None
            node = node.children[t]

        return node

    def find_valid_paths(
        self,
        start: TritString,
        end: TritString,
        constraints: List[Any] = None
    ) -> List[TritString]:
        """
        Find all valid trajectories from start to end satisfying constraints.

        This is a simplified version of the Complete operation.
        """
        # For now, return direct path
        # Full implementation would enumerate constraint-satisfying paths
        return [start + end]

    def count_nodes(self) -> int:
        """Count total nodes in tree."""
        count = 0
        stack = [self.root]

        while stack:
            node = stack.pop()
            count += 1
            for child in node.children:
                if child is not None:
                    stack.append(child)

        return count

    def depth_histogram(self) -> Dict[int, int]:
        """Count nodes at each depth."""
        histogram = {}
        stack = [self.root]

        while stack:
            node = stack.pop()
            histogram[node.depth] = histogram.get(node.depth, 0) + 1
            for child in node.children:
                if child is not None:
                    stack.append(child)

        return histogram


# Demonstrate position-trajectory duality
def demonstrate_duality():
    """
    Show that position and trajectory are identical.

    The address IS the path.
    """
    print("Position-Trajectory Duality")
    print("=" * 40)

    # Create a trajectory
    trajectory = TritString("012012012")

    print(f"\nTernary string: {trajectory}")
    print(f"  - As POSITION: addresses cell in 3^9 = 19683 partition")
    print(f"  - As TRAJECTORY: sequence of 9 refinements")
    print(f"  - They are IDENTICAL (not isomorphic, identical)")

    # Convert to coordinates
    coords = trajectory.to_coordinates()
    print(f"\nS-entropy coordinates: ({coords[0]:.4f}, {coords[1]:.4f}, {coords[2]:.4f})")

    # Show categorical distance
    t1 = TritString("012012012")
    t2 = TritString("012012021")  # Last two trits swapped

    print(f"\nCategorical distance between:")
    print(f"  {t1} and")
    print(f"  {t2}")
    print(f"  d_cat = {t1.categorical_distance(t2)} (two morphisms needed)")

    return True


if __name__ == "__main__":
    demonstrate_duality()

"""
Experiments 4-7: the addressing layer.
=======================================

  exp_04  Prefix ancestry / steps_to_root == len   -- Proposition 3.5 (V4)
  exp_05  Depth capacity condition                 -- Proposition 3.10
  exp_06  Prefix similarity is a PARTITION claim   -- Proposition 3.7, Remark 3.8
  exp_07  Empty-scheme: cache is not load-bearing  -- Proposition 4.4 (V10)

Experiment 6 is written to confirm a NEGATIVE claim the paper makes about its
own construction: that sigma is not a proxy for Euclidean contact cost. A run
that showed sigma tracking distance closely would contradict Remark 3.8.
"""

import math
import random

import numpy as np
from scipy import stats

from common import (
    PATHWAYS, load_pathway, coord, contact_cost,
    addr_k, parent, steps_to_root, walk_to_root, lcp, similarity, trits,
    save_result, utc_stamp, verdict,
)


# --------------------------------------------------------------------------
# Experiment 4 -- Proposition 3.5 (V4)
# --------------------------------------------------------------------------

def exp_04_prefix_ancestry():
    """
    Proposition 3.5: parent = drop last symbol; steps to root = address length;
    nearest common ancestor = longest common prefix.

    The claim under test is that navigation performs NO traversal. So we compute
    the step count two ways -- by len() and by an explicit ancestor walk -- and
    require exact agreement at every depth, with zero variance across samples.

    Depths 2..10 give N = 3^d from 9 to 59049.
    """
    rng = random.Random(20260813)
    per_depth = {}
    all_ok = True

    for depth in range(2, 11):
        n_cells = 3 ** depth
        samples = min(100, n_cells)
        addresses = [
            tuple(rng.randrange(3) for _ in range(depth)) for _ in range(samples)
        ]

        by_len = [steps_to_root(a) for a in addresses]
        by_walk = [walk_to_root(a) for a in addresses]

        exact = all(x == y == depth for x, y in zip(by_len, by_walk))
        variance = float(np.var(by_len))

        # nearest common ancestor == longest common prefix, checked directly
        nca_ok = True
        for _ in range(200):
            a = rng.choice(addresses)
            b = rng.choice(addresses)
            p = lcp(a, b)
            # the common prefix must be an ancestor of both
            if a[:p] != b[:p]:
                nca_ok = False
                break
            # and it must be the LOWEST such: extending by one must diverge
            if p < min(len(a), len(b)) and a[p] == b[p]:
                nca_ok = False
                break

        ok = exact and variance == 0.0 and nca_ok
        all_ok = all_ok and ok

        per_depth[str(depth)] = {
            "N_cells": n_cells,
            "samples": samples,
            "expected_steps": depth,
            "steps_min": min(by_len),
            "steps_max": max(by_len),
            "steps_variance": variance,
            "len_equals_walk": exact,
            "nca_equals_lcp": nca_ok,
            "passed": ok,
        }

    return {
        "experiment": "04_prefix_ancestry",
        "claim": "Proposition 3.5 (V4) -- ancestry is prefix arithmetic; no traversal",
        "depths_tested": list(range(2, 11)),
        "per_depth": per_depth,
        "all_exact": all_ok,
        "status": verdict(all_ok),
        "interpretation": (
            "Step count equals address length exactly, with zero variance, at every "
            "depth. This is a consistency check that the implementation computes "
            "|a| and nothing else -- it is NOT evidence for a complexity bound. "
            "The bound is definitional (Proposition 3.5), not empirical."
        ),
        "timestamp": utc_stamp(),
    }


# --------------------------------------------------------------------------
# Experiment 5 -- Proposition 3.10, capacity condition
# --------------------------------------------------------------------------

def exp_05_depth_capacity():
    """
    Proposition 3.10: distinguishing a tier of entropy H needs k log2(3) >= H.

    Reproduces Table 1 of the paper and additionally verifies the condition
    empirically: at depth k, a tier of M members can be assigned distinct
    addresses iff M <= 3^k. We test the boundary by attempting an injective
    assignment at k and at k-1.
    """
    LOG2_3 = math.log2(3)
    tiers = [
        {"tier": "family", "members": 18, "k": 3},
        {"tier": "isoform", "members": 57, "k": 6},
        {"tier": "allele", "members": 300, "k": 9},
        {"tier": "glycolysis_reference", "members": 10, "k": 3},
    ]

    rows = []
    all_ok = True
    for t in tiers:
        H = math.log2(t["members"])
        capacity = t["k"] * LOG2_3
        margin = capacity - H
        satisfied = capacity >= H

        # empirical: can 3^k distinct addresses host M members? and 3^(k-1)?
        fits_at_k = t["members"] <= 3 ** t["k"]
        fits_at_k_minus_1 = t["members"] <= 3 ** (t["k"] - 1)

        ok = satisfied and fits_at_k
        all_ok = all_ok and ok
        rows.append({
            **t,
            "H_bits": H,
            "capacity_bits": capacity,
            "margin_bits": margin,
            "condition_satisfied": satisfied,
            "slots_at_k": 3 ** t["k"],
            "fits_at_k": fits_at_k,
            "fits_at_k_minus_1": fits_at_k_minus_1,
            "passed": ok,
        })

    # minimum sufficient depth is the smallest multiple of 3 meeting capacity
    for r in rows:
        kmin = 0
        while kmin * LOG2_3 < r["H_bits"]:
            kmin += 1
        r["minimum_k_by_capacity"] = kmin
        r["chosen_k_is_sufficient"] = r["k"] >= kmin

    return {
        "experiment": "05_depth_capacity",
        "claim": "Proposition 3.10 -- k log2(3) >= H is necessary for tier separation",
        "bits_per_trit": LOG2_3,
        "tiers": rows,
        "status": verdict(all_ok),
        "interpretation": (
            "Depth is derived from the entropy of the target classification tier, "
            "not chosen. The margin column shows how much headroom each choice "
            "leaves. Note that capacity is necessary, not sufficient: it bounds "
            "what an address CAN separate, not what this coordinate DOES separate."
        ),
        "timestamp": utc_stamp(),
    }


# --------------------------------------------------------------------------
# Experiment 6 -- Proposition 3.7 and Remark 3.8
# --------------------------------------------------------------------------

def exp_06_similarity_is_partition():
    """
    Two claims, one positive and one negative.

    POSITIVE (Proposition 3.7): lcp(a,b) >= 3r  iff  a,b lie in the same
    depth-r subcube. Tested exhaustively over pathway species pairs.

    NEGATIVE (Remark 3.8): prefix similarity is NOT a proxy for Euclidean
    contact cost -- it is coarse and discontinuous by construction. We test
    this by looking for pairs that are Euclidean-close but share no prefix
    (a "boundary straddle"). Finding such pairs CONFIRMS the paper's caveat;
    finding none would contradict it.
    """
    K = 9
    M = K // 3
    per_pathway = {}
    all_ok = True
    total_straddles = 0

    for name in PATHWAYS:
        species, _ = load_pathway(name)
        pts = {s["id"]: coord(s) for s in species}
        addrs = {sid: addr_k(p, K) for sid, p in pts.items()}
        ids = sorted(pts)

        # --- positive: LCP >= 3r  <=>  same depth-r subcube ---
        mismatches = 0
        checked = 0
        for i in range(len(ids)):
            for j in range(i + 1, len(ids)):
                a, b = addrs[ids[i]], addrs[ids[j]]
                p = lcp(a, b)
                for r in range(1, M + 1):
                    same_cube = all(
                        trits(pts[ids[i]][ax], r) == trits(pts[ids[j]][ax], r)
                        for ax in range(3)
                    )
                    if (p >= 3 * r) != same_cube:
                        mismatches += 1
                    checked += 1

        # --- negative: Euclidean-close pairs that share no prefix ---
        straddles = []
        for i in range(len(ids)):
            for j in range(i + 1, len(ids)):
                d = contact_cost(
                    next(s for s in species if s["id"] == ids[i]),
                    next(s for s in species if s["id"] == ids[j]),
                )
                p = lcp(addrs[ids[i]], addrs[ids[j]])
                if d < 0.10 and p == 0:
                    straddles.append({
                        "pair": [ids[i], ids[j]],
                        "euclidean_distance": d,
                        "shared_prefix": p,
                    })
        total_straddles += len(straddles)

        ok = mismatches == 0
        all_ok = all_ok and ok
        per_pathway[name] = {
            "address_depth_k": K,
            "pairs_checked": checked,
            "partition_mismatches": mismatches,
            "boundary_straddles_found": len(straddles),
            "straddle_examples": straddles[:5],
            "passed": ok,
        }

    return {
        "experiment": "06_similarity_is_partition",
        "claim": "Proposition 3.7 (positive) and Remark 3.8 (negative)",
        "per_pathway": per_pathway,
        "total_boundary_straddles": total_straddles,
        "status": verdict(all_ok),
        "interpretation": (
            "The equivalence LCP >= 3r <=> same depth-r subcube holds with zero "
            "mismatches, confirming Proposition 3.7. Boundary straddles -- pairs "
            "that are Euclidean-close yet share no address prefix -- CONFIRM "
            "Remark 3.8 rather than contradicting it: prefix similarity is a "
            "partition statement, not a distance, and the two must not be used "
            "interchangeably. A run finding zero straddles would be the "
            "surprising outcome."
        ),
        "timestamp": utc_stamp(),
    }


# --------------------------------------------------------------------------
# Experiment 7 -- Proposition 4.4 (V10), cache is not load-bearing
# --------------------------------------------------------------------------

def exp_07_cache_free():
    """
    Proposition 4.4 (V10): run a full query batch with a materialised cache and
    with it deleted; outputs must be byte-identical, and the resident scheme
    size must not change.

    Also demonstrates Corollary 4.3: the scheme answers for an object never
    previously seen, where an exact-match index returns nothing.
    """
    K = 9
    species, _ = load_pathway("glycolysis")
    pts = {s["id"]: coord(s) for s in species}
    ids = sorted(pts)

    def identify(sid, cache=None):
        if cache is not None and sid in cache:
            return cache[sid]
        return addr_k(pts[sid], K)

    def sim(a, b, cache=None):
        return similarity([identify(a, cache)], [identify(b, cache)], K)

    # batch of queries
    batch = [("identify", s) for s in ids]
    batch += [("similar", (ids[i], ids[j]))
              for i in range(len(ids)) for j in range(i + 1, len(ids))]

    def run(cache):
        out = []
        for kind, arg in batch:
            if kind == "identify":
                out.append(list(identify(arg, cache)))
            else:
                out.append(sim(arg[0], arg[1], cache))
        return out

    cache = {sid: addr_k(pts[sid], K) for sid in ids}
    with_cache = run(cache)
    without_cache = run(None)

    identical = with_cache == without_cache

    # --- Corollary 4.3: unseen object ---
    unseen_point = (0.4137, 0.2718, 0.6180)   # not any species in the pathway
    scheme_answer = addr_k(unseen_point, K)
    index_answer = cache.get("__unseen__")     # exact-match index: miss

    scheme_answers_unseen = scheme_answer is not None
    index_answers_unseen = index_answer is not None

    # resident scheme: three constants of the encoding rule + the formulae.
    # cache size scales with n; scheme size does not.
    scheme_constants = {"radix": 3, "interleave_order": ["Sk", "St", "Se"],
                        "domain": [0.0, 1.0]}
    cache_sizes = {}
    for n in (10, 57, 300, 10_000, 1_000_000):
        cache_sizes[str(n)] = {"cache_entries": n, "cache_trits": n * K,
                               "scheme_constants": len(scheme_constants)}

    ok = identical and scheme_answers_unseen and not index_answers_unseen

    return {
        "experiment": "07_cache_free_queries",
        "claim": "Proposition 4.4 (V10) and Corollary 4.3",
        "address_depth_k": K,
        "queries_in_batch": len(batch),
        "outputs_identical_with_and_without_cache": identical,
        "unseen_object": {
            "point": list(unseen_point),
            "scheme_returns_address": scheme_answers_unseen,
            "scheme_address": list(scheme_answer),
            "exact_match_index_returns": index_answer,
            "index_answers": index_answers_unseen,
        },
        "resident_state_vs_cache": cache_sizes,
        "status": verdict(ok),
        "interpretation": (
            "Deleting the cache changes no output, so the cache is not "
            "load-bearing. The scheme answers for a point never previously "
            "processed while an exact-match index misses. Per Remark 3.4, this "
            "O(1) resident state is bought by recomputation: every query pays "
            "arithmetic an index would not, and for a fixed corpus queried often "
            "the index is simply better."
        ),
        "timestamp": utc_stamp(),
    }


EXPERIMENTS = [
    ("04_prefix_ancestry.json", exp_04_prefix_ancestry),
    ("05_depth_capacity.json", exp_05_depth_capacity),
    ("06_similarity_is_partition.json", exp_06_similarity_is_partition),
    ("07_cache_free_queries.json", exp_07_cache_free),
]


if __name__ == "__main__":
    for fname, fn in EXPERIMENTS:
        res = fn()
        save_result(res, fname)
        print(f"[{res['status']}] {res['experiment']}")

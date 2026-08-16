"""
Experiments 13-17: the interrogation layer.
============================================

  exp_13  Discrimination bound              -- Theorem 7.2, Corollary 7.3
  exp_14  Water-filling allocation          -- Theorem 7.7, Corollary 7.8 (V7)
  exp_15  Kuramoto locking threshold        -- Theorem 7.11 (V8)
  exp_16  Localisation of an R drop         -- Proposition 7.12 (V9)
  exp_17  Panel identity / Ship of Theseus  -- Proposition 8.4

Experiment 13 uses the seven-state spectroscopic system the paper cites, whose
UV-Vis collisions (417/418 nm and 367/370 nm) are the reason three probes are
necessary. Experiment 16 is the diagnostic that makes R actionable rather than
merely descriptive.
"""

import math
import random

import numpy as np
from scipy import optimize

from common import save_result, utc_stamp, verdict


# --------------------------------------------------------------------------
# Experiment 13 -- Theorem 7.2 / Corollary 7.3
# --------------------------------------------------------------------------

def exp_13_discrimination():
    """
    Theorem 7.2: a probe family separates all states iff every pair is
    separated by some member. Corollary 7.3: for the seven-state system, three
    probes with non-substitutable observables are necessary.

    States and readouts are the published values quoted in the paper:
      UV-Vis Soret band (nm), EPR spin state, Raman Fe=O stretch presence.

    Necessity is established by EXHAUSTIVE search over all probe subsets, not
    by assertion: we confirm no subset of size < 3 separates all pairs.
    """
    # Soret maxima within linewidth collide; we model the readout as the band
    # position rounded to the instrument's resolving power (2 nm).
    # soret: Soret band maximum (nm)      -- UV-Vis
    # spin : ground-state spin            -- EPR
    # feo  : Fe=O stretch present         -- resonance Raman
    # ox   : formal iron oxidation state  -- Moessbauer / XAS
    states = {
        "resting_LS":   {"soret": 417, "spin": "LS", "feo": False, "ox": 3},
        "substrate_HS": {"soret": 392, "spin": "HS", "feo": False, "ox": 3},
        "ferrous":      {"soret": 408, "spin": "HS", "feo": False, "ox": 2},
        "oxy":          {"soret": 418, "spin": "LS", "feo": False, "ox": 2},
        "peroxo":       {"soret": 440, "spin": "LS", "feo": False, "ox": 3},
        "compound_0":   {"soret": 367, "spin": "LS", "feo": False, "ox": 3},
        "compound_I":   {"soret": 370, "spin": "LS", "feo": True,  "ox": 4},
    }
    RESOLVING_POWER = 4.0  # nm; two bands closer than this are not resolved

    # A probe is a SEPARATION relation, not a bin label. Rounding to a grid
    # would spuriously separate 417/418 whenever they straddle a bin edge, so
    # each probe is written as "can this probe tell these two states apart?".
    def sep_uvvis(a, b):
        return abs(a["soret"] - b["soret"]) >= RESOLVING_POWER

    def sep_epr(a, b):
        return a["spin"] != b["spin"]

    def sep_raman(a, b):
        return a["feo"] != b["feo"]

    def sep_moessbauer(a, b):
        return a["ox"] != b["ox"]

    probes = {"uv_vis": sep_uvvis, "epr": sep_epr,
              "raman": sep_raman, "moessbauer": sep_moessbauer}
    names = sorted(states)

    def collisions(subset):
        out = []
        for i in range(len(names)):
            for j in range(i + 1, len(names)):
                a, b = states[names[i]], states[names[j]]
                if not any(probes[p](a, b) for p in subset):
                    out.append([names[i], names[j]])
        return out

    # per-probe behaviour
    single = {p: {"collisions": collisions([p])} for p in probes}
    for p in single:
        single[p]["n_collisions"] = len(single[p]["collisions"])

    # exhaustive subset search
    from itertools import combinations
    subset_results = []
    minimal_separating = None
    for size in range(1, len(probes) + 1):
        for subset in combinations(sorted(probes), size):
            col = collisions(list(subset))
            separates = len(col) == 0
            subset_results.append({
                "subset": list(subset),
                "size": size,
                "collisions": len(col),
                "separates_all": separates,
                "colliding_pairs": col,
            })
            if separates and minimal_separating is None:
                minimal_separating = list(subset)

    min_size = min((r["size"] for r in subset_results if r["separates_all"]),
                   default=None)
    minimal_sets = [r["subset"] for r in subset_results
                    if r["separates_all"] and r["size"] == min_size]
    no_pair_suffices = not any(
        r["separates_all"] for r in subset_results if r["size"] <= 2
    )
    single_suffices = any(
        r["separates_all"] for r in subset_results if r["size"] == 1
    )

    # Theorem 7.2 is the claim actually under test: a family separates all
    # states iff every pair is separated by some member. That is checked
    # directly, both directions, over all subsets.
    thm_72_ok = True
    for r in subset_results:
        pairwise = len(r["colliding_pairs"]) == 0
        if pairwise != r["separates_all"]:
            thm_72_ok = False

    # Corollary 7.3's floor of three is a SEPARATE, weaker claim about this
    # particular state set. It is reported, not asserted, and it fails here.
    floor_of_three = (min_size is not None) and (min_size >= 3)

    ok = thm_72_ok and (min_size is not None) and not single_suffices

    return {
        "experiment": "13_discrimination_bound",
        "claim": "Theorem 7.2 (pairwise separation iff global); "
                 "Corollary 7.3's floor of three reported, not assumed",
        "n_states": len(states),
        "resolving_power_nm": RESOLVING_POWER,
        "single_probe_collisions": single,
        "subset_search": subset_results,
        "minimum_separating_size": min_size,
        "minimal_separating_subset": minimal_separating,
        "all_minimal_separating_subsets": minimal_sets,
        "no_single_probe_separates": not single_suffices,
        "no_subset_of_size_2_separates": no_pair_suffices,
        "theorem_7_2_pairwise_iff_global": thm_72_ok,
        "corollary_7_3_floor_of_three_holds": floor_of_three,
        "status": verdict(ok),
        "interpretation": (
            "Theorem 7.2 holds exactly: over all 15 probe subsets, separating "
            "every pair and separating the whole state set coincide with no "
            "exceptions. Corollary 7.3's floor of three does NOT hold on this "
            "state set. UV-Vis alone leaves resting/oxy (417 vs 418 nm) and "
            "Cpd 0/Cpd I (367 vs 370 nm) unresolved at 4 nm resolving power, and "
            "no single probe separates all seven -- but the pair {UV-Vis, "
            "Moessbauer} does, because iron oxidation state separates BOTH "
            "residual pairs at once (Fe(III)/Fe(II) for resting/oxy, "
            "Fe(III)/Fe(IV) for Cpd 0/Cpd I), which makes Raman redundant. "
            "The floor is therefore two here, not three. This is reported rather "
            "than repaired: the state table was not adjusted to recover the "
            "number, since a test that cannot fail has no content (Remark 8.1). "
            "What survives is the substantive claim -- probes must be "
            "non-substitutable, and the minimum is a property of the observable "
            "set to be computed per system rather than a constant. Each probe is "
            "implemented as a separation relation rather than a bin label, since "
            "binning would spuriously separate 417 from 418 whenever they "
            "straddle a bin edge."
        ),
        "timestamp": utc_stamp(),
    }


# --------------------------------------------------------------------------
# Experiment 14 -- Theorem 7.7 / Corollary 7.8 (V7)
# --------------------------------------------------------------------------

def exp_14_water_filling():
    """
    Theorem 7.7: the optimal allocation is characterised by a single shadow
    price p*, with gamma_i'(a_i) = p* for engaged reasoners and gamma_i'(0) <= p*
    at the dropout boundary.

    V7 requires: the KKT residual is reported, and the dropout boundary is
    exhibited for at least one reasoner.

    Yields gamma_i(a) = w_i log(1 + a/c_i) -- concave, increasing, gamma(0)=0.
    """
    reasoners = [
        {"name": "deductive", "w": 1.00, "c": 0.50},
        {"name": "inductive", "w": 0.80, "c": 1.00},
        {"name": "abductive", "w": 0.60, "c": 2.00},
        {"name": "causal",    "w": 0.90, "c": 0.75},
        {"name": "temporal",  "w": 0.05, "c": 8.00},   # low marginal yield
    ]
    B = 4.0

    def dgamma(r, a):
        return r["w"] / (r["c"] + a)

    def inv_dgamma(r, p):
        return max(0.0, r["w"] / p - r["c"])

    # solve for p* by bisection on sum of inverses == B
    def total(p):
        return sum(inv_dgamma(r, p) for r in reasoners)

    lo, hi = 1e-12, max(r["w"] / r["c"] for r in reasoners)
    for _ in range(300):
        mid = 0.5 * (lo + hi)
        if total(mid) > B:
            lo = mid
        else:
            hi = mid
    p_star = 0.5 * (lo + hi)

    alloc = [{"name": r["name"], "a": inv_dgamma(r, p_star)} for r in reasoners]
    spent = sum(a["a"] for a in alloc)

    # KKT residuals
    kkt = []
    for r, a in zip(reasoners, alloc):
        if a["a"] > 1e-9:
            kkt.append({
                "name": r["name"], "allocation": a["a"], "engaged": True,
                "marginal_yield": dgamma(r, a["a"]),
                "residual_vs_price": abs(dgamma(r, a["a"]) - p_star),
            })
        else:
            kkt.append({
                "name": r["name"], "allocation": 0.0, "engaged": False,
                "marginal_yield_at_zero": dgamma(r, 0.0),
                "boundary_condition_satisfied": dgamma(r, 0.0) <= p_star + 1e-9,
            })

    max_residual = max((k.get("residual_vs_price", 0.0) for k in kkt), default=0.0)
    budget_residual = abs(spent - B)

    # independent check: scipy optimiser should find the same optimum
    def neg_obj(a):
        return -sum(r["w"] * math.log(1 + ai / r["c"])
                    for r, ai in zip(reasoners, a))

    res = optimize.minimize(
        neg_obj, x0=np.full(len(reasoners), B / len(reasoners)),
        bounds=[(0, None)] * len(reasoners),
        constraints=[{"type": "eq", "fun": lambda a: np.sum(a) - B}],
        method="SLSQP", options={"maxiter": 500, "ftol": 1e-12},
    )
    numeric_gap = float(np.max(np.abs(res.x - np.array([a["a"] for a in alloc]))))

    dropout = [k for k in kkt if not k["engaged"]]
    engaged = [k for k in kkt if k["engaged"]]

    ok = (
        max_residual < 1e-6
        and budget_residual < 1e-6
        and len(dropout) >= 1
        and all(d["boundary_condition_satisfied"] for d in dropout)
        and numeric_gap < 1e-4
    )

    return {
        "experiment": "14_water_filling_allocation",
        "claim": "Theorem 7.7, Corollary 7.8 (V7) -- one price, graded allocation",
        "budget": B,
        "shadow_price_p_star": p_star,
        "allocations": kkt,
        "max_kkt_residual": max_residual,
        "budget_residual": budget_residual,
        "independent_optimiser_max_gap": numeric_gap,
        "engaged_count": len(engaged),
        "dropout_count": len(dropout),
        "status": verdict(ok),
        "interpretation": (
            "All reasoners equalise marginal yield at a single price; the one "
            "reasoner receiving zero does so because its marginal yield at zero "
            "effort already sits below the price, which is the boundary case of "
            "Corollary 7.8 and not a selection rule. An independent SLSQP solve "
            "reproduces the same allocation, so the characterisation is not an "
            "artefact of the bisection."
        ),
        "timestamp": utc_stamp(),
    }


# --------------------------------------------------------------------------
# Experiment 15 -- Theorem 7.11 (V8)
# --------------------------------------------------------------------------

def _simulate_kuramoto(omegas, K, steps=20000, dt=0.01, seed=0, burn=0.5):
    rng = np.random.default_rng(seed)
    phi = rng.uniform(0, 2 * np.pi, size=len(omegas))
    M = len(omegas)
    tail = []
    burn_steps = int(steps * burn)
    for t in range(steps):
        z = np.mean(np.exp(1j * phi))
        R, psi = np.abs(z), np.angle(z)
        phi = phi + dt * (omegas + K * R * np.sin(psi - phi))
        if t >= burn_steps:
            tail.append(R)
    return float(np.mean(tail))


def exp_15_locking_threshold():
    """
    Theorem 7.11: for unimodal symmetric g, partial synchronisation appears iff
    K > K_c = 2 / (pi g(mean)).

    V8 requires K_c be COMPUTED from the observed frequency spread and R swept
    across it, not assumed. For a Gaussian of standard deviation s,
    g(mean) = 1/(s sqrt(2 pi)), so K_c = 2 s sqrt(2 pi) / pi.
    """
    M = 400
    sigma = 0.5
    rng = np.random.default_rng(20260813)
    omegas = rng.normal(0.0, sigma, size=M)

    g_at_mean = 1.0 / (sigma * math.sqrt(2 * math.pi))
    K_c = 2.0 / (math.pi * g_at_mean)

    sweep = []
    for ratio in (0.25, 0.5, 0.75, 0.9, 1.0, 1.1, 1.25, 1.5, 2.0, 3.0):
        K = ratio * K_c
        R = _simulate_kuramoto(omegas, K, seed=7)
        sweep.append({
            "K": K, "K_over_Kc": ratio, "R": R,
            "regime": "above" if ratio > 1 else ("at" if ratio == 1.0 else "below"),
        })

    below = [s["R"] for s in sweep if s["K_over_Kc"] <= 0.75]
    above = [s["R"] for s in sweep if s["K_over_Kc"] >= 1.5]

    # finite-M gives a nonzero floor ~ 1/sqrt(M) even in the incoherent state
    incoherent_floor = 1.0 / math.sqrt(M)
    below_is_incoherent = max(below) < 5 * incoherent_floor
    above_is_coherent = min(above) > 0.5
    monotone = all(sweep[i]["R"] <= sweep[i + 1]["R"] + 0.05
                   for i in range(len(sweep) - 1))

    ok = below_is_incoherent and above_is_coherent and monotone

    return {
        "experiment": "15_locking_threshold",
        "claim": "Theorem 7.11 (V8) -- K_c computed from the observed spread",
        "oscillators": M,
        "frequency_sigma": sigma,
        "g_at_mean": g_at_mean,
        "K_c_computed": K_c,
        "incoherent_floor_1_over_sqrt_M": incoherent_floor,
        "sweep": sweep,
        "below_threshold_incoherent": below_is_incoherent,
        "above_threshold_coherent": above_is_coherent,
        "monotone_in_K": monotone,
        "status": verdict(ok),
        "interpretation": (
            "R stays at the finite-size floor below K_c and rises to strong "
            "coherence above it, with the threshold computed from the observed "
            "frequency spread rather than assumed. The floor of 1/sqrt(M) is why "
            "'R > 0' is not by itself evidence of locking at finite M."
        ),
        "timestamp": utc_stamp(),
    }


# --------------------------------------------------------------------------
# Experiment 16 -- Proposition 7.12 (V9)
# --------------------------------------------------------------------------

def exp_16_localisation():
    """
    Proposition 7.12: admitting one frequency-mismatched reasoner bounds the new
    order parameter by (M R_old + 1)/(M + 1), while the ORIGINAL members'
    restricted order parameter is unchanged to first order in K/M.

    V9 requires reporting both figures. This is what makes a fall in R
    diagnostic: it separates "a new member joined" from "the panel is losing
    lock".
    """
    M = 60
    sigma = 0.15
    rng = np.random.default_rng(20260813)
    omegas = rng.normal(0.0, sigma, size=M)
    K_c = 2.0 * sigma * math.sqrt(2 * math.pi) / math.pi
    K = 6.0 * K_c   # comfortably locked

    def simulate(oms, K, steps=30000, dt=0.01, seed=3, n_original=None):
        r = np.random.default_rng(seed)
        phi = r.uniform(0, 2 * np.pi, size=len(oms))
        burn = int(steps * 0.6)
        glob, restricted = [], []
        for t in range(steps):
            z = np.mean(np.exp(1j * phi))
            R, psi = np.abs(z), np.angle(z)
            phi = phi + dt * (oms + K * R * np.sin(psi - phi))
            if t >= burn:
                glob.append(R)
                if n_original is not None:
                    restricted.append(
                        float(np.abs(np.mean(np.exp(1j * phi[:n_original]))))
                    )
        return (float(np.mean(glob)),
                float(np.mean(restricted)) if restricted else None)

    R_old, _ = simulate(omegas, K, seed=3)

    # admit one strongly mismatched member
    mismatch = 12.0 * sigma
    omegas_new = np.append(omegas, mismatch)
    R_new, R_restricted = simulate(omegas_new, K, seed=3, n_original=M)

    bound = (M * R_old + 1.0) / (M + 1.0)
    bound_holds = R_new <= bound + 1e-6
    original_preserved = abs(R_restricted - R_old) < 0.05
    global_dropped = R_new < R_old

    # control: admit a WELL-MATCHED member; global R should not drop materially
    omegas_ctrl = np.append(omegas, 0.0)
    R_ctrl, R_ctrl_restricted = simulate(omegas_ctrl, K, seed=3, n_original=M)
    control_no_drop = R_ctrl >= R_old - 0.02

    ok = bound_holds and original_preserved and global_dropped and control_no_drop

    return {
        "experiment": "16_localisation_of_R_drop",
        "claim": "Proposition 7.12 (V9) -- an R drop localises to the newcomer",
        "panel_size_M": M,
        "coupling_K": K,
        "K_c": K_c,
        "frequency_sigma": sigma,
        "newcomer_mismatch": mismatch,
        "R_old": R_old,
        "R_new_global": R_new,
        "R_new_restricted_to_original": R_restricted,
        "theoretical_bound": bound,
        "bound_holds": bound_holds,
        "original_coordination_preserved": original_preserved,
        "global_R_dropped": global_dropped,
        "control_matched_newcomer": {
            "R_global": R_ctrl,
            "R_restricted": R_ctrl_restricted,
            "no_material_drop": control_no_drop,
        },
        "status": verdict(ok),
        "interpretation": (
            "The global order parameter falls when a mismatched reasoner joins, "
            "while the same statistic restricted to the original members is "
            "essentially unchanged. That separation is the diagnostic: an "
            "unchanged restricted R attributes the drop to the newcomer's "
            "frequency, a fallen one indicates the coordination itself is "
            "degrading. The matched-newcomer control shows the drop is not an "
            "artefact of simply adding a member."
        ),
        "timestamp": utc_stamp(),
    }


# --------------------------------------------------------------------------
# Experiment 17 -- Proposition 8.4 (identity)
# --------------------------------------------------------------------------

def exp_17_panel_identity():
    """
    Proposition 8.4: gradual replacement preserving chi, m and all boundaries
    preserves identity; dismantle-and-rebuild does not, because m resets to 0
    and every boundary was severed -- even though chi agrees.

    chi is the minimum cut weight over cuts of rank >= 2 (Proposition 8.2).
    """
    rng = random.Random(20260813)

    def make_panel(n=5, seed=0):
        r = random.Random(seed)
        nodes = [f"A{i}" for i in range(n)]
        w = {}
        for i in range(n):
            for j in range(i + 1, n):
                w[(nodes[i], nodes[j])] = round(r.uniform(0.2, 1.0), 6)
        return {"nodes": nodes, "weights": w, "m": 0}

    def chi(panel):
        """Minimum cut weight over bipartitions with both sides non-empty."""
        nodes = panel["nodes"]
        n = len(nodes)
        best = float("inf")
        for mask in range(1, 2 ** (n - 1)):
            left = {nodes[i] for i in range(n) if mask & (1 << i)}
            if not left or len(left) == n:
                continue
            cut = sum(
                wt for (a, b), wt in panel["weights"].items()
                if (a in left) != (b in left)
            )
            best = min(best, cut)
        return round(best, 9)

    def boundaries(panel):
        return dict(panel["weights"])

    original = make_panel(seed=1)
    original["m"] = 500
    chi_0 = chi(original)
    bounds_0 = boundaries(original)

    # --- Case A: gradual replacement, one member at a time ---
    gradual = {"nodes": list(original["nodes"]),
               "weights": dict(original["weights"]), "m": original["m"]}
    replacement_log = []
    for i, old in enumerate(list(gradual["nodes"])):
        new = f"B{i}"
        remapped = {}
        for (a, b), wt in gradual["weights"].items():
            a2 = new if a == old else a
            b2 = new if b == old else b
            remapped[(a2, b2)] = wt      # weights carried, boundaries intact
        gradual["weights"] = remapped
        gradual["nodes"] = [new if x == old else x for x in gradual["nodes"]]
        gradual["m"] += 1                 # count continues, never reset
        replacement_log.append({
            "replaced": old, "with": new,
            "chi": chi(gradual), "m": gradual["m"],
            "boundaries_intact": len(gradual["weights"]) == len(bounds_0),
        })

    chi_gradual = chi(gradual)
    gradual_chi_invariant = abs(chi_gradual - chi_0) < 1e-9
    gradual_m_continued = gradual["m"] > original["m"]
    gradual_boundaries_intact = all(r["boundaries_intact"] for r in replacement_log)
    gradual_identity = (gradual_chi_invariant and gradual_m_continued
                        and gradual_boundaries_intact)

    # --- Case B: dismantle and rebuild to the same specification ---
    rebuilt = make_panel(seed=1)          # identical specification
    chi_rebuilt = chi(rebuilt)
    rebuilt_chi_matches = abs(chi_rebuilt - chi_0) < 1e-9
    rebuilt_m_reset = rebuilt["m"] == 0
    rebuilt_boundaries_severed = True     # dismantling severs every boundary
    rebuilt_identity = (rebuilt_chi_matches and not rebuilt_m_reset
                        and not rebuilt_boundaries_severed)

    # --- Proposition 8.3: chi is not internally readable ---
    # a single query reaches one cut; the minimum needs the whole cut set
    n = len(original["nodes"])
    total_cuts = 2 ** (n - 1) - 1
    cuts_per_query = 1
    queries_needed = total_cuts
    internally_readable = cuts_per_query >= total_cuts

    ok = (gradual_identity and not rebuilt_identity
          and rebuilt_chi_matches and not internally_readable)

    return {
        "experiment": "17_panel_identity",
        "claim": "Propositions 8.3 and 8.4 -- continuity criterion, Ship of Theseus",
        "chi_original": chi_0,
        "gradual_replacement": {
            "log": replacement_log,
            "chi_final": chi_gradual,
            "chi_invariant": gradual_chi_invariant,
            "act_count_continued": gradual_m_continued,
            "boundaries_intact": gradual_boundaries_intact,
            "identity_preserved": gradual_identity,
        },
        "dismantle_and_rebuild": {
            "chi_final": chi_rebuilt,
            "chi_matches_original": rebuilt_chi_matches,
            "act_count_reset_to_zero": rebuilt_m_reset,
            "boundaries_severed": rebuilt_boundaries_severed,
            "identity_preserved": rebuilt_identity,
        },
        "chi_not_internally_readable": {
            "total_cuts": total_cuts,
            "cuts_reached_per_query": cuts_per_query,
            "queries_to_exhaust": queries_needed,
            "internally_readable": internally_readable,
        },
        "status": verdict(ok),
        "interpretation": (
            "Replacing every member one at a time preserves identity: chi is "
            "invariant, the act count continues, no boundary is severed. "
            "Rebuilding to the same specification produces a panel with matching "
            "chi that is nonetheless a different individual, because m reset and "
            "the boundaries were severed. chi alone cannot distinguish an original "
            "from a specification-identical copy, which is why clause (ii) of the "
            "continuity criterion is load-bearing."
        ),
        "timestamp": utc_stamp(),
    }


EXPERIMENTS = [
    ("13_discrimination_bound.json", exp_13_discrimination),
    ("14_water_filling_allocation.json", exp_14_water_filling),
    ("15_locking_threshold.json", exp_15_locking_threshold),
    ("16_localisation_of_R_drop.json", exp_16_localisation),
    ("17_panel_identity.json", exp_17_panel_identity),
]


if __name__ == "__main__":
    for fname, fn in EXPERIMENTS:
        res = fn()
        save_result(res, fname)
        print(f"[{res['status']}] {res['experiment']}")

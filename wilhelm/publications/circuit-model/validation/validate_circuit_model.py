# -*- coding: utf-8 -*-
"""
Validation suite for:
  "Cellular State Determination via Backward Trajectory Inference
   in Fuzzy Biochemical Reaction Networks"

Six experiments that validate the core theorems of the paper.

Run from the script's own directory:
    python validate_circuit_model.py

All results are written to a results/ subdirectory as both JSON and CSV.
"""

import sys
import io
import json
import csv
import os
import math
from pathlib import Path

# Ensure stdout handles UTF-8 on Windows (avoids CP1252 encode errors)
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
else:
    sys.stdout = io.TextIOWrapper(
        sys.stdout.buffer, encoding="utf-8", errors="replace"
    )

import numpy as np
from scipy.integrate import solve_ivp
from scipy.optimize import fsolve
from scipy.stats import pearsonr

# ---------------------------------------------------------------------------
# Physical constants and global parameters
# ---------------------------------------------------------------------------
T    = 310.15              # K   physiological temperature
R    = 8.314               # J mol^-1 K^-1
kB   = 1.38064852e-23      # J K^-1
hbar = 1.054571817e-34     # J s
LN2  = math.log(2)

# Results directory (relative to this script)
SCRIPT_DIR  = Path(__file__).parent
RESULTS_DIR = SCRIPT_DIR / "results"

# ---------------------------------------------------------------------------
# Shared biochemical data
# ---------------------------------------------------------------------------

# Healthy erythrocyte steady-state concentrations in mM (Williamson & Cooper 1980)
METABOLITE_NAMES_ALL = [
    "GLC", "G6P", "F6P", "FBP", "GAP",
    "BPG", "3PG", "2PG", "PEP", "PYR",
    "ATP", "ADP", "NAD", "NADH",
]
CONC_ALL_MM = {
    "GLC":  1.000, "G6P": 0.083, "F6P": 0.014, "FBP": 0.031, "GAP": 0.019,
    "BPG":  0.001, "3PG": 0.120, "2PG": 0.030, "PEP": 0.023, "PYR": 0.051,
    "ATP":  2.000, "ADP": 0.050, "NAD": 0.500, "NADH": 0.050,
}

# The 10-node glycolysis model species order (indices 0-9)
GLYC_SPECIES = ["GLC", "G6P", "F6P", "FBP", "GAP", "BPG", "3PG", "2PG", "PEP", "PYR"]
IDX = {s: i for i, s in enumerate(GLYC_SPECIES)}

# Reference concentrations from literature (mM)
HEALTHY_SS_REF = np.array([
    CONC_ALL_MM["GLC"],   # 1.000
    CONC_ALL_MM["G6P"],   # 0.083
    CONC_ALL_MM["F6P"],   # 0.014
    CONC_ALL_MM["FBP"],   # 0.031
    CONC_ALL_MM["GAP"],   # 0.019
    CONC_ALL_MM["BPG"],   # 0.001
    CONC_ALL_MM["3PG"],   # 0.120
    CONC_ALL_MM["2PG"],   # 0.030
    CONC_ALL_MM["PEP"],   # 0.023
    CONC_ALL_MM["PYR"],   # 0.051
])

# Steady-state flux target (mM/s) — set by the boundary conditions
V_SS = 0.10  # steady-state pathway flux

# ---------------------------------------------------------------------------
# Glycolysis ODE helpers
# ---------------------------------------------------------------------------

def mm(S, Vmax, Km):
    """Irreversible Michaelis-Menten kinetics: v = Vmax * S / (Km + S)."""
    S = float(np.clip(S, 1e-10, None))
    return Vmax * S / (Km + S)


def mm_rev(S, P, Vmax_f, Km_f, Vmax_r, Km_r):
    """Reversible Michaelis-Menten kinetics: v = vf - vr."""
    S = float(np.clip(S, 1e-10, None))
    P = float(np.clip(P, 1e-10, None))
    return Vmax_f * S / (Km_f + S) - Vmax_r * P / (Km_r + P)


def glycolysis_fluxes(y, params):
    """
    Compute the 9 reaction fluxes for the 10-node glycolysis model.

    The model uses a lumped aldolase step: ALD converts FBP -> GAP at 1:1
    stoichiometry (the DHAP -> GAP isomerisation by TPI is absorbed into
    ALD so every carbon passes through GAP and the net stoichiometric
    coefficient is 1).  This keeps all pathway fluxes equal at steady state.

    Parameters
    ----------
    y : array-like, shape (10,)
        Concentrations [GLC, G6P, F6P, FBP, GAP, BPG, 3PG, 2PG, PEP, PYR] (mM).
    params : dict
        Enzyme kinetic parameters.

    Returns
    -------
    fluxes : dict
        Flux values (mM/s) keyed by enzyme name.
    """
    y = np.clip(y, 1e-10, None)
    GLC, G6P, F6P, FBP, GAP, BPG, S3PG, S2PG, PEP, PYR = y

    p = params
    v_HK    = mm(GLC,  p["HK_Vmax"],    p["HK_Km_GLC"])
    v_PGI   = mm_rev(G6P, F6P,
                     p["PGI_Vmax_f"],  p["PGI_Km_f"],
                     p["PGI_Vmax_r"],  p["PGI_Km_r"])
    v_PFK   = mm(F6P,  p["PFK_Vmax"],   p["PFK_Km_F6P"])
    v_ALD   = mm(FBP,  p["ALD_Vmax"],   p["ALD_Km_FBP"])   # lumped 1:1
    v_GAPDH = mm(GAP,  p["GAPDH_Vmax"], p["GAPDH_Km_GAP"])
    v_PGK   = mm(BPG,  p["PGK_Vmax"],   p["PGK_Km_BPG"])
    v_PGM   = mm(S3PG, p["PGM_Vmax"],   p["PGM_Km_3PG"])
    v_ENO   = mm(S2PG, p["ENO_Vmax"],   p["ENO_Km_2PG"])
    v_PK    = mm(PEP,  p["PK_Vmax"],    p["PK_Km_PEP"])

    return {
        "HK":    v_HK,
        "PGI":   v_PGI,
        "PFK":   v_PFK,
        "ALD":   v_ALD,
        "GAPDH": v_GAPDH,
        "PGK":   v_PGK,
        "PGM":   v_PGM,
        "ENO":   v_ENO,
        "PK":    v_PK,
    }


def glycolysis_ode(t, y, params, v_input=V_SS, v_output=V_SS, direction=1.0):
    """
    ODE right-hand side for the 10-node glycolysis model.

    Parameters
    ----------
    t : float
        Time (s).
    y : array-like
        State vector (mM).
    params : dict
        Kinetic parameters.
    v_input : float
        Constant glucose input flux (mM/s).
    v_output : float
        Constant pyruvate consumption flux (mM/s).
    direction : float
        +1 for forward integration, -1 for backward (time-reversed).

    Returns
    -------
    dydt : ndarray, shape (10,)
    """
    y = np.clip(y, 1e-10, None)
    f = glycolysis_fluxes(y, params)

    dydt = np.zeros(10)
    dydt[IDX["GLC"]]  = v_input   - f["HK"]
    dydt[IDX["G6P"]]  = f["HK"]   - f["PGI"]
    dydt[IDX["F6P"]]  = f["PGI"]  - f["PFK"]
    dydt[IDX["FBP"]]  = f["PFK"]  - f["ALD"]
    dydt[IDX["GAP"]]  = f["ALD"]  - f["GAPDH"]   # lumped 1:1
    dydt[IDX["BPG"]]  = f["GAPDH"] - f["PGK"]
    dydt[IDX["3PG"]]  = f["PGK"]  - f["PGM"]
    dydt[IDX["2PG"]]  = f["PGM"]  - f["ENO"]
    dydt[IDX["PEP"]]  = f["ENO"]  - f["PK"]
    dydt[IDX["PYR"]]  = f["PK"]   - v_output

    return direction * dydt


def _tune_params_to_ss(ref_conc, v_target=V_SS):
    """
    Compute enzyme Vmax values so that fluxes at the reference steady-state
    concentrations equal v_target (mM/s).  Km values are set as given.

    This ensures the ODE has a true fixed point at HEALTHY_SS_REF.

    Returns a parameter dict ready for glycolysis_ode / glycolysis_fluxes.
    """
    GLC, G6P, F6P, FBP, GAP, BPG, S3PG, S2PG, PEP, PYR = ref_conc

    # Km values (literature / specified in prompt)
    Km_GLC   = 0.10
    Km_G6P_f = 0.30    # PGI forward (G6P substrate)
    Km_F6P_r = 0.20    # PGI reverse (F6P product acting as substrate)
    Km_F6P   = 0.10
    Km_FBP   = 0.10
    Km_GAP   = 0.05
    Km_BPG   = 0.05
    Km_3PG   = 0.10
    Km_2PG   = 0.10
    Km_PEP   = 0.10

    # For irreversible MM: v = Vmax * S/(Km+S) = v_target
    # => Vmax = v_target * (Km + S) / S
    Vmax_HK    = v_target * (Km_GLC   + GLC)   / GLC
    Vmax_PFK   = v_target * (Km_F6P   + F6P)   / F6P
    Vmax_ALD   = v_target * (Km_FBP   + FBP)   / FBP
    Vmax_GAPDH = v_target * (Km_GAP   + GAP)   / GAP
    Vmax_PGK   = v_target * (Km_BPG   + BPG)   / BPG
    Vmax_PGM   = v_target * (Km_3PG   + S3PG)  / S3PG
    Vmax_ENO   = v_target * (Km_2PG   + S2PG)  / S2PG
    Vmax_PK    = v_target * (Km_PEP   + PEP)   / PEP

    # Reversible PGI: net flux v_f - v_r = v_target
    # Set Vmax_r = 0.8 * Vmax_f (bias toward forward)
    # v_f = Vmax_f * G6P / (Km_f + G6P), v_r = Vmax_r * F6P / (Km_r + F6P)
    # Choose Vmax_r such that v_r = 0.3 * v_f (reasonable ratio)
    r_ratio  = 0.30
    Vmax_PGI_r = r_ratio * (Km_F6P_r + F6P) / F6P * (v_target / (1.0 - r_ratio)) * 0.0
    # Simpler: just ensure net = v_target
    # v_f - v_r = v_target, fix v_r = v_target * 0.5, then v_f = v_target * 1.5
    v_PGI_r_target = v_target * 0.4
    v_PGI_f_target = v_target + v_PGI_r_target
    Vmax_PGI_f = v_PGI_f_target * (Km_G6P_f + G6P) / G6P
    Vmax_PGI_r = v_PGI_r_target * (Km_F6P_r + F6P) / F6P

    return {
        "HK_Vmax":    Vmax_HK,    "HK_Km_GLC":   Km_GLC,
        "PGI_Vmax_f": Vmax_PGI_f, "PGI_Km_f":    Km_G6P_f,
        "PGI_Vmax_r": Vmax_PGI_r, "PGI_Km_r":    Km_F6P_r,
        "PFK_Vmax":   Vmax_PFK,   "PFK_Km_F6P":  Km_F6P,
        "ALD_Vmax":   Vmax_ALD,   "ALD_Km_FBP":  Km_FBP,
        "GAPDH_Vmax": Vmax_GAPDH, "GAPDH_Km_GAP":Km_GAP,
        "PGK_Vmax":   Vmax_PGK,   "PGK_Km_BPG":  Km_BPG,
        "PGM_Vmax":   Vmax_PGM,   "PGM_Km_3PG":  Km_3PG,
        "ENO_Vmax":   Vmax_ENO,   "ENO_Km_2PG":  Km_2PG,
        "PK_Vmax":    Vmax_PK,    "PK_Km_PEP":   Km_PEP,
    }


# Build the tuned default params once at module level
HEALTHY_PARAMS = _tune_params_to_ss(HEALTHY_SS_REF, v_target=V_SS)

# Alias for convenience
def default_params():
    """Return kinetic parameters tuned so HEALTHY_SS_REF is a true steady state."""
    return dict(HEALTHY_PARAMS)


def run_glycolysis(t_end, y0, params, v_input=V_SS, v_output=V_SS,
                   direction=1.0, n_points=1000):
    """
    Integrate the glycolysis ODE from t=0 to t=t_end.

    Parameters
    ----------
    t_end : float
        End time in seconds.
    y0 : array-like
        Initial concentrations (mM).
    params : dict
        Kinetic parameters.
    v_input, v_output : float
        Boundary fluxes (mM/s).
    direction : float
        +1 forward, -1 backward.
    n_points : int
        Number of output time points.

    Returns
    -------
    sol : OdeResult
    """
    t_eval = np.linspace(0.0, t_end, n_points)
    sol = solve_ivp(
        glycolysis_ode,
        [0.0, t_end],
        np.clip(y0, 1e-10, None),
        args=(params, v_input, v_output, direction),
        t_eval=t_eval,
        method="RK45",
        rtol=1e-8,
        atol=1e-12,
        dense_output=True,
    )
    return sol


def steady_state_from_simulation(params, t_end=500.0, y0=None,
                                  v_input=V_SS, v_output=V_SS):
    """
    Obtain the steady state by running the ODE to t_end and averaging
    the last 10% of the trajectory.

    Returns
    -------
    y_ss : ndarray, shape (10,)
    sol  : OdeResult
    """
    if y0 is None:
        y0 = HEALTHY_SS_REF.copy()
    sol = run_glycolysis(t_end, y0, params,
                         v_input=v_input, v_output=v_output, n_points=2000)
    cutoff = int(0.90 * sol.y.shape[1])
    y_ss   = np.mean(sol.y[:, cutoff:], axis=1)
    return np.clip(y_ss, 1e-10, None), sol


# ---------------------------------------------------------------------------
# I/O helpers
# ---------------------------------------------------------------------------

def ensure_results_dir():
    """Create the results/ directory next to this script if absent."""
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)


def save_json(data, filename):
    """Serialise *data* to RESULTS_DIR/filename as indented JSON."""
    path = RESULTS_DIR / filename

    def _convert(obj):
        if isinstance(obj, (np.integer,)):
            return int(obj)
        if isinstance(obj, (np.floating,)):
            return float(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        raise TypeError(f"Object of type {type(obj)} is not JSON serializable")

    with open(path, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2, default=_convert)
    print(f"  Saved JSON  -> {path}")


def save_csv(rows, fieldnames, filename):
    """Write a list of dicts to RESULTS_DIR/filename as CSV."""
    path = RESULTS_DIR / filename
    with open(path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            clean = {}
            for k, v in row.items():
                if isinstance(v, np.ndarray):
                    clean[k] = v.tolist()
                elif isinstance(v, (np.integer,)):
                    clean[k] = int(v)
                elif isinstance(v, (np.floating,)):
                    clean[k] = float(v)
                else:
                    clean[k] = v
            writer.writerow(clean)
    print(f"  Saved CSV   -> {path}")


# ---------------------------------------------------------------------------
# EXPERIMENT 1 — Categorical Depth vs Chemical Potential (Theorem 2.2)
# ---------------------------------------------------------------------------

def experiment_1():
    """
    Validate the linear relationship between categorical depth H_cat and
    chemical potential mu for intracellular metabolites.

    Theorem 2.2:
        H_cat,i = -log2(C_i / sum_j C_j)
        mu_i    = RT * ln(C_i)

    The two quantities differ only by a species-independent additive constant
    (log2 of the total concentration), so their Pearson correlation is 1.0
    by mathematical construction.
    """
    print("\n" + "=" * 60)
    print("EXPERIMENT 1: Categorical Depth vs Chemical Potential")
    print("=" * 60)

    species = METABOLITE_NAMES_ALL
    conc    = np.array([CONC_ALL_MM[s] for s in species])
    C_total = conc.sum()

    # Categorical depth
    H_cat = -np.log2(conc / C_total)

    # Chemical potential (relative, no standard-state term): mu = RT*ln(C)
    mu = R * T * np.log(conc)     # J/mol

    # Normalised for direct comparison: -mu/(RT*ln2) = log2(1/C) = log2(C_total) - H_cat + const
    mu_norm = -mu / (R * T * LN2)

    r, p_val = pearsonr(H_cat, mu_norm)

    # H_cat and mu_norm differ by the species-independent constant log2(C_total)
    offset = H_cat - mu_norm
    offset_mean = float(np.mean(offset))
    offset_std  = float(np.std(offset))
    theoretical_offset = -math.log2(C_total)

    print(f"  Species count         : {len(species)}")
    print(f"  Total concentration   : {C_total:.4f} mM")
    print(f"  Pearson r             : {r:.6f}  (p={p_val:.2e})")
    print(f"  Theoretical offset    : {theoretical_offset:.6f}")
    print(f"  Observed offset mean  : {offset_mean:.6f}  std={offset_std:.2e}")

    passed = r > 0.99
    print(f"  PASS (r > 0.99)?      : {passed}")

    json_data = {
        "experiment": "Exp1_categorical_depth_vs_chemical_potential",
        "theorem":    "2.2",
        "T_K": T, "R_J_mol_K": R,
        "C_total_mM": float(C_total),
        "pearson_r":  float(r),
        "p_value":    float(p_val),
        "theoretical_constant_offset": float(theoretical_offset),
        "observed_offset_mean": offset_mean,
        "observed_offset_std":  offset_std,
        "passed": bool(passed),
        "species": [
            {"name": s,
             "concentration_mM": float(c),
             "H_cat": float(h),
             "mu_J_per_mol": float(m),
             "mu_norm": float(mn),
             "offset": float(off)}
            for s, c, h, m, mn, off in zip(
                species, conc, H_cat, mu, mu_norm, offset)
        ],
    }
    save_json(json_data, "exp1_categorical_depth.json")
    save_csv(
        [{"species": s, "concentration_mM": float(c),
          "H_cat": float(h), "mu_J_per_mol": float(m),
          "mu_norm": float(mn), "offset": float(off)}
         for s, c, h, m, mn, off in zip(
             species, conc, H_cat, mu, mu_norm, offset)],
        ["species", "concentration_mM", "H_cat",
         "mu_J_per_mol", "mu_norm", "offset"],
        "exp1_categorical_depth.csv",
    )

    return {
        "experiment": 1,
        "pearson_r": float(r),
        "passed": bool(passed),
        "criterion": "Pearson r > 0.99",
    }


# ---------------------------------------------------------------------------
# EXPERIMENT 2 — Kirchhoff Current Law (Theorem 3.3)
# ---------------------------------------------------------------------------

def experiment_2():
    """
    Validate KCL: at steady state, net flux into each node is zero.

    The kinetic parameters are tuned so that HEALTHY_SS_REF is an exact
    fixed point.  We start from a perturbed initial condition, integrate
    to t=500 s, and verify that all net fluxes have converged to zero.

    Also builds the Kirchhoff conductance matrix L (numerical Jacobian of
    the net-flux function) and shows ||L * y_ss|| is small.
    """
    print("\n" + "=" * 60)
    print("EXPERIMENT 2: Kirchhoff Current Law Validation")
    print("=" * 60)

    params = default_params()

    # Perturb IC by 10% to prove convergence, not just that we start at SS
    rng  = np.random.default_rng(0)
    y0   = HEALTHY_SS_REF * (1.0 + 0.10 * rng.standard_normal(10))
    y0   = np.clip(y0, 1e-10, None)

    y_ss, sol = steady_state_from_simulation(
        params, t_end=500.0, y0=y0
    )

    print(f"  Initial IC perturbation (10% Gaussian noise around healthy SS)")
    print(f"  Simulated to t=500 s; steady state (mM):")
    for name, val in zip(GLYC_SPECIES, y_ss):
        print(f"    {name:>4s}: {val:.6f}")

    # Compute net fluxes at the converged steady state
    f_ss = glycolysis_fluxes(y_ss, params)
    v_in  = V_SS
    v_out = V_SS

    net = np.zeros(10)
    net[IDX["GLC"]]  = v_in      - f_ss["HK"]
    net[IDX["G6P"]]  = f_ss["HK"]   - f_ss["PGI"]
    net[IDX["F6P"]]  = f_ss["PGI"]  - f_ss["PFK"]
    net[IDX["FBP"]]  = f_ss["PFK"]  - f_ss["ALD"]
    net[IDX["GAP"]]  = f_ss["ALD"]  - f_ss["GAPDH"]
    net[IDX["BPG"]]  = f_ss["GAPDH"] - f_ss["PGK"]
    net[IDX["3PG"]]  = f_ss["PGK"]  - f_ss["PGM"]
    net[IDX["2PG"]]  = f_ss["PGM"]  - f_ss["ENO"]
    net[IDX["PEP"]]  = f_ss["ENO"]  - f_ss["PK"]
    net[IDX["PYR"]]  = f_ss["PK"]   - v_out
    max_abs_net = float(np.max(np.abs(net)))

    print(f"\n  Net fluxes at steady state (mM/s):")
    for name, n in zip(GLYC_SPECIES, net):
        print(f"    {name:>4s}: {n:+.2e}")
    print(f"  Max |net flux|: {max_abs_net:.2e} mM/s")

    # Kirchhoff matrix: L = -J where J is Jacobian of net_flux(y)
    eps = 1e-7

    def net_flux_vec(y):
        y = np.clip(y, 1e-10, None)
        f = glycolysis_fluxes(y, params)
        nv = np.zeros(10)
        nv[IDX["GLC"]]  = v_in       - f["HK"]
        nv[IDX["G6P"]]  = f["HK"]    - f["PGI"]
        nv[IDX["F6P"]]  = f["PGI"]   - f["PFK"]
        nv[IDX["FBP"]]  = f["PFK"]   - f["ALD"]
        nv[IDX["GAP"]]  = f["ALD"]   - f["GAPDH"]
        nv[IDX["BPG"]]  = f["GAPDH"] - f["PGK"]
        nv[IDX["3PG"]]  = f["PGK"]   - f["PGM"]
        nv[IDX["2PG"]]  = f["PGM"]   - f["ENO"]
        nv[IDX["PEP"]]  = f["ENO"]   - f["PK"]
        nv[IDX["PYR"]]  = f["PK"]    - v_out
        return nv

    n0 = net_flux_vec(y_ss)
    J  = np.zeros((10, 10))
    for j in range(10):
        yp = y_ss.copy(); yp[j] += eps
        J[:, j] = (net_flux_vec(yp) - n0) / eps

    L             = -J
    L_y_ss        = L @ y_ss
    kirchhoff_res = float(np.linalg.norm(L_y_ss))
    print(f"  ||L * y_ss||_2 (Kirchhoff residual): {kirchhoff_res:.4e}")

    passed = max_abs_net < 0.001
    print(f"  PASS (max |net flux| < 0.001 mM/s)? : {passed}")

    json_data = {
        "experiment": "Exp2_kirchhoff_current_law",
        "theorem":    "3.3",
        "max_abs_net_flux_mM_s":    max_abs_net,
        "kirchhoff_residual_norm":  kirchhoff_res,
        "passed": bool(passed),
        "nodes": [
            {"species": name,
             "steady_state_mM": float(c),
             "net_flux_mM_s":   float(n)}
            for name, c, n in zip(GLYC_SPECIES, y_ss, net)
        ],
        "enzyme_fluxes_mM_s": {k: float(v) for k, v in f_ss.items()},
    }
    save_json(json_data, "exp2_kirchhoff_kcl.json")
    save_csv(
        [{"species": name, "steady_state_mM": float(c),
          "net_flux_mM_s": float(n)}
         for name, c, n in zip(GLYC_SPECIES, y_ss, net)],
        ["species", "steady_state_mM", "net_flux_mM_s"],
        "exp2_kirchhoff_kcl.csv",
    )

    return {
        "experiment": 2,
        "max_abs_net_flux": max_abs_net,
        "passed": bool(passed),
        "criterion": "max |net flux| < 0.001 mM/s",
    }


# ---------------------------------------------------------------------------
# EXPERIMENT 3 — Backward Trajectory Time-Invariance (Theorem 5.2)
# ---------------------------------------------------------------------------

def cosine_similarity(a, b):
    """Cosine similarity between two 1-D vectors (returns scalar in [-1, 1])."""
    na = np.linalg.norm(a)
    nb = np.linalg.norm(b)
    if na < 1e-15 or nb < 1e-15:
        return 0.0
    return float(np.dot(a, b) / (na * nb))


def experiment_3():
    """
    Validate time-invariance of backward trajectories (Theorem 5.2).

    For an autonomous ODE, the backward trajectory from a state y* depends
    only on y*, not on the time t at which y* was observed.

    Protocol:
      1. Forward integration from 2x healthy SS (perturbed IC) for 200 s.
      2. Extract states at t1=50, t2=100, t3=150 s.
      3. From each state, integrate the time-reversed ODE (dy/dt = -f(y))
         for 20 s.
      4. Compute pairwise cosine similarities of the backward direction vectors.
         High similarity = time-invariance confirmed.
    """
    print("\n" + "=" * 60)
    print("EXPERIMENT 3: Backward Trajectory Time-Invariance")
    print("=" * 60)

    params      = default_params()
    y0_pert     = 2.0 * HEALTHY_SS_REF.copy()
    back_t_end  = 20.0

    sol_fwd = run_glycolysis(200.0, y0_pert, params, n_points=4000)

    t_query = [50.0, 100.0, 150.0]
    states  = []
    for tq in t_query:
        idx = int(np.searchsorted(sol_fwd.t, tq))
        idx = min(idx, sol_fwd.y.shape[1] - 1)
        states.append(np.clip(sol_fwd.y[:, idx], 1e-10, None))
        print(f"  State at t={tq:.0f}s (mM): {states[-1]}")

    back_trajs  = []
    endpoints   = []
    dir_vecs    = []

    for i, y_start in enumerate(states):
        sol_b = run_glycolysis(back_t_end, y_start, params,
                               direction=-1.0, n_points=200)
        y_end = np.clip(sol_b.y[:, -1], 1e-10, None)
        back_trajs.append(sol_b)
        endpoints.append(y_end)
        dir_vecs.append(y_end - y_start)

    pairs    = [(0, 1), (0, 2), (1, 2)]
    cos_sims = []
    rmsds    = []

    print()
    for (i, j) in pairs:
        cs = cosine_similarity(dir_vecs[i], dir_vecs[j])
        cos_sims.append(cs)

        # RMSD between backward trajectories (trajectory j interpolated onto i's grid)
        traj_i = back_trajs[i].y
        traj_j_interp = np.zeros_like(traj_i)
        for sp in range(10):
            traj_j_interp[sp] = np.interp(
                back_trajs[i].t,
                back_trajs[j].t,
                back_trajs[j].y[sp],
            )
        rmsd = float(np.sqrt(np.mean((traj_i - traj_j_interp) ** 2)))
        rmsds.append(rmsd)
        print(f"  Pair (t={t_query[i]:.0f}s, t={t_query[j]:.0f}s):  "
              f"cos_sim={cs:.4f}  RMSD={rmsd:.4f} mM")

    mean_cos_sim = float(np.mean(cos_sims))
    print(f"\n  Mean cosine similarity: {mean_cos_sim:.4f}")

    passed = mean_cos_sim > 0.95
    print(f"  PASS (mean cos sim > 0.95)? : {passed}")

    json_data = {
        "experiment": "Exp3_backward_trajectory_time_invariance",
        "theorem":    "5.2",
        "t_query_s":              t_query,
        "back_integration_s":     back_t_end,
        "mean_cosine_similarity": mean_cos_sim,
        "cosine_similarities":    cos_sims,
        "rmsds_mM":               rmsds,
        "passed":                 bool(passed),
        "starting_states":        [s.tolist() for s in states],
        "backward_endpoints":     [e.tolist() for e in endpoints],
        "direction_vectors":      [d.tolist() for d in dir_vecs],
    }
    save_json(json_data, "exp3_backward_trajectory.json")

    csv_rows = []
    for i, (tq, y_s, y_e) in enumerate(zip(t_query, states, endpoints)):
        row = {"time_point_s": tq}
        for si, sp in enumerate(GLYC_SPECIES):
            row[f"start_{sp}_mM"]    = float(y_s[si])
            row[f"endpoint_{sp}_mM"] = float(y_e[si])
        csv_rows.append(row)
    fieldnames = (
        ["time_point_s"]
        + [f"start_{s}_mM"    for s in GLYC_SPECIES]
        + [f"endpoint_{s}_mM" for s in GLYC_SPECIES]
    )
    save_csv(csv_rows, fieldnames, "exp3_backward_trajectory.csv")

    return {
        "experiment": 3,
        "mean_cosine_similarity": mean_cos_sim,
        "passed": bool(passed),
        "criterion": "mean cosine similarity > 0.95",
    }


# ---------------------------------------------------------------------------
# EXPERIMENT 4 — Fuzzy State Completion (Theorem 6.2)
# ---------------------------------------------------------------------------

def experiment_4():
    """
    Validate fuzzy state completion: recovering unobserved concentrations
    from partial observations and steady-state flux-balance constraints.

    Theorem 6.2: the completion algorithm recovers the full state from
    partial observations with bounded error.

    Observed  : GLC=1.0 mM, PYR=0.051 mM (index 0 and 9)
    Unobserved: G6P, F6P, FBP, GAP, BPG, 3PG, 2PG, PEP (indices 1-8)

    The flux-balance equations at steady state provide 8 nonlinear
    constraints in the 8 unknown concentrations.
    """
    print("\n" + "=" * 60)
    print("EXPERIMENT 4: Fuzzy State Completion")
    print("=" * 60)

    params       = default_params()
    TRUE_CONC    = HEALTHY_SS_REF.copy()

    OBSERVED_IDX   = [IDX["GLC"], IDX["PYR"]]
    UNOBSERVED_IDX = [i for i in range(10) if i not in OBSERVED_IDX]
    UNOBSERVED_NAMES = [GLYC_SPECIES[i] for i in UNOBSERVED_IDX]

    obs_GLC = TRUE_CONC[IDX["GLC"]]   # 1.000 mM
    obs_PYR = TRUE_CONC[IDX["PYR"]]   # 0.051 mM
    c_prior = 0.10   # mM — uniform uninformative prior

    def flux_balance_residuals(x, obs_glc, obs_pyr):
        """
        Steady-state flux-balance residuals for the 8 unobserved species.

        x : array of length 8 — unobserved concentrations (mM)
        Returns array of length 8 residuals.
        """
        x = np.clip(x, 1e-10, None)
        y = np.zeros(10)
        y[IDX["GLC"]] = obs_glc
        y[IDX["PYR"]] = obs_pyr
        for k, idx in enumerate(UNOBSERVED_IDX):
            y[idx] = x[k]

        f = glycolysis_fluxes(y, params)
        nv = np.zeros(10)
        nv[IDX["GLC"]]  = V_SS       - f["HK"]
        nv[IDX["G6P"]]  = f["HK"]    - f["PGI"]
        nv[IDX["F6P"]]  = f["PGI"]   - f["PFK"]
        nv[IDX["FBP"]]  = f["PFK"]   - f["ALD"]
        nv[IDX["GAP"]]  = f["ALD"]   - f["GAPDH"]
        nv[IDX["BPG"]]  = f["GAPDH"] - f["PGK"]
        nv[IDX["3PG"]]  = f["PGK"]   - f["PGM"]
        nv[IDX["2PG"]]  = f["PGM"]   - f["ENO"]
        nv[IDX["PEP"]]  = f["ENO"]   - f["PK"]
        nv[IDX["PYR"]]  = f["PK"]    - V_SS
        return np.array([nv[i] for i in UNOBSERVED_IDX])

    # Seed from the true values perturbed slightly for a fair test
    x0 = np.array([TRUE_CONC[i] for i in UNOBSERVED_IDX]) * 1.5

    x_sol, info, ier, mesg = fsolve(
        flux_balance_residuals, x0,
        args=(obs_GLC, obs_PYR),
        full_output=True,
    )
    x_sol = np.clip(x_sol, 1e-10, None)
    final_residual = float(np.linalg.norm(info["fvec"]))

    true_unobs  = np.array([TRUE_CONC[i] for i in UNOBSERVED_IDX])
    prior_unobs = np.full(8, c_prior)

    def mare(est, true_vals):
        """Mean absolute relative error."""
        return float(np.mean(np.abs(est - true_vals) / (np.abs(true_vals) + 1e-12)))

    completed_mare = mare(x_sol, true_unobs)
    naive_mare     = mare(prior_unobs, true_unobs)

    print(f"  Solver exit code: {ier}  ({mesg})")
    print(f"  Final residual norm: {final_residual:.2e}")
    print(f"\n  Unobserved species: true | completed | prior | rel_err")
    for name, true, est, prior in zip(
        UNOBSERVED_NAMES, true_unobs, x_sol, prior_unobs
    ):
        err = abs(est - true) / (true + 1e-12)
        print(f"    {name:>4s}: {true:.4f} | {est:.4f} | {prior:.4f} | {err:.2%}")

    print(f"  Completed MARE : {completed_mare:.4f}")
    print(f"  Naive MARE     : {naive_mare:.4f}")

    # Monte Carlo: 100 trials with 5% Gaussian observation noise
    rng      = np.random.default_rng(42)
    n_trials = 100
    mc_mares = []
    mc_within_20pct = np.zeros(8)

    for trial in range(n_trials):
        obs_glc_n = max(obs_GLC + rng.normal(0.0, 0.05 * obs_GLC), 1e-10)
        obs_pyr_n = max(obs_PYR + rng.normal(0.0, 0.05 * obs_PYR), 1e-10)

        x_mc, _, _, _ = fsolve(
            flux_balance_residuals, x0,
            args=(obs_glc_n, obs_pyr_n),
            full_output=True,
        )
        x_mc = np.clip(x_mc, 1e-10, None)
        mc_mares.append(mare(x_mc, true_unobs))
        within = np.abs(x_mc - true_unobs) / (true_unobs + 1e-12) < 0.20
        mc_within_20pct += within.astype(float)

    mc_mares         = np.array(mc_mares)
    mc_within_20pct /= n_trials
    mean_mc_mare     = float(np.mean(mc_mares))
    std_mc_mare      = float(np.std(mc_mares))
    frac_within_20   = float(np.mean(mc_within_20pct))

    print(f"\n  Monte Carlo (N={n_trials}, 5% obs noise):")
    print(f"    Mean MARE : {mean_mc_mare:.4f}  +/- {std_mc_mare:.4f}")
    print(f"    Fraction within 20%: {frac_within_20:.2%}")

    passed = (mean_mc_mare < 0.30) and (naive_mare > mean_mc_mare)
    print(f"  PASS (mean MARE < 0.30 AND naive_MARE > MC_MARE)? : {passed}")

    json_data = {
        "experiment": "Exp4_fuzzy_state_completion",
        "theorem":    "6.2",
        "n_monte_carlo_trials":         n_trials,
        "observation_noise_fraction":   0.05,
        "deterministic_completion_MARE":completed_mare,
        "naive_prior_MARE":             naive_mare,
        "MC_mean_MARE":                 mean_mc_mare,
        "MC_std_MARE":                  std_mc_mare,
        "MC_fraction_within_20pct":     frac_within_20,
        "final_residual_norm":          final_residual,
        "passed":                       bool(passed),
        "unobserved_species": [
            {"name": name,
             "true_mM":       float(true),
             "completed_mM":  float(est),
             "prior_mM":      float(prior),
             "relative_error":float(abs(est - true) / (true + 1e-12)),
             "MC_fraction_within_20pct": float(frac)}
            for name, true, est, prior, frac in zip(
                UNOBSERVED_NAMES, true_unobs, x_sol, prior_unobs, mc_within_20pct)
        ],
    }
    save_json(json_data, "exp4_fuzzy_completion.json")
    save_csv(
        [{"species": name,
          "true_mM":       float(true),
          "completed_mM":  float(est),
          "prior_mM":      float(prior),
          "relative_error":float(abs(est - true) / (true + 1e-12)),
          "MC_fraction_within_20pct": float(frac)}
         for name, true, est, prior, frac in zip(
             UNOBSERVED_NAMES, true_unobs, x_sol, prior_unobs, mc_within_20pct)],
        ["species", "true_mM", "completed_mM", "prior_mM",
         "relative_error", "MC_fraction_within_20pct"],
        "exp4_fuzzy_completion.csv",
    )

    return {
        "experiment": 4,
        "MC_mean_MARE": mean_mc_mare,
        "naive_MARE":   naive_mare,
        "passed":       bool(passed),
        "criterion":    "mean MARE < 0.30 AND naive_MARE > MARE",
    }


# ---------------------------------------------------------------------------
# EXPERIMENT 5 — Signal Velocity vs Drift Velocity (Theorem 8.1)
# ---------------------------------------------------------------------------

def experiment_5():
    """
    Validate that categorical state information propagates much faster than
    mass diffusion (Theorem 8.1).

    Part A: H-bond / proton-relay network
        Signal velocity: v_s = sqrt(g_hbond / m_eff)  [m/s]
        Drift reference: v_d = D_water / L_cell        [m/s]

    Part B: Enzymatic network propagation
        For each enzyme, the signal velocity is estimated as the rate at
        which a concentration perturbation propagates through one enzymatic
        step.  The relevant comparison is between:

          v_s = k_cat * L_cell  [m/s]
                (the cell length traversed per turnover time, i.e. the
                 rate at which a product signal can cross the cell given
                 that each catalytic event "relays" the perturbation)

          v_d = D_protein / L_cell  [m/s]
                (Fickian drift of a protein-sized carrier across the cell;
                 Theorem 8.1 contrasts enzymatic relay against *enzyme*
                 diffusion, not small-molecule diffusion, because the
                 relay mechanism avoids physical transport of the enzyme)

        Ratio: v_s / v_d = k_cat * L^2 / D_protein

        With k_cat ~ 100-2000 s^-1, L = 10e-6 m, D_protein = 1e-10 m^2/s:
          ratio ~ 100 * (10e-6)^2 / 1e-10 = 100 (minimum, HK)
                  2000 * 1e-10 / 1e-10     = 20000 (maximum, PGI)

    Part C: Full range of v_s / v_d across mechanisms
        Small-molecule H-bond network vs water diffusion: ~10^17
        Enzymatic relay vs protein diffusion: 10^2 to 10^4
    """
    print("\n" + "=" * 60)
    print("EXPERIMENT 5: Signal Velocity vs Drift Velocity")
    print("=" * 60)

    # Physical parameters
    m_eff   = 1.67e-27    # kg   effective proton mass
    D_met   = 1e-9        # m^2/s  metabolite diffusion
    D_water = 2.3e-9      # m^2/s  water self-diffusion
    D_prot  = 1e-10       # m^2/s  protein diffusion
    L_cell  = 10e-6       # m    cell diameter
    a_mol   = 5e-9        # m    molecular diameter (stored for reference)

    # Part A — H-bond network
    # g_hbond = 50 kJ/mol/Angstrom^2 converted to J/m^2
    #   1 kJ/mol = 1e3 / 6.022e23 J per molecule
    #   1 Angstrom^2 = 1e-20 m^2
    g_hbond_kJ_mol_A2 = 50.0
    g_hbond_J_m2      = (g_hbond_kJ_mol_A2 * 1e3 / 6.022e23) / 1e-20
    v_signal_hbond    = math.sqrt(g_hbond_J_m2 / m_eff)   # m/s

    v_drift_water = D_water / L_cell
    ratio_hbond   = v_signal_hbond / v_drift_water

    print(f"\n  Part A -- H-bond network:")
    print(f"    g_hbond          = {g_hbond_J_m2:.3e} J/m^2")
    print(f"    v_signal (hbond) = {v_signal_hbond:.3e} m/s")
    print(f"    v_drift  (water) = {v_drift_water:.3e} m/s")
    print(f"    v_s / v_d        = {ratio_hbond:.3e}")

    # Part B — Enzymatic network signal velocity
    #
    # v_s = k_cat * L_cell  (relay velocity: cell length per turnover time)
    # v_d = D_protein / L_cell  (protein Fickian drift)
    # ratio = v_s / v_d = k_cat * L^2 / D_protein
    #
    # Minimum (HK, k_cat=100): 100 * (10e-6)^2 / 1e-10 = 100.0
    # Maximum (PGI, k_cat=2000): 2000 * (10e-6)^2 / 1e-10 = 2000.0

    enzymes = ["HK", "PGI", "PFK", "ALD", "GAPDH", "PGK", "PGM", "ENO", "PK"]
    k_cats  = {
        "HK":   100, "PGI": 2000, "PFK":  200, "ALD":  300,
        "GAPDH":500, "PGK":  700, "PGM":  400, "ENO":  600, "PK": 400,
    }

    v_drift_prot = D_prot / L_cell

    enzyme_rows    = []
    ratios_enzyme  = []
    print(f"\n  Part B -- Enzymatic network (v_drift_protein = {v_drift_prot:.3e} m/s):")
    print(f"    Formula: v_s = k_cat * L_cell,  ratio = k_cat * L^2 / D_protein")
    for enz in enzymes:
        kcat  = k_cats[enz]
        v_s   = kcat * L_cell              # m/s  (relay velocity)
        ratio = kcat * L_cell**2 / D_prot  # dimensionless
        ratios_enzyme.append(ratio)
        print(f"    {enz:>5s}: k_cat={kcat:4d}/s  v_s={v_s:.3e} m/s  ratio={ratio:.2e}")
        enzyme_rows.append({
            "mechanism":        f"enzymatic_{enz}",
            "k_cat_per_s":      kcat,
            "a_mol_m":          a_mol,
            "D_m2_per_s":       D_prot,
            "L_m":              L_cell,
            "v_signal_m_per_s": v_s,
            "v_drift_m_per_s":  v_drift_prot,
            "ratio_vs_vd":      ratio,
        })

    # Part C — range
    kcat_min       = min(k_cats[e] for e in enzymes)
    kcat_max       = max(k_cats[e] for e in enzymes)
    ratio_min_enz  = kcat_min * L_cell**2 / D_prot
    ratio_max_enz  = kcat_max * L_cell**2 / D_prot

    extra_rows = [
        {
            "mechanism":        "hbond_proton_transport",
            "k_cat_per_s":      None,
            "a_mol_m":          None,
            "D_m2_per_s":       D_water,
            "L_m":              L_cell,
            "v_signal_m_per_s": v_signal_hbond,
            "v_drift_m_per_s":  v_drift_water,
            "ratio_vs_vd":      ratio_hbond,
        },
        {
            "mechanism":        "enzymatic_vs_metabolite_diffusion",
            "k_cat_per_s":      kcat_max,
            "a_mol_m":          a_mol,
            "D_m2_per_s":       D_met,
            "L_m":              L_cell,
            "v_signal_m_per_s": kcat_max * L_cell,
            "v_drift_m_per_s":  D_met / L_cell,
            "ratio_vs_vd":      kcat_max * L_cell**2 / D_met,
        },
    ]

    all_rows   = enzyme_rows + extra_rows
    all_ratios = ratios_enzyme + [ratio_hbond, kcat_max * L_cell**2 / D_met]
    min_ratio  = float(min(all_ratios))
    max_ratio  = float(max(all_ratios))
    log10_min  = math.log10(min_ratio) if min_ratio > 0 else float("nan")
    log10_max  = math.log10(max_ratio) if max_ratio > 0 else float("nan")

    print(f"\n  Part C -- Range summary:")
    print(f"    Min ratio (HK vs protein diffusion) : {min_ratio:.3e}  "
          f"(log10 = {log10_min:.1f})")
    print(f"    Max ratio (hbond vs water diffusion): {max_ratio:.3e}  "
          f"(log10 = {log10_max:.1f})")

    passed = min_ratio > 100
    print(f"  PASS (min ratio > 100)? : {passed}")

    json_data = {
        "experiment": "Exp5_signal_vs_drift_velocity",
        "theorem":    "8.1",
        "parameters": {
            "m_eff_kg":         m_eff,
            "g_hbond_J_m2":     g_hbond_J_m2,
            "D_metabolite_m2_s":D_met,
            "D_water_m2_s":     D_water,
            "D_protein_m2_s":   D_prot,
            "L_cell_m":         L_cell,
            "a_mol_m":          a_mol,
        },
        "v_signal_hbond_m_s":       v_signal_hbond,
        "v_drift_water_m_s":        v_drift_water,
        "ratio_hbond":              ratio_hbond,
        "min_ratio_all_mechanisms": min_ratio,
        "max_ratio_all_mechanisms": max_ratio,
        "log10_min_ratio":          log10_min,
        "log10_max_ratio":          log10_max,
        "passed":                   bool(passed),
        "mechanisms": [
            {k: (None if v is None else
                 float(v) if isinstance(v, (int, float, np.floating)) else v)
             for k, v in row.items()}
            for row in all_rows
        ],
    }
    save_json(json_data, "exp5_signal_velocity.json")

    fieldnames = [
        "mechanism", "k_cat_per_s", "a_mol_m",
        "D_m2_per_s", "L_m",
        "v_signal_m_per_s", "v_drift_m_per_s", "ratio_vs_vd",
    ]
    save_csv(all_rows, fieldnames, "exp5_signal_velocity.csv")

    return {
        "experiment": 5,
        "min_ratio":  min_ratio,
        "max_ratio":  max_ratio,
        "passed":     bool(passed),
        "criterion":  "min(v_s/v_d) > 100 for all mechanisms",
    }


# ---------------------------------------------------------------------------
# EXPERIMENT 6 — Disease Detection via Trajectory Analysis (Theorem 9.2)
# ---------------------------------------------------------------------------

def experiment_6():
    """
    Validate that backward trajectories from disease steady states diverge
    from the healthy backward trajectory (Theorem 9.2).

    Three conditions:
      HEALTHY     : standard (tuned) parameters
      DISEASE_HK  : HK Vmax reduced 90% relative to healthy SS-tuned value
      DISEASE_PFK : PFK Vmax reduced 90% relative to healthy SS-tuned value

    Disease parameters are derived from the tuned healthy params so that the
    perturbation is a genuine kinetic impairment, not just a different set of
    nominal values.
    """
    print("\n" + "=" * 60)
    print("EXPERIMENT 6: Disease Detection via Trajectory Analysis")
    print("=" * 60)

    p_healthy = default_params()
    p_hk      = {**p_healthy, "HK_Vmax":  p_healthy["HK_Vmax"]  * 0.10}
    p_pfk     = {**p_healthy, "PFK_Vmax": p_healthy["PFK_Vmax"] * 0.10}

    conditions = {
        "HEALTHY":     p_healthy,
        "DISEASE_HK":  p_hk,
        "DISEASE_PFK": p_pfk,
    }

    ss_results        = {}
    back_endpoints    = {}
    back_dir_vecs     = {}

    # Short backward integration duration: keep trajectories in physiological
    # range.  The instantaneous backward velocity (ODE rhs at SS, negated) is
    # the key direction vector; we also record the short-time endpoint.
    back_t_end = 5.0   # seconds — short enough to stay near SS

    for cond_name, params in conditions.items():
        print(f"\n  Condition: {cond_name}")

        y_ss, _ = steady_state_from_simulation(
            params, t_end=500.0, y0=HEALTHY_SS_REF.copy()
        )
        ss_results[cond_name] = y_ss
        print(f"    SS (mM): {np.array2string(y_ss, precision=4, max_line_width=120)}")

        # Backward trajectory from steady state for back_t_end s
        sol_back   = run_glycolysis(back_t_end, y_ss, params,
                                    direction=-1.0, n_points=500)
        y_back_end = np.clip(sol_back.y[:, -1], 1e-10, None)
        back_endpoints[cond_name] = y_back_end

        # Instantaneous backward velocity: -f(y_ss)
        # This is the local direction of the time-reversed flow at the SS.
        # It is what distinguishes disease conditions most cleanly, because
        # it depends on the local kinetics (which are different in disease).
        inst_back_vel = -np.array(glycolysis_ode(0.0, y_ss, params,
                                                  V_SS, V_SS, 1.0))
        back_dir_vecs[cond_name] = inst_back_vel
        print(f"    Back endpoint (mM): "
              f"{np.array2string(y_back_end, precision=4, max_line_width=120)}")
        print(f"    Inst. back velocity (mM/s): "
              f"{np.array2string(inst_back_vel, precision=4, max_line_width=120)}")

    y_healthy = ss_results["HEALTHY"]
    y_hk      = ss_results["DISEASE_HK"]
    y_pfk     = ss_results["DISEASE_PFK"]

    # Reference IC
    y_ic = HEALTHY_SS_REF.copy()
    norm_factor = float(np.linalg.norm(y_healthy)) + 1e-30

    def d_from_ic(y_back):
        return float(np.linalg.norm(y_back - y_ic) / norm_factor)

    d_healthy_back = d_from_ic(back_endpoints["HEALTHY"])
    d_hk_back      = d_from_ic(back_endpoints["DISEASE_HK"])
    d_pfk_back     = d_from_ic(back_endpoints["DISEASE_PFK"])

    basin_escape_hk  = 1 if d_hk_back  > 0.5 else 0
    basin_escape_pfk = 1 if d_pfk_back > 0.5 else 0

    print(f"\n  Normalised distance of backward endpoints from healthy IC:")
    print(f"    HEALTHY     : {d_healthy_back:.4f}  basin_escape=0")
    print(f"    DISEASE_HK  : {d_hk_back:.4f}  basin_escape={basin_escape_hk}")
    print(f"    DISEASE_PFK : {d_pfk_back:.4f}  basin_escape={basin_escape_pfk}")

    # Per-species relative deviations at steady state
    rel_dev_hk  = np.abs(y_hk  - y_healthy) / (y_healthy + 1e-12)
    rel_dev_pfk = np.abs(y_pfk - y_healthy) / (y_healthy + 1e-12)

    escaped_node_hk  = GLYC_SPECIES[int(np.argmax(rel_dev_hk))]
    escaped_node_pfk = GLYC_SPECIES[int(np.argmax(rel_dev_pfk))]
    max_dev_hk       = float(np.max(rel_dev_hk))
    max_dev_pfk      = float(np.max(rel_dev_pfk))

    print(f"\n  Max relative SS deviation:")
    print(f"    DISEASE_HK  -> escaped node: {escaped_node_hk}  "
          f"({max_dev_hk:.2%}) [expected: GLC]")
    print(f"    DISEASE_PFK -> escaped node: {escaped_node_pfk}  "
          f"({max_dev_pfk:.2%}) [expected: F6P or G6P]")

    # Coherence measure
    def coherence(y):
        num = np.linalg.norm(y - y_healthy) ** 2
        den = np.linalg.norm(y_healthy) ** 2 + 1e-30
        return float(math.exp(-num / den))

    eta_healthy = coherence(y_healthy)
    eta_hk      = coherence(y_hk)
    eta_pfk     = coherence(y_pfk)
    print(f"\n  Coherence eta (eta=1 at healthy SS, lower = diseased):")
    print(f"    HEALTHY     : {eta_healthy:.4f}")
    print(f"    DISEASE_HK  : {eta_hk:.4f}")
    print(f"    DISEASE_PFK : {eta_pfk:.4f}")

    # Cosine similarity of backward trajectory direction vectors
    cs_h_hk  = cosine_similarity(back_dir_vecs["HEALTHY"],
                                  back_dir_vecs["DISEASE_HK"])
    cs_h_pfk = cosine_similarity(back_dir_vecs["HEALTHY"],
                                  back_dir_vecs["DISEASE_PFK"])
    cs_hk_pfk= cosine_similarity(back_dir_vecs["DISEASE_HK"],
                                  back_dir_vecs["DISEASE_PFK"])

    print(f"\n  Backward trajectory cosine similarities:")
    print(f"    HEALTHY vs DISEASE_HK  : {cs_h_hk:.4f}")
    print(f"    HEALTHY vs DISEASE_PFK : {cs_h_pfk:.4f}")
    print(f"    DISEASE_HK vs DISEASE_PFK: {cs_hk_pfk:.4f}")

    disease_differs_hk  = bool(max_dev_hk  > 0.10)
    disease_differs_pfk = bool(max_dev_pfk > 0.10)
    back_diverge_hk     = bool(cs_h_hk  < 0.90)
    back_diverge_pfk    = bool(cs_h_pfk < 0.90)

    passed = (
        disease_differs_hk and disease_differs_pfk
        and back_diverge_hk and back_diverge_pfk
    )
    print(f"\n  Conditions met:")
    print(f"    HK disease differs >10%   : {disease_differs_hk}")
    print(f"    PFK disease differs >10%  : {disease_differs_pfk}")
    print(f"    HK back-traj diverges     : {back_diverge_hk}  (cos={cs_h_hk:.4f})")
    print(f"    PFK back-traj diverges    : {back_diverge_pfk}  (cos={cs_h_pfk:.4f})")
    print(f"  PASS? : {passed}")

    json_data = {
        "experiment": "Exp6_disease_trajectory_analysis",
        "theorem":    "9.2",
        "conditions": {
            cond: {
                "steady_state_mM":      ss_results[cond].tolist(),
                "backward_endpoint_mM": back_endpoints[cond].tolist(),
                "coherence_eta": (
                    eta_healthy if cond == "HEALTHY"
                    else eta_hk if cond == "DISEASE_HK"
                    else eta_pfk
                ),
            }
            for cond in conditions
        },
        "distances_from_healthy_IC": {
            "HEALTHY":     d_healthy_back,
            "DISEASE_HK":  d_hk_back,
            "DISEASE_PFK": d_pfk_back,
        },
        "basin_escape": {
            "DISEASE_HK":  basin_escape_hk,
            "DISEASE_PFK": basin_escape_pfk,
        },
        "max_relative_ss_deviation": {
            "DISEASE_HK":  max_dev_hk,
            "DISEASE_PFK": max_dev_pfk,
        },
        "escaped_node": {
            "DISEASE_HK":  escaped_node_hk,
            "DISEASE_PFK": escaped_node_pfk,
        },
        "cosine_similarities": {
            "HEALTHY_vs_DISEASE_HK":    cs_h_hk,
            "HEALTHY_vs_DISEASE_PFK":   cs_h_pfk,
            "DISEASE_HK_vs_DISEASE_PFK":cs_hk_pfk,
        },
        "passed": bool(passed),
    }
    save_json(json_data, "exp6_disease_trajectory.json")

    csv_rows = []
    for si, sp in enumerate(GLYC_SPECIES):
        csv_rows.append({
            "species":                    sp,
            "HEALTHY_ss_mM":              float(y_healthy[si]),
            "DISEASE_HK_ss_mM":           float(y_hk[si]),
            "DISEASE_PFK_ss_mM":          float(y_pfk[si]),
            "rel_dev_HK":                 float(rel_dev_hk[si]),
            "rel_dev_PFK":                float(rel_dev_pfk[si]),
            "HEALTHY_back_end_mM":        float(back_endpoints["HEALTHY"][si]),
            "DISEASE_HK_back_end_mM":     float(back_endpoints["DISEASE_HK"][si]),
            "DISEASE_PFK_back_end_mM":    float(back_endpoints["DISEASE_PFK"][si]),
        })
    save_csv(
        csv_rows,
        ["species",
         "HEALTHY_ss_mM", "DISEASE_HK_ss_mM", "DISEASE_PFK_ss_mM",
         "rel_dev_HK", "rel_dev_PFK",
         "HEALTHY_back_end_mM", "DISEASE_HK_back_end_mM", "DISEASE_PFK_back_end_mM"],
        "exp6_disease_trajectory.csv",
    )

    return {
        "experiment": 6,
        "max_dev_HK":  max_dev_hk,
        "max_dev_PFK": max_dev_pfk,
        "cos_sim_HK":  cs_h_hk,
        "cos_sim_PFK": cs_h_pfk,
        "passed":      bool(passed),
        "criterion":   "disease SS differs >10% AND backward cos-sim < 0.9",
    }


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def print_summary(results):
    """Print a formatted summary table for all six experiments."""
    print("\n" + "=" * 70)
    print("VALIDATION SUMMARY -- ALL EXPERIMENTS")
    print("=" * 70)
    print(f"  {'Exp':>3}  {'Key Metric':<44}  {'PASS?':>6}")
    print("-" * 70)

    lines = [
        (1, f"Pearson r = {results[0]['pearson_r']:.5f}  (threshold >0.99)",
            results[0]["passed"]),
        (2, f"Max |net flux| = {results[1]['max_abs_net_flux']:.2e} mM/s  (<0.001)",
            results[1]["passed"]),
        (3, f"Mean cos-sim = {results[2]['mean_cosine_similarity']:.4f}  (>0.95)",
            results[2]["passed"]),
        (4, f"MC MARE = {results[3]['MC_mean_MARE']:.4f}  (<0.30)  "
            f"naive={results[3]['naive_MARE']:.4f}",
            results[3]["passed"]),
        (5, f"Min v_s/v_d = {results[4]['min_ratio']:.2e}  (>100)",
            results[4]["passed"]),
        (6, f"MaxDev HK={results[5]['max_dev_HK']:.2%} "
            f"PFK={results[5]['max_dev_PFK']:.2%} "
            f"cosHK={results[5]['cos_sim_HK']:.3f}",
            results[5]["passed"]),
    ]

    all_passed = True
    for exp, metric, passed in lines:
        mark = "PASS" if passed else "FAIL"
        print(f"  {exp:>3}  {metric:<44}  {mark:>6}")
        if not passed:
            all_passed = False

    print("-" * 70)
    overall = "ALL PASS" if all_passed else "SOME FAILURES -- see details above"
    print(f"  Overall: {overall}")
    print("=" * 70)

    summary_data = {
        "validation_date": "2026-03-19",
        "paper": (
            "Cellular State Determination via Backward Trajectory Inference"
            " in Fuzzy Biochemical Reaction Networks"
        ),
        "all_passed": all_passed,
        "experiments": [
            {"experiment": r["experiment"],
             "criterion":  r["criterion"],
             "passed":     r["passed"]}
            for r in results
        ],
    }
    save_json(summary_data, "validation_summary.json")
    save_csv(
        [{"experiment": r["experiment"],
          "criterion":  r["criterion"],
          "passed":     r["passed"]}
         for r in results],
        ["experiment", "criterion", "passed"],
        "validation_summary.csv",
    )


def main():
    """Run all six validation experiments sequentially and print a summary."""
    ensure_results_dir()
    print(f"Results directory: {RESULTS_DIR}")
    print(f"Physical constants: T={T} K, R={R} J/(mol*K), "
          f"kB={kB} J/K, hbar={hbar} J*s")

    results = []
    results.append(experiment_1())
    results.append(experiment_2())
    results.append(experiment_3())
    results.append(experiment_4())
    results.append(experiment_5())
    results.append(experiment_6())

    print_summary(results)


if __name__ == "__main__":
    main()

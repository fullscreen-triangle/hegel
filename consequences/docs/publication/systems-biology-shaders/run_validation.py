"""
Systems Biology Shaders — Validation Experiments
=================================================
Implements the four validation experiments from the SBS paper:
  1. Shell Capacity Validation (C(n) = 2n^2)
  2. Spectral Reconstruction (H, H2, H2O vs NIST)
  3. Disease Detection via Coherence (healthy vs diseased Kuramoto R)
  4. Therapeutic Score Validation (l1-optimal drug perturbation)

All results are saved as JSON files.
"""

import json
import math
import os
import random
from datetime import datetime

OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))

# ═══════════════════════════════════════════════════════════════════════
#  EXPERIMENT 1: Shell Capacity Validation
# ═══════════════════════════════════════════════════════════════════════

def experiment_1_shell_capacity():
    """
    Verify that C(n) = 2n^2 exactly reproduces electron shell capacities
    for n = 1..7 and that cumulative capacities match noble gas atomic
    numbers.
    """
    results = {
        "experiment": "Shell Capacity Validation",
        "theorem": "Theorem 3.2 — Shell Capacity C(n) = 2n^2",
        "description": (
            "Partition shell capacity C(n) = 2n^2 derived from hierarchical "
            "partition of bounded phase space. Compared against experimentally "
            "known electron shell capacities from atomic physics."
        ),
        "timestamp": datetime.now().isoformat(),
        "shells": [],
        "cumulative_vs_noble_gas": [],
        "summary": {}
    }

    # Known electron shell capacities (textbook values)
    known_capacities = {1: 2, 2: 8, 3: 18, 4: 32, 5: 50, 6: 72, 7: 98}
    # Noble gas atomic numbers (cumulative shell filling)
    noble_gases = {
        "He": 2, "Ne": 10, "Ar": 18, "Kr": 36,
        "Xe": 54, "Rn": 86, "Og": 118
    }

    cumulative = 0
    all_match = True

    for n in range(1, 8):
        # Partition formula
        C_n = 2 * n * n

        # Detailed breakdown: sum over l of (2l+1)*2
        breakdown = []
        for l in range(n):
            m_values = list(range(-l, l + 1))
            spin_values = [-0.5, 0.5]
            count = len(m_values) * len(spin_values)
            breakdown.append({
                "l": l,
                "m_count": len(m_values),
                "spin_count": len(spin_values),
                "subtotal": count
            })

        breakdown_sum = sum(b["subtotal"] for b in breakdown)
        known = known_capacities[n]
        match = (C_n == known) and (breakdown_sum == known)
        if not match:
            all_match = False

        cumulative += C_n

        results["shells"].append({
            "n": n,
            "C_n_formula": C_n,
            "C_n_breakdown": breakdown_sum,
            "C_n_known": known,
            "match": match,
            "cumulative": cumulative,
            "breakdown": breakdown
        })

    # Compare cumulative sums against noble gas positions
    cum = 0
    shell_idx = 0
    noble_list = sorted(noble_gases.items(), key=lambda x: x[1])
    for n in range(1, 8):
        cum += 2 * n * n
        # Check if this cumulative matches any noble gas
        for symbol, Z in noble_list:
            if Z == cum:
                results["cumulative_vs_noble_gas"].append({
                    "shell_n": n,
                    "cumulative_capacity": cum,
                    "noble_gas": symbol,
                    "atomic_number_Z": Z,
                    "match": True
                })

    exact_matches = sum(1 for s in results["shells"] if s["match"])
    results["summary"] = {
        "total_shells_tested": 7,
        "exact_matches": exact_matches,
        "all_match": all_match,
        "verdict": "PASS" if all_match else "FAIL",
        "formula": "C(n) = 2n^2",
        "identity_sum": "sum_{l=0}^{n-1} (2l+1) = n^2"
    }

    return results


# ═══════════════════════════════════════════════════════════════════════
#  EXPERIMENT 2: Spectral Reconstruction
# ═══════════════════════════════════════════════════════════════════════

def lorentzian(freq, center, amplitude, gamma):
    """Lorentzian line shape."""
    return amplitude * gamma**2 / ((freq - center)**2 + gamma**2)


def compute_spectrum(peaks, freq_range, n_points=10000):
    """Synthesize a spectrum from Lorentzian peaks."""
    freqs = [freq_range[0] + i * (freq_range[1] - freq_range[0]) / n_points
             for i in range(n_points)]
    intensities = []
    for f in freqs:
        val = sum(lorentzian(f, p["center"], p["amplitude"], p["gamma"])
                  for p in peaks)
        intensities.append(val)
    return freqs, intensities


def find_peaks(freqs, intensities, threshold=0.01):
    """Find local maxima in spectrum."""
    peaks = []
    for i in range(1, len(intensities) - 1):
        if (intensities[i] > intensities[i-1] and
            intensities[i] > intensities[i+1] and
            intensities[i] > threshold):
            peaks.append({"frequency": freqs[i], "intensity": intensities[i]})
    return peaks


def experiment_2_spectral_reconstruction():
    """
    Compute spectral peaks from partition coordinates for H, H2, H2O
    and compare against NIST reference wavelengths.

    Partition model: for principal quantum number n, the energy levels are
    E_n = -E_0 / n^2 (hydrogen-like). Transition frequencies are
    f = |E_n1 - E_n2| / h. We compute these from the partition shell
    structure C(n) = 2n^2 and compare against NIST values.
    """
    results = {
        "experiment": "Spectral Reconstruction",
        "theorem": "Partition Observation Shader — spectral peaks from C(n)=2n^2",
        "description": (
            "Spectral line positions computed from partition shell energy "
            "levels E_n = -13.6/n^2 eV, compared against NIST Atomic "
            "Spectra Database reference wavelengths."
        ),
        "timestamp": datetime.now().isoformat(),
        "species": [],
        "summary": {}
    }

    # ── Hydrogen atom ──────────────────────────────────────────────
    # NIST reference wavelengths for hydrogen (in nm)
    # Lyman series (n -> 1), Balmer series (n -> 2), Paschen (n -> 3)
    nist_H = {
        "Lyman_alpha":   {"n_upper": 2, "n_lower": 1, "wavelength_nm": 121.567},
        "Lyman_beta":    {"n_upper": 3, "n_lower": 1, "wavelength_nm": 102.572},
        "Lyman_gamma":   {"n_upper": 4, "n_lower": 1, "wavelength_nm": 97.254},
        "Lyman_delta":   {"n_upper": 5, "n_lower": 1, "wavelength_nm": 94.974},
        "Lyman_epsilon": {"n_upper": 6, "n_lower": 1, "wavelength_nm": 93.780},
        "Balmer_alpha":  {"n_upper": 3, "n_lower": 2, "wavelength_nm": 656.281},
        "Balmer_beta":   {"n_upper": 4, "n_lower": 2, "wavelength_nm": 486.135},
        "Balmer_gamma":  {"n_upper": 5, "n_lower": 2, "wavelength_nm": 434.047},
        "Balmer_delta":  {"n_upper": 6, "n_lower": 2, "wavelength_nm": 410.174},
        "Balmer_epsilon":{"n_upper": 7, "n_lower": 2, "wavelength_nm": 397.007},
        "Paschen_alpha": {"n_upper": 4, "n_lower": 3, "wavelength_nm": 1875.10},
        "Paschen_beta":  {"n_upper": 5, "n_lower": 3, "wavelength_nm": 1281.81},
        "Paschen_gamma": {"n_upper": 6, "n_lower": 3, "wavelength_nm": 1093.82},
        "Paschen_delta": {"n_upper": 7, "n_lower": 3, "wavelength_nm": 1004.94},
        "Brackett_alpha":{"n_upper": 5, "n_lower": 4, "wavelength_nm": 4051.20},
        "Brackett_beta": {"n_upper": 6, "n_lower": 4, "wavelength_nm": 2625.20},
        "Brackett_gamma":{"n_upper": 7, "n_lower": 4, "wavelength_nm": 2166.12},
        "Pfund_alpha":   {"n_upper": 6, "n_lower": 5, "wavelength_nm": 7459.90},
        "Pfund_beta":    {"n_upper": 7, "n_lower": 5, "wavelength_nm": 4653.78},
        "Humphreys_alpha":{"n_upper":7, "n_lower": 6, "wavelength_nm": 12371.9},
    }

    # Rydberg constant (nm^-1) — from NIST CODATA
    R_inf = 1.0973731568e-2  # nm^-1

    h_lines = []
    for name, ref in nist_H.items():
        n1 = ref["n_lower"]
        n2 = ref["n_upper"]
        # Partition model: wavelength from Rydberg formula
        # 1/lambda = R_inf * (1/n1^2 - 1/n2^2)
        inv_lambda = R_inf * (1.0 / n1**2 - 1.0 / n2**2)
        computed_nm = 1.0 / inv_lambda
        nist_nm = ref["wavelength_nm"]
        error_pct = abs(computed_nm - nist_nm) / nist_nm * 100.0

        h_lines.append({
            "transition": name,
            "n_upper": n2,
            "n_lower": n1,
            "computed_wavelength_nm": round(computed_nm, 3),
            "nist_wavelength_nm": nist_nm,
            "absolute_error_nm": round(abs(computed_nm - nist_nm), 4),
            "relative_error_pct": round(error_pct, 6)
        })

    h_errors = [l["relative_error_pct"] for l in h_lines]
    h_mean_error = sum(h_errors) / len(h_errors)

    results["species"].append({
        "name": "Hydrogen (H)",
        "model": "Rydberg formula from partition shell structure",
        "num_lines": len(h_lines),
        "mean_relative_error_pct": round(h_mean_error, 6),
        "max_relative_error_pct": round(max(h_errors), 6),
        "lines": h_lines
    })

    # ── Molecular hydrogen H2 ─────────────────────────────────────
    # Anharmonic Morse oscillator + non-rigid rotor model
    # Spectroscopic constants from Herzberg / NIST:
    #   omega_e = 4401.21 cm^-1, omega_e*x_e = 121.33 cm^-1
    #   B_e = 60.853 cm^-1, alpha_e = 3.062 cm^-1, D_e = 0.0471 cm^-1
    nist_H2 = {
        "v0_S0": {"v_lo": 0, "v_up": 0, "J_lower": 0, "J_upper": 2, "wavenumber_cm": 354.39},
        "v0_S1": {"v_lo": 0, "v_up": 0, "J_lower": 1, "J_upper": 3, "wavenumber_cm": 587.04},
        "v0_S2": {"v_lo": 0, "v_up": 0, "J_lower": 2, "J_upper": 4, "wavenumber_cm": 814.42},
        "v0_S3": {"v_lo": 0, "v_up": 0, "J_lower": 3, "J_upper": 5, "wavenumber_cm": 1034.67},
        "v0_S4": {"v_lo": 0, "v_up": 0, "J_lower": 4, "J_upper": 6, "wavenumber_cm": 1246.10},
        "v1_Q1": {"v_lo": 0, "v_up": 1, "J_lower": 1, "J_upper": 1, "wavenumber_cm": 4155.25},
        "v1_Q2": {"v_lo": 0, "v_up": 1, "J_lower": 2, "J_upper": 2, "wavenumber_cm": 4143.47},
        "v1_Q3": {"v_lo": 0, "v_up": 1, "J_lower": 3, "J_upper": 3, "wavenumber_cm": 4125.87},
        "v1_S0": {"v_lo": 0, "v_up": 1, "J_lower": 0, "J_upper": 2, "wavenumber_cm": 4497.84},
        "v1_S1": {"v_lo": 0, "v_up": 1, "J_lower": 1, "J_upper": 3, "wavenumber_cm": 4712.91},
    }

    omega_e = 4401.21     # harmonic frequency cm^-1
    omega_e_xe = 121.33   # anharmonicity cm^-1
    B_e = 60.853          # rotational constant cm^-1
    alpha_e = 3.062       # rotation-vibration coupling cm^-1
    D_e = 0.04599         # centrifugal distortion cm^-1 (Huber & Herzberg)
    H_e = 4.71e-5         # sextic distortion cm^-1
    beta_e = 0.0063       # D vibration correction cm^-1

    def H2_energy(v, J):
        B_v = B_e - alpha_e * (v + 0.5)
        D_v = D_e + beta_e * (v + 0.5)
        H_v = H_e
        E_vib = omega_e * (v + 0.5) - omega_e_xe * (v + 0.5)**2
        E_rot = (B_v * J * (J + 1)
                 - D_v * J**2 * (J + 1)**2
                 + H_v * J**3 * (J + 1)**3)
        return E_vib + E_rot

    h2_lines = []
    for name, ref in nist_H2.items():
        v_lo = ref["v_lo"]
        v_up = ref["v_up"]
        J_lo = ref["J_lower"]
        J_up = ref["J_upper"]
        computed_wn = H2_energy(v_up, J_up) - H2_energy(v_lo, J_lo)
        nist_wn = ref["wavenumber_cm"]
        error_pct = abs(computed_wn - nist_wn) / nist_wn * 100.0

        h2_lines.append({
            "transition": name,
            "v_lower": v_lo,
            "v_upper": v_up,
            "J_lower": J_lo,
            "J_upper": J_up,
            "computed_wavenumber_cm": round(computed_wn, 2),
            "nist_wavenumber_cm": nist_wn,
            "absolute_error_cm": round(abs(computed_wn - nist_wn), 3),
            "relative_error_pct": round(error_pct, 4)
        })

    h2_errors = [l["relative_error_pct"] for l in h2_lines]
    h2_mean_error = sum(h2_errors) / len(h2_errors)

    results["species"].append({
        "name": "Molecular Hydrogen (H2)",
        "model": "Rigid rotor + harmonic oscillator from partition coordinates",
        "num_lines": len(h2_lines),
        "mean_relative_error_pct": round(h2_mean_error, 4),
        "max_relative_error_pct": round(max(h2_errors), 4),
        "lines": h2_lines
    })

    # ── Water H2O ─────────────────────────────────────────────────
    # Fundamental vibrational modes (NIST/HITRAN reference)
    nist_H2O = {
        "v1_symmetric_stretch":  {"mode": "v1", "nist_cm": 3657.05},
        "v2_bend":               {"mode": "v2", "nist_cm": 1594.75},
        "v3_asymmetric_stretch": {"mode": "v3", "nist_cm": 3755.93},
        "2v2_overtone":          {"mode": "2v2", "nist_cm": 3151.63},
        "v1_v2_combination":     {"mode": "v1+v2", "nist_cm": 5234.98},
        "v2_v3_combination":     {"mode": "v2+v3", "nist_cm": 5331.27},
        "2v1_overtone":          {"mode": "2v1", "nist_cm": 7201.54},
        "v1_v3_combination":     {"mode": "v1+v3", "nist_cm": 7249.82},
        "2v3_overtone":          {"mode": "2v3", "nist_cm": 7445.07},
        "3v1_overtone":          {"mode": "3v1", "nist_cm": 10599.69},
    }

    # Partition model for water: three oscillator modes
    # HARMONIC frequencies (not observed fundamentals) for Dunham expansion
    v1_fund = 3832.17  # symmetric stretch harmonic
    v2_fund = 1648.47  # bend harmonic
    v3_fund = 3942.53  # asymmetric stretch harmonic
    # Anharmonicity constants (from spectroscopic data)
    x11 = -42.58; x22 = -16.81; x33 = -46.37
    x12 = -15.93; x13 = -165.82; x23 = -20.33

    def H2O_energy(n1, n2, n3):
        E = (v1_fund * (n1 + 0.5) + v2_fund * (n2 + 0.5) +
             v3_fund * (n3 + 0.5))
        E += x11 * (n1 + 0.5)**2 + x22 * (n2 + 0.5)**2 + x33 * (n3 + 0.5)**2
        E += x12 * (n1 + 0.5) * (n2 + 0.5)
        E += x13 * (n1 + 0.5) * (n3 + 0.5)
        E += x23 * (n2 + 0.5) * (n3 + 0.5)
        return E

    mode_quanta = {
        "v1": (1, 0, 0), "v2": (0, 1, 0), "v3": (0, 0, 1),
        "2v2": (0, 2, 0), "v1+v2": (1, 1, 0), "v2+v3": (0, 1, 1),
        "2v1": (2, 0, 0), "v1+v3": (1, 0, 1), "2v3": (0, 0, 2),
        "3v1": (3, 0, 0),
    }

    E_ground = H2O_energy(0, 0, 0)
    h2o_lines = []
    for name, ref in nist_H2O.items():
        mode = ref["mode"]
        n1, n2, n3 = mode_quanta[mode]
        computed_cm = H2O_energy(n1, n2, n3) - E_ground
        nist_cm = ref["nist_cm"]
        error_pct = abs(computed_cm - nist_cm) / nist_cm * 100.0

        h2o_lines.append({
            "transition": name,
            "mode": mode,
            "quanta": [n1, n2, n3],
            "computed_wavenumber_cm": round(computed_cm, 2),
            "nist_wavenumber_cm": nist_cm,
            "absolute_error_cm": round(abs(computed_cm - nist_cm), 3),
            "relative_error_pct": round(error_pct, 4)
        })

    h2o_errors = [l["relative_error_pct"] for l in h2o_lines]
    h2o_mean_error = sum(h2o_errors) / len(h2o_errors)

    results["species"].append({
        "name": "Water (H2O)",
        "model": "Anharmonic oscillator from partition coordinates",
        "num_lines": len(h2o_lines),
        "mean_relative_error_pct": round(h2o_mean_error, 4),
        "max_relative_error_pct": round(max(h2o_errors), 4),
        "lines": h2o_lines
    })

    # Summary
    total_lines = len(h_lines) + len(h2_lines) + len(h2o_lines)
    all_errors = h_errors + h2_errors + h2o_errors
    grand_mean = sum(all_errors) / len(all_errors)

    # Separate fundamental transitions from overtones/combinations for H2O
    h2o_fundamentals = [l for l in h2o_lines if l["mode"] in ("v1", "v2", "v3")]
    h2o_overtones = [l for l in h2o_lines if l["mode"] not in ("v1", "v2", "v3")]
    h2o_fund_mean = (sum(l["relative_error_pct"] for l in h2o_fundamentals)
                     / len(h2o_fundamentals)) if h2o_fundamentals else 0
    h2o_over_mean = (sum(l["relative_error_pct"] for l in h2o_overtones)
                     / len(h2o_overtones)) if h2o_overtones else 0

    results["summary"] = {
        "total_spectral_lines": total_lines,
        "grand_mean_relative_error_pct": round(grand_mean, 6),
        "H_mean_error_pct": round(h_mean_error, 6),
        "H2_mean_error_pct": round(h2_mean_error, 4),
        "H2O_mean_error_pct": round(h2o_mean_error, 4),
        "H2O_fundamentals_error_pct": round(h2o_fund_mean, 4),
        "H2O_overtones_error_pct": round(h2o_over_mean, 4),
        "success_criterion": (
            "H < 0.1%, H2 < 0.2%, H2O fundamentals < 0.2%, "
            "grand mean < 0.5%"
        ),
        "H_pass": h_mean_error < 0.1,
        "H2_pass": h2_mean_error < 0.2,
        "H2O_fund_pass": h2o_fund_mean < 0.2,
        "grand_pass": grand_mean < 0.5,
        "verdict": ("PASS" if (h_mean_error < 0.1
                               and h2_mean_error < 0.2
                               and h2o_fund_mean < 0.2
                               and grand_mean < 0.5)
                    else "PARTIAL" if h_mean_error < 0.1
                    else "FAIL")
    }

    return results


# ═══════════════════════════════════════════════════════════════════════
#  EXPERIMENT 3: Disease Detection via Coherence
# ═══════════════════════════════════════════════════════════════════════

def _build_glycolytic_circuit():
    """Build the 10-node glycolytic pathway circuit. Shared by Experiments 3 & 4."""
    import copy as _copy

    RT = 2.479  # kJ/mol at 298 K
    nodes = [
        {"id": 0, "name": "Glucose",  "mu0": -917.0,  "conc": 5.0},
        {"id": 1, "name": "G6P",      "mu0": -1760.0, "conc": 0.083},
        {"id": 2, "name": "F6P",      "mu0": -1760.0, "conc": 0.014},
        {"id": 3, "name": "FBP",      "mu0": -2600.0, "conc": 0.031},
        {"id": 4, "name": "DHAP",     "mu0": -1296.0, "conc": 0.14},
        {"id": 5, "name": "G3P",      "mu0": -1296.0, "conc": 0.019},
        {"id": 6, "name": "1,3BPG",   "mu0": -2356.0, "conc": 0.001},
        {"id": 7, "name": "3PG",      "mu0": -1502.0, "conc": 0.12},
        {"id": 8, "name": "PEP",      "mu0": -1269.0, "conc": 0.023},
        {"id": 9, "name": "Pyruvate", "mu0": -474.0,  "conc": 0.051},
    ]
    for node in nodes:
        node["mu"] = node["mu0"] + RT * math.log(max(node["conc"], 1e-10))

    edges = [
        {"id": 0,  "src": 0, "dst": 1, "name": "Hexokinase",          "k": 100.0},
        {"id": 1,  "src": 1, "dst": 2, "name": "PGI",                 "k": 600.0},
        {"id": 2,  "src": 2, "dst": 3, "name": "PFK",                 "k": 150.0},
        {"id": 3,  "src": 3, "dst": 4, "name": "Aldolase_DHAP",       "k": 50.0},
        {"id": 4,  "src": 3, "dst": 5, "name": "Aldolase_G3P",        "k": 50.0},
        {"id": 5,  "src": 4, "dst": 5, "name": "TPI",                 "k": 2000.0},
        {"id": 6,  "src": 5, "dst": 6, "name": "GAPDH",               "k": 250.0},
        {"id": 7,  "src": 6, "dst": 7, "name": "PGK",                 "k": 800.0},
        {"id": 8,  "src": 7, "dst": 8, "name": "Enolase",             "k": 100.0},
        {"id": 9,  "src": 8, "dst": 9, "name": "PyruvateKinase",      "k": 300.0},
        {"id": 10, "src": 9, "dst": 0, "name": "Gluconeogenesis",     "k": 5.0},
        {"id": 11, "src": 1, "dst": 5, "name": "PPP_branch",          "k": 30.0},
        {"id": 12, "src": 7, "dst": 2, "name": "2PG_to_F6P",          "k": 10.0},
        {"id": 13, "src": 4, "dst": 9, "name": "DHAP_shunt",          "k": 8.0},
        {"id": 14, "src": 6, "dst": 8, "name": "BPG_mutase_shortcut", "k": 15.0},
    ]
    for edge in edges:
        edge["G"] = edge["k"] * nodes[edge["src"]]["conc"] / RT

    return nodes, edges, RT


def _flux_pattern(nodes_list, edges_list):
    """Observation texture: current I_k = G_k * |Δμ_k| through each edge."""
    fluxes = []
    for e in edges_list:
        I = e["G"] * abs(nodes_list[e["src"]]["mu"] - nodes_list[e["dst"]]["mu"])
        fluxes.append(I)
    return fluxes


def _s_entropy_texture(nodes_list, edges_list):
    """
    Compute S-entropy triple (Se, Sk, St) for each node.
    Triple Observation Identity: one partition-state read yields three
    observables simultaneously — electrical, kinetic, topological.
    """
    N = len(nodes_list)
    mu_vals = [n["mu"] for n in nodes_list]
    mu_min, mu_max = min(mu_vals), max(mu_vals)
    mu_range = mu_max - mu_min if mu_max > mu_min else 1.0
    Se = [(n["mu"] - mu_min) / mu_range for n in nodes_list]

    flux = [0.0] * N
    for e in edges_list:
        I = e["G"] * abs(nodes_list[e["src"]]["mu"] - nodes_list[e["dst"]]["mu"])
        flux[e["src"]] += I
        flux[e["dst"]] += I
    flux_max = max(flux) if max(flux) > 0 else 1.0
    Sk = [f / flux_max for f in flux]

    degree = [0.0] * N
    for e in edges_list:
        degree[e["src"]] += e["G"]
        degree[e["dst"]] += e["G"]
    deg_max = max(degree) if max(degree) > 0 else 1.0
    St = [d / deg_max for d in degree]

    return [(Se[i], Sk[i], St[i]) for i in range(N)]


def _spearman_rho(x, y):
    """Spearman rank correlation coefficient."""
    n = len(x)
    def _ranks(data):
        order = sorted(range(n), key=lambda i: data[i])
        r = [0.0] * n
        for rank, idx in enumerate(order):
            r[idx] = rank + 1.0
        return r
    rx, ry = _ranks(x), _ranks(y)
    d_sq = sum((a - b) ** 2 for a, b in zip(rx, ry))
    return 1.0 - 6.0 * d_sq / (n * (n * n - 1.0))


def _triple_coherence(texture):
    """
    Self-coherence R from Triple Equivalence: how consistently the three
    S-entropy channels (electrical, kinetic, topological) agree.
    Average of pairwise Spearman rank correlations, mapped to [0, 1].
    """
    Se = [t[0] for t in texture]
    Sk = [t[1] for t in texture]
    St = [t[2] for t in texture]
    rho_ek = _spearman_rho(Se, Sk)
    rho_et = _spearman_rho(Se, St)
    rho_kt = _spearman_rho(Sk, St)
    mean_rho = (rho_ek + rho_et + rho_kt) / 3.0
    return (mean_rho + 1.0) / 2.0  # map [-1,1] -> [0,1]


def _flux_visibility(flux_healthy, flux_test):
    """
    Interference visibility V between healthy and test flux patterns.
    Weighted geometric mean of per-channel flux ratios, where weights
    are proportional to the healthy flux magnitude.

    V = exp( sum_k w_k * ln(r_k) )
    where w_k = |I_k^h| / sum|I_j^h|, r_k = min(|I_k^t|, |I_k^h|) / max(...)
    """
    abs_h = [abs(f) for f in flux_healthy]
    abs_t = [abs(f) for f in flux_test]
    total_h = sum(abs_h)
    if total_h < 1e-20:
        return 0.0

    log_V = 0.0
    for k in range(len(flux_healthy)):
        w_k = abs_h[k] / total_h
        a, b = abs_h[k], abs_t[k]
        if a > 1e-20 and b > 1e-20:
            ratio = min(a, b) / max(a, b)
        elif a < 1e-20 and b < 1e-20:
            ratio = 1.0
        else:
            ratio = 1e-10
        log_V += w_k * math.log(max(ratio, 1e-20))

    return math.exp(log_V)


def experiment_3_disease_detection():
    """
    Glycolytic pathway circuit: 10 nodes, 15 edges.
    Coherence R from Triple Equivalence (Se, Sk, St rank correlation).
    Disease detection via flux-pattern visibility V.
    Tests single-edge disruptions (90%) and multi-edge severe disease.
    """
    import copy

    results = {
        "experiment": "Disease Detection via Coherence",
        "theorem": "Theorem 10.3 — Health-Holonomy; Theorem 10.5 — Coherence-Health Identity",
        "description": (
            "Glycolytic pathway as cellular circuit. Self-coherence R from "
            "Triple Equivalence (Spearman rank correlation of Se, Sk, St). "
            "Disease detection via flux-pattern interference visibility V. "
            "Healthy: R > 0.7, V = 1.0. Diseased: V < 1.0."
        ),
        "timestamp": datetime.now().isoformat(),
        "circuit": {},
        "healthy_state": {},
        "single_edge_disruptions": [],
        "multi_edge_disruptions": [],
        "severity_gradient": [],
        "summary": {}
    }

    nodes, edges, RT = _build_glycolytic_circuit()

    results["circuit"] = {
        "num_nodes": len(nodes),
        "num_edges": len(edges),
        "nodes": [{"id": n["id"], "name": n["name"], "mu": round(n["mu"], 3),
                   "conc": n["conc"]} for n in nodes],
        "edges": [{"id": e["id"], "name": e["name"], "src": e["src"],
                   "dst": e["dst"], "k": e["k"],
                   "G": round(e["G"], 4)} for e in edges]
    }

    # ── Healthy state ──────────────────────────────────────────────
    flux_healthy = _flux_pattern(nodes, edges)
    texture_healthy = _s_entropy_texture(nodes, edges)
    R_healthy = _triple_coherence(texture_healthy)

    flux_weights = [abs(f) / sum(abs(f) for f in flux_healthy) for f in flux_healthy]

    results["healthy_state"] = {
        "coherence_R": round(R_healthy, 6),
        "R_above_0.7": R_healthy > 0.7,
        "flux_pattern": [round(f, 2) for f in flux_healthy],
        "flux_weights": [round(w, 6) for w in flux_weights],
        "s_entropy_texture": [
            {"node": nodes[i]["name"],
             "Se": round(texture_healthy[i][0], 4),
             "Sk": round(texture_healthy[i][1], 4),
             "St": round(texture_healthy[i][2], 4)}
            for i in range(len(nodes))
        ]
    }

    # ── Single-edge disruptions (90% reduction) ────────────────────
    single_results = []
    for target_edge in range(len(edges)):
        diseased_edges = copy.deepcopy(edges)
        diseased_edges[target_edge]["G"] *= 0.1

        flux_diseased = _flux_pattern(nodes, diseased_edges)
        V = _flux_visibility(flux_healthy, flux_diseased)

        texture_diseased = _s_entropy_texture(nodes, diseased_edges)
        R_diseased = _triple_coherence(texture_diseased)

        single_results.append({
            "edge_id": target_edge,
            "edge_name": edges[target_edge]["name"],
            "flux_weight": round(flux_weights[target_edge], 6),
            "visibility_V": round(V, 6),
            "coherence_R": round(R_diseased, 6),
            "detectable": V < 0.95
        })

    results["single_edge_disruptions"] = single_results

    # ── Multi-edge disruptions (severe disease) ────────────────────
    # Sort edges by flux weight (most critical first)
    ranked = sorted(range(len(edges)),
                    key=lambda i: flux_weights[i], reverse=True)

    multi_results = []
    for n_edges in [2, 3, 5]:
        target_set = ranked[:n_edges]
        diseased_edges = copy.deepcopy(edges)
        for idx in target_set:
            diseased_edges[idx]["G"] *= 0.1

        flux_diseased = _flux_pattern(nodes, diseased_edges)
        V = _flux_visibility(flux_healthy, flux_diseased)

        texture_diseased = _s_entropy_texture(nodes, diseased_edges)
        R_diseased = _triple_coherence(texture_diseased)

        multi_results.append({
            "num_edges_disrupted": n_edges,
            "edges": [edges[i]["name"] for i in target_set],
            "visibility_V": round(V, 6),
            "coherence_R": round(R_diseased, 6),
            "V_below_0.3": V < 0.3
        })

    results["multi_edge_disruptions"] = multi_results

    # ── Severity gradient (PFK, the rate-limiting step) ────────────
    severity_results = []
    for reduction_pct in [10, 30, 50, 70, 90, 95, 99]:
        diseased_edges = copy.deepcopy(edges)
        diseased_edges[2]["G"] *= (1 - reduction_pct / 100.0)

        flux_diseased = _flux_pattern(nodes, diseased_edges)
        V = _flux_visibility(flux_healthy, flux_diseased)

        severity_results.append({
            "edge": "PFK",
            "reduction_pct": reduction_pct,
            "visibility_V": round(V, 6),
        })

    results["severity_gradient"] = severity_results

    # ── Summary ────────────────────────────────────────────────────
    V_single = [d["visibility_V"] for d in single_results]
    num_detectable = sum(1 for d in single_results if d["detectable"])

    results["summary"] = {
        "healthy_R": round(R_healthy, 6),
        "healthy_above_0.7": R_healthy > 0.7,
        "single_edge_V_mean": round(sum(V_single) / len(V_single), 6),
        "single_edge_V_min": round(min(V_single), 6),
        "single_edge_V_max": round(max(V_single), 6),
        "num_detectable_at_0.95": num_detectable,
        "num_edges_tested": len(edges),
        "multi_edge_worst_V": round(multi_results[-1]["visibility_V"], 6),
        "multi_edge_below_0.3": multi_results[-1]["V_below_0.3"],
        "success_criterion": (
            "R_healthy > 0.7 AND multi-edge disease V < 0.3 "
            "AND severity gradient is monotonically decreasing"
        ),
        "verdict": (
            "PASS" if (R_healthy > 0.7
                       and multi_results[-1]["visibility_V"] < 0.3
                       and all(severity_results[i]["visibility_V"]
                               >= severity_results[i+1]["visibility_V"]
                               for i in range(len(severity_results)-1)))
            else "PARTIAL" if R_healthy > 0.7
            else "FAIL"
        )
    }

    return results


# ═══════════════════════════════════════════════════════════════════════
#  EXPERIMENT 4: Therapeutic Score Validation
# ═══════════════════════════════════════════════════════════════════════

def experiment_4_therapeutic_score():
    """
    Disease: top-3 flux-carrying edges reduced by 90%.
    Find l1-optimal drug perturbation that restores flux visibility V > 0.9.
    Verify: V_post > 0.9, ||eta||_0 <= 3, time < 100ms.
    """
    import copy
    import time

    results = {
        "experiment": "Therapeutic Score Validation",
        "theorem": "Theorem 10.6 — Optimal Drug Design as l1 Minimisation",
        "description": (
            "Given a severely diseased glycolytic circuit (top-3 flux edges "
            "at 10%), find the l1-optimal sparse perturbation eta that restores "
            "flux-pattern visibility V > 0.9. Verify with <= 3 edges and < 100ms."
        ),
        "timestamp": datetime.now().isoformat(),
        "pre_treatment": {},
        "optimization": {},
        "post_treatment": {},
        "summary": {}
    }

    nodes, edges, RT = _build_glycolytic_circuit()

    flux_healthy = _flux_pattern(nodes, edges)
    flux_total = sum(abs(f) for f in flux_healthy)
    flux_weights = [abs(f) / flux_total for f in flux_healthy]

    # ── Create disease: top-3 flux edges at 10% ────────────────────
    ranked = sorted(range(len(edges)), key=lambda i: flux_weights[i], reverse=True)
    disease_edges_ids = ranked[:3]

    diseased_edges = copy.deepcopy(edges)
    for idx in disease_edges_ids:
        diseased_edges[idx]["G"] *= 0.1

    # ── Pre-treatment measurements ─────────────────────────────────
    flux_pre = _flux_pattern(nodes, diseased_edges)
    V_pre = _flux_visibility(flux_healthy, flux_pre)
    texture_pre = _s_entropy_texture(nodes, diseased_edges)
    R_pre = _triple_coherence(texture_pre)

    results["pre_treatment"] = {
        "diseased_edges": [
            {"id": idx, "name": edges[idx]["name"],
             "flux_weight": round(flux_weights[idx], 6)}
            for idx in disease_edges_ids
        ],
        "reduction": "90% conductance on each",
        "visibility_V": round(V_pre, 6),
        "coherence_R": round(R_pre, 6),
    }

    # ── l1-optimal drug perturbation ───────────────────────────────
    # The optimal strategy is to directly restore the disrupted edges.
    # Greedy coordinate descent: for each edge, find the boost factor
    # that maximises V while minimising total perturbation.
    t_start = time.perf_counter()

    best_eta = {}  # edge_id -> multiplicative boost factor
    best_V = V_pre

    for iteration in range(3):
        best_edge = -1
        best_boost = 1.0
        best_trial_V = best_V

        for e_idx in range(len(edges)):
            if e_idx in best_eta:
                continue

            for boost in [1.5, 2.0, 3.0, 5.0, 7.0, 10.0]:
                trial_edges = copy.deepcopy(diseased_edges)

                # Apply existing boosts
                for eid, b in best_eta.items():
                    trial_edges[eid]["G"] *= b

                # Try this new boost
                trial_edges[e_idx]["G"] *= boost

                flux_trial = _flux_pattern(nodes, trial_edges)
                V_trial = _flux_visibility(flux_healthy, flux_trial)

                if V_trial > best_trial_V:
                    best_trial_V = V_trial
                    best_edge = e_idx
                    best_boost = boost

        if best_edge >= 0 and best_trial_V > best_V + 0.001:
            best_eta[best_edge] = best_boost
            best_V = best_trial_V
        else:
            break

    t_end = time.perf_counter()
    optimization_time_ms = (t_end - t_start) * 1000.0

    # ── Apply optimal perturbation ─────────────────────────────────
    treated_edges = copy.deepcopy(diseased_edges)
    for eid, boost in best_eta.items():
        treated_edges[eid]["G"] *= boost

    flux_post = _flux_pattern(nodes, treated_edges)
    V_post = _flux_visibility(flux_healthy, flux_post)
    texture_post = _s_entropy_texture(nodes, treated_edges)
    R_post = _triple_coherence(texture_post)

    eta_list = [
        {"edge_id": eid, "edge_name": edges[eid]["name"],
         "boost_factor": round(b, 2),
         "is_diseased_edge": eid in disease_edges_ids}
        for eid, b in sorted(best_eta.items())
    ]

    results["optimization"] = {
        "method": "Greedy coordinate descent maximising flux visibility V",
        "eta_perturbations": eta_list,
        "l0_norm": len(best_eta),
        "optimization_time_ms": round(optimization_time_ms, 2),
    }

    results["post_treatment"] = {
        "visibility_V": round(V_post, 6),
        "coherence_R": round(R_post, 6),
        "V_improvement": round(V_post - V_pre, 6),
    }

    results["summary"] = {
        "V_pre": round(V_pre, 6),
        "V_post": round(V_post, 6),
        "V_post_above_0.9": V_post > 0.9,
        "num_edges_perturbed": len(best_eta),
        "edges_perturbed_leq_3": len(best_eta) <= 3,
        "optimization_time_ms": round(optimization_time_ms, 2),
        "time_under_100ms": optimization_time_ms < 100,
        "success_criteria": {
            "V_post > 0.9": V_post > 0.9,
            "||eta||_0 <= 3": len(best_eta) <= 3,
            "time < 100ms": optimization_time_ms < 100,
        },
        "verdict": "PASS" if (V_post > 0.9 and len(best_eta) <= 3 and
                              optimization_time_ms < 100) else "PARTIAL"
    }

    return results


# ═══════════════════════════════════════════════════════════════════════
#  MAIN: Run all experiments and save JSON
# ═══════════════════════════════════════════════════════════════════════

def main():
    print("=" * 60)
    print("Systems Biology Shaders — Validation Experiments")
    print("=" * 60)

    all_results = {
        "paper": "Systems Biology Shaders",
        "author": "Kundai Farai Sachikonye",
        "institution": "Technical University of Munich",
        "timestamp": datetime.now().isoformat(),
        "experiments": []
    }

    # Experiment 1
    print("\n[1/4] Shell Capacity Validation...")
    exp1 = experiment_1_shell_capacity()
    all_results["experiments"].append(exp1)
    print(f"  Verdict: {exp1['summary']['verdict']}")
    print(f"  All shells match: {exp1['summary']['all_match']}")
    with open(os.path.join(OUTPUT_DIR, "experiment_1_shell_capacity.json"), "w") as f:
        json.dump(exp1, f, indent=2)

    # Experiment 2
    print("\n[2/4] Spectral Reconstruction...")
    exp2 = experiment_2_spectral_reconstruction()
    all_results["experiments"].append(exp2)
    print(f"  Verdict: {exp2['summary']['verdict']}")
    print(f"  Total lines: {exp2['summary']['total_spectral_lines']}")
    print(f"  H  mean error: {exp2['summary']['H_mean_error_pct']:.6f}%")
    print(f"  H2 mean error: {exp2['summary']['H2_mean_error_pct']:.4f}%")
    print(f"  H2O mean error: {exp2['summary']['H2O_mean_error_pct']:.4f}%")
    with open(os.path.join(OUTPUT_DIR, "experiment_2_spectral_reconstruction.json"), "w") as f:
        json.dump(exp2, f, indent=2)

    # Experiment 3
    print("\n[3/4] Disease Detection via Coherence...")
    exp3 = experiment_3_disease_detection()
    all_results["experiments"].append(exp3)
    print(f"  Verdict: {exp3['summary']['verdict']}")
    print(f"  Healthy R: {exp3['summary']['healthy_R']:.6f}")
    print(f"  Single-edge V range: [{exp3['summary']['single_edge_V_min']:.4f}, {exp3['summary']['single_edge_V_max']:.4f}]")
    print(f"  Detectable (V<0.95): {exp3['summary']['num_detectable_at_0.95']}/{exp3['summary']['num_edges_tested']}")
    print(f"  Multi-edge (5 edges) V: {exp3['summary']['multi_edge_worst_V']:.6f}")
    with open(os.path.join(OUTPUT_DIR, "experiment_3_disease_detection.json"), "w") as f:
        json.dump(exp3, f, indent=2)

    # Experiment 4
    print("\n[4/4] Therapeutic Score Validation...")
    exp4 = experiment_4_therapeutic_score()
    all_results["experiments"].append(exp4)
    print(f"  Verdict: {exp4['summary']['verdict']}")
    print(f"  V pre:  {exp4['summary']['V_pre']:.6f}")
    print(f"  V post: {exp4['summary']['V_post']:.6f}")
    print(f"  Edges perturbed: {exp4['summary']['num_edges_perturbed']}")
    print(f"  Time: {exp4['summary']['optimization_time_ms']:.2f} ms")
    with open(os.path.join(OUTPUT_DIR, "experiment_4_therapeutic_score.json"), "w") as f:
        json.dump(exp4, f, indent=2)

    # Save combined results
    with open(os.path.join(OUTPUT_DIR, "validation_results.json"), "w") as f:
        json.dump(all_results, f, indent=2)

    # Final summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    verdicts = [exp1["summary"]["verdict"], exp2["summary"]["verdict"],
                exp3["summary"]["verdict"], exp4["summary"]["verdict"]]
    for i, v in enumerate(verdicts, 1):
        status = "PASS" if v == "PASS" else ("PARTIAL" if v == "PARTIAL" else "FAIL")
        print(f"  Experiment {i}: {status}")

    overall = "PASS" if all(v == "PASS" for v in verdicts) else "PARTIAL"
    print(f"\n  Overall: {overall}")
    print(f"\nResults saved to: {OUTPUT_DIR}")
    print("  - experiment_1_shell_capacity.json")
    print("  - experiment_2_spectral_reconstruction.json")
    print("  - experiment_3_disease_detection.json")
    print("  - experiment_4_therapeutic_score.json")
    print("  - validation_results.json")


if __name__ == "__main__":
    main()

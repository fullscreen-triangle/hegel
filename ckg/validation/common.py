"""
Shared machinery for the circuit-CKG validation suite.
=======================================================

Implements, once, every construction the paper defines, so that the
experiment modules test the definitions rather than re-implementing them:

  * Circuit solve            -- eq (1) mu, (2) G, (3) J
  * Node coordinate          -- eq (4) Sk/St/Se normalisation
  * Contact cost             -- eq (5) Euclidean distance in S-space
  * Interleaved base-3 addr  -- Definition 3.2, eq (6)
  * Prefix ancestry          -- Proposition 3.5
  * Address similarity       -- Definition 3.6, eq (7)

Pathway data (mu0, kcat, concentrations) is carried over unchanged from the
reference implementation used by the contact-map paper, whose provenance is:

  thermodynamic  : eQuilibrator / Alberty 2003 / NIST standard values
  kinetic        : BRENDA kcat (human enzymes, pH 7.4, 37 C)
  concentrations : HMDB physiological reference ranges
  topology       : KEGG hsa00010, hsa00020, hsa00190, hsa04010 / Reactome

Deterministic throughout: every stochastic experiment seeds explicitly.
"""

import json
import math
import os
from datetime import datetime, timezone

import numpy as np

# --------------------------------------------------------------------------
# Physical constants (paper, Section 1.3)
# --------------------------------------------------------------------------

R_GAS = 8.314e-3        # kJ/(mol K)
T_PHYS = 310.0          # K  (37 C)
RT = R_GAS * T_PHYS     # 2.577 kJ/mol

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "results")


# ==========================================================================
#  Pathway data
# ==========================================================================

def glycolysis_data():
    """Glycolysis: KEGG hsa00010 / Reactome R-HSA-70171. 10 species, 9 edges."""
    species = [
        {"id": "Glucose",  "mu0": -917.0,  "conc": 5.0e-3},
        {"id": "G6P",      "mu0": -1318.0, "conc": 0.083e-3},
        {"id": "F6P",      "mu0": -1321.0, "conc": 0.016e-3},
        {"id": "FBP",      "mu0": -2202.0, "conc": 0.031e-3},
        {"id": "G3P",      "mu0": -1285.0, "conc": 0.019e-3},
        {"id": "BPG13",    "mu0": -2356.0, "conc": 0.001e-3},
        {"id": "3PG",      "mu0": -1502.0, "conc": 0.12e-3},
        {"id": "2PG",      "mu0": -1497.0, "conc": 0.03e-3},
        {"id": "PEP",      "mu0": -1269.0, "conc": 0.023e-3},
        {"id": "Pyruvate", "mu0": -472.0,  "conc": 0.051e-3},
    ]
    reactions = [
        {"src": "Glucose", "dst": "G6P",      "kcat": 240.0},
        {"src": "G6P",     "dst": "F6P",      "kcat": 1240.0},
        {"src": "F6P",     "dst": "FBP",      "kcat": 150.0},
        {"src": "FBP",     "dst": "G3P",      "kcat": 18.0},
        {"src": "G3P",     "dst": "BPG13",    "kcat": 130.0},
        {"src": "BPG13",   "dst": "3PG",      "kcat": 370.0},
        {"src": "3PG",     "dst": "2PG",      "kcat": 795.0},
        {"src": "2PG",     "dst": "PEP",      "kcat": 80.0},
        {"src": "PEP",     "dst": "Pyruvate", "kcat": 550.0},
    ]
    return species, reactions


def tca_data():
    """TCA cycle: KEGG hsa00020. 9 species, cyclic topology."""
    species = [
        {"id": "AcCoA",   "mu0": -374.0,  "conc": 0.06e-3},
        {"id": "Citrate", "mu0": -1166.0, "conc": 0.44e-3},
        {"id": "Isocit",  "mu0": -1160.0, "conc": 0.04e-3},
        {"id": "aKG",     "mu0": -798.0,  "conc": 0.03e-3},
        {"id": "SucCoA",  "mu0": -509.0,  "conc": 0.05e-3},
        {"id": "Succ",    "mu0": -690.0,  "conc": 0.30e-3},
        {"id": "Fum",     "mu0": -604.0,  "conc": 0.03e-3},
        {"id": "Malate",  "mu0": -842.0,  "conc": 0.22e-3},
        {"id": "OAA",     "mu0": -794.0,  "conc": 0.011e-3},
    ]
    reactions = [
        {"src": "AcCoA",   "dst": "Citrate", "kcat": 167.0},
        {"src": "Citrate", "dst": "Isocit",  "kcat": 30.0},
        {"src": "Isocit",  "dst": "aKG",     "kcat": 28.0},
        {"src": "aKG",     "dst": "SucCoA",  "kcat": 50.0},
        {"src": "SucCoA",  "dst": "Succ",    "kcat": 22.0},
        {"src": "Succ",    "dst": "Fum",     "kcat": 19.0},
        {"src": "Fum",     "dst": "Malate",  "kcat": 800.0},
        {"src": "Malate",  "dst": "OAA",     "kcat": 350.0},
        {"src": "OAA",     "dst": "AcCoA",   "kcat": 100.0},
    ]
    return species, reactions


def oxphos_data():
    """Oxidative phosphorylation: KEGG hsa00190. 8 species."""
    species = [
        {"id": "NADH",   "mu0": -1120.0, "conc": 0.08e-3},
        {"id": "Q",      "mu0": -280.0,  "conc": 0.30e-3},
        {"id": "QH2",    "mu0": -320.0,  "conc": 0.20e-3},
        {"id": "CytC_ox","mu0": -180.0,  "conc": 0.02e-3},
        {"id": "CytC_rd","mu0": -195.0,  "conc": 0.02e-3},
        {"id": "O2",     "mu0": 16.4,    "conc": 0.03e-3},
        {"id": "H2O",    "mu0": -237.0,  "conc": 55.0},
        {"id": "ATP",    "mu0": -2292.0, "conc": 3.0e-3},
    ]
    reactions = [
        {"src": "NADH",    "dst": "Q",       "kcat": 120.0},
        {"src": "Q",       "dst": "QH2",     "kcat": 200.0},
        {"src": "QH2",     "dst": "CytC_ox", "kcat": 90.0},
        {"src": "CytC_ox", "dst": "CytC_rd", "kcat": 300.0},
        {"src": "CytC_rd", "dst": "O2",      "kcat": 150.0},
        {"src": "O2",      "dst": "H2O",     "kcat": 400.0},
        {"src": "H2O",     "dst": "ATP",     "kcat": 100.0},
    ]
    return species, reactions


def egfr_data():
    """EGFR/MAPK signalling cascade: KEGG hsa04010. 9 species."""
    species = [
        {"id": "EGF",   "mu0": -120.0, "conc": 1.0e-9},
        {"id": "EGFR",  "mu0": -200.0, "conc": 2.0e-8},
        {"id": "pEGFR", "mu0": -215.0, "conc": 5.0e-9},
        {"id": "GRB2",  "mu0": -150.0, "conc": 1.0e-7},
        {"id": "SOS",   "mu0": -160.0, "conc": 5.0e-8},
        {"id": "RAS",   "mu0": -180.0, "conc": 4.0e-7},
        {"id": "RAF",   "mu0": -175.0, "conc": 1.0e-7},
        {"id": "MEK",   "mu0": -170.0, "conc": 4.0e-7},
        {"id": "ERK",   "mu0": -165.0, "conc": 9.0e-7},
    ]
    reactions = [
        {"src": "EGF",   "dst": "EGFR",  "kcat": 10.0},
        {"src": "EGFR",  "dst": "pEGFR", "kcat": 25.0},
        {"src": "pEGFR", "dst": "GRB2",  "kcat": 40.0},
        {"src": "GRB2",  "dst": "SOS",   "kcat": 35.0},
        {"src": "SOS",   "dst": "RAS",   "kcat": 60.0},
        {"src": "RAS",   "dst": "RAF",   "kcat": 55.0},
        {"src": "RAF",   "dst": "MEK",   "kcat": 70.0},
        {"src": "MEK",   "dst": "ERK",   "kcat": 85.0},
    ]
    return species, reactions


PATHWAYS = {
    "glycolysis": glycolysis_data,
    "tca": tca_data,
    "oxphos": oxphos_data,
    "egfr_mapk": egfr_data,
}


# ==========================================================================
#  Circuit solve -- paper equations (1)-(3)
# ==========================================================================

def compute_potentials(species):
    """eq (1):  mu_i = mu0_i + RT ln c_i."""
    for s in species:
        s["mu"] = s["mu0"] + RT * math.log(s["conc"])
    return species


def compute_conductances(species, reactions):
    """eq (2):  G_ij = kcat_ij c_i / RT."""
    by_id = {s["id"]: s for s in species}
    for r in reactions:
        r["conductance"] = r["kcat"] * by_id[r["src"]]["conc"] / RT
    return reactions


def compute_fluxes(species, reactions):
    """eq (3):  J_ij = G_ij (mu_i - mu_j)."""
    by_id = {s["id"]: s for s in species}
    for r in reactions:
        r["flux"] = r["conductance"] * (by_id[r["src"]]["mu"] - by_id[r["dst"]]["mu"])
    return reactions


def neighbour_table(species, reactions):
    """Undirected incidence: reverse edges carry negated flux, same conductance."""
    nb = {s["id"]: [] for s in species}
    for r in reactions:
        nb[r["src"]].append({"flux": r["flux"], "conductance": r["conductance"]})
        nb[r["dst"]].append({"flux": -r["flux"], "conductance": r["conductance"]})
    return nb


def compute_coordinates(species, reactions):
    """eq (4): normalise (flux total, conductance total, potential) into [0,1]^3."""
    nb = neighbour_table(species, reactions)

    flux_tot = {s["id"]: sum(abs(e["flux"]) for e in nb[s["id"]]) for s in species}
    cond_tot = {s["id"]: sum(e["conductance"] for e in nb[s["id"]]) for s in species}

    F_max = max(flux_tot.values()) or 1.0
    C_max = max(cond_tot.values()) or 1.0
    mus = [s["mu"] for s in species]
    mu_min, mu_max = min(mus), max(mus)
    mu_range = (mu_max - mu_min) or 1.0

    for s in species:
        s["Sk"] = flux_tot[s["id"]] / F_max
        s["St"] = cond_tot[s["id"]] / C_max
        s["Se"] = (s["mu"] - mu_min) / mu_range
    return species


def solve_circuit(species, reactions):
    """Full pipeline: mu -> G -> J -> (Sk,St,Se). Mutates and returns both."""
    compute_potentials(species)
    compute_conductances(species, reactions)
    compute_fluxes(species, reactions)
    compute_coordinates(species, reactions)
    return species, reactions


def load_pathway(name):
    """Fresh, fully solved copy of a named pathway."""
    species, reactions = PATHWAYS[name]()
    return solve_circuit(species, reactions)


def coord(s):
    return (s["Sk"], s["St"], s["Se"])


def contact_cost(s1, s2):
    """eq (5): Euclidean distance between node coordinates."""
    return math.sqrt(
        (s1["Sk"] - s2["Sk"]) ** 2
        + (s1["St"] - s2["St"]) ** 2
        + (s1["Se"] - s2["Se"]) ** 2
    )


# ==========================================================================
#  Ternary addressing -- Definitions 3.1, 3.2, 3.6; Proposition 3.5
# ==========================================================================

def trits(x, m):
    """Definition 3.1: first m trits of x in [0,1]. x == 1 maps to all 2s."""
    if x >= 1.0:
        return [2] * m
    if x < 0.0:
        x = 0.0
    out = []
    for r in range(1, m + 1):
        out.append(int(math.floor((3 ** r) * x)) % 3)
    return out


def addr_k(point, k):
    """
    Definition 3.2 / eq (6): interleaved base-3 address.

    k must be a multiple of 3; m = k/3 trits are taken from each of the
    three axes and interleaved (Sk, St, Se, Sk, St, Se, ...).
    """
    if k % 3 != 0:
        raise ValueError("address length k must be a multiple of 3")
    m = k // 3
    tk = trits(point[0], m)
    tt = trits(point[1], m)
    te = trits(point[2], m)
    out = []
    for r in range(m):
        out.extend((tk[r], tt[r], te[r]))
    return tuple(out)


def parent(address):
    """Proposition 3.5(i): parent = drop the last symbol."""
    return address[:-1]


def steps_to_root(address):
    """
    Proposition 3.5(ii): step count IS the address length.

    Deliberately written as len(): the claim under test is that no traversal
    is performed, so the implementation must not perform one.
    """
    return len(address)


def walk_to_root(address):
    """Explicit ancestor chain -- used only to check it agrees with len()."""
    steps = 0
    a = address
    while len(a) > 0:
        a = parent(a)
        steps += 1
    return steps


def lcp(a, b):
    """Longest common prefix length."""
    n = 0
    for x, y in zip(a, b):
        if x != y:
            break
        n += 1
    return n


def similarity(u_addrs, v_addrs, k):
    """Definition 3.6 / eq (7): mean normalised LCP over paired parts."""
    n = len(u_addrs)
    if n == 0:
        return 0.0
    return sum(lcp(a, b) for a, b in zip(u_addrs, v_addrs)) / (n * k)


# ==========================================================================
#  Result IO
# ==========================================================================

def ensure_output_dir():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    return OUTPUT_DIR


def save_result(result, filename):
    ensure_output_dir()
    path = os.path.join(OUTPUT_DIR, filename)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False, default=str)
    return path


def utc_stamp():
    return datetime.now(timezone.utc).isoformat()


def verdict(passed):
    return "PASS" if passed else "FAIL"

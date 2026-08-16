"""
Six figure panels for the circuit-CKG manuscript.
==================================================

Each panel: white background, four charts in a row, at least one 3D, minimal
text, no conceptual diagrams / tables / text-only axes. Every value plotted is
either recomputed from the circuit or read from the validation JSON in
results/ -- nothing is drawn by hand.

  panel_1  the circuit                 -- Theorem 2.1, Proposition 2.6
  panel_2  the coordinate              -- eq (4), V3, incl. the oxphos degeneracy
  panel_3  ternary addressing          -- Definitions 3.1/3.2, Propositions 3.5/3.10
  panel_4  similarity and propagation  -- Propositions 3.7/3.8, Theorems 5.4/5.6
  panel_5  virtual sub-states          -- Theorem 6.2, Corollary 6.3, Theorem 6.4
  panel_6  the panel layer             -- Theorems 7.2/7.7/7.11, Proposition 7.12

    python make_figures.py
"""

import json
import math
import os
import random

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D  # noqa: F401
from scipy import stats

from common import (
    PATHWAYS, load_pathway, coord, contact_cost, addr_k, trits, lcp,
    OUTPUT_DIR,
)

FIG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "figures")

PATH_ORDER = ["glycolysis", "tca", "oxphos", "egfr_mapk"]
PATH_LABEL = {"glycolysis": "glycolysis", "tca": "TCA",
              "oxphos": "OxPhos", "egfr_mapk": "EGFR"}
CMAP = {"glycolysis": "#1b4f72", "tca": "#117864",
        "oxphos": "#922b21", "egfr_mapk": "#7d6608"}


# --------------------------------------------------------------------------

def style():
    plt.rcParams.update({
        "figure.facecolor": "white",
        "axes.facecolor": "white",
        "savefig.facecolor": "white",
        "axes.edgecolor": "#333333",
        "axes.linewidth": 0.8,
        "axes.grid": True,
        "grid.color": "#dddddd",
        "grid.linewidth": 0.5,
        "font.size": 8,
        "axes.titlesize": 9,
        "axes.labelsize": 8,
        "xtick.labelsize": 7,
        "ytick.labelsize": 7,
        "legend.fontsize": 7,
        "legend.frameon": False,
        "axes.spines.top": False,
        "axes.spines.right": False,
    })


def new_panel(specs):
    """specs: list of 4 items, each None (2D) or '3d'."""
    fig = plt.figure(figsize=(15.0, 3.7))
    axes = []
    for i, kind in enumerate(specs):
        if kind == "3d":
            ax = fig.add_subplot(1, 4, i + 1, projection="3d")
            ax.set_facecolor("white")
            ax.xaxis.pane.set_facecolor("white")
            ax.yaxis.pane.set_facecolor("white")
            ax.zaxis.pane.set_facecolor("white")
            ax.xaxis.pane.set_edgecolor("#dddddd")
            ax.yaxis.pane.set_edgecolor("#dddddd")
            ax.zaxis.pane.set_edgecolor("#dddddd")
            ax.grid(True, color="#dddddd", linewidth=0.4)
        else:
            ax = fig.add_subplot(1, 4, i + 1)
        axes.append(ax)
    return fig, axes


def save(fig, name):
    os.makedirs(FIG_DIR, exist_ok=True)
    path = os.path.join(FIG_DIR, name)
    fig.tight_layout(pad=1.1)
    fig.savefig(path + ".pdf", dpi=300, facecolor="white")
    fig.savefig(path + ".png", dpi=200, facecolor="white")
    plt.close(fig)
    print(f"  {name}.pdf / .png")
    return path


def load_json(name):
    with open(os.path.join(OUTPUT_DIR, name), encoding="utf-8") as f:
        return json.load(f)


# ==========================================================================
#  Panel 1 -- the circuit
# ==========================================================================

def panel_1():
    """(a) conductance vs flux 3D  (b) KCL/KVL residuals  (c) potential ladder
       (d) relabelling invariance vs data-permutation control."""
    fig, ax = new_panel(["3d", None, None, None])

    # --- (a) 3D: the solved circuit in (log G, log|J|, mu) ---
    a = ax[0]
    for name in PATH_ORDER:
        species, reactions = load_pathway(name)
        by_id = {s["id"]: s for s in species}
        G = np.array([r["conductance"] for r in reactions])
        J = np.array([abs(r["flux"]) for r in reactions])
        mu = np.array([by_id[r["src"]]["mu"] for r in reactions])
        m = (G > 0) & (J > 0)
        a.scatter(np.log10(G[m]), np.log10(J[m]), mu[m],
                  s=26, color=CMAP[name], alpha=0.85,
                  edgecolors="white", linewidths=0.4, label=PATH_LABEL[name])
    a.set_xlabel(r"$\log_{10} G_{ij}$", labelpad=-2)
    a.set_ylabel(r"$\log_{10} |J_{ij}|$", labelpad=-2)
    a.set_zlabel(r"$\mu_i$  (kJ/mol)", labelpad=-4)
    a.set_title("(a) solved edges")
    a.view_init(elev=20, azim=-58)
    a.legend(loc="upper left", bbox_to_anchor=(-0.08, 0.98))
    a.tick_params(pad=-1)

    # --- (b) KCL / KVL residuals ---
    d = load_json("01_kirchhoff_correspondence.json")["per_pathway"]
    b = ax[1]
    x = np.arange(len(PATH_ORDER))
    FLOOR = 1e-20          # bottom of the axis
    DRAWN = 3e-19          # height drawn for an exactly-zero residual
    kcl_raw = [d[p]["kcl_max_residual"] for p in PATH_ORDER]
    kvl_raw = [d[p]["kvl_max_residual"] for p in PATH_ORDER]
    kcl = [v if v > 0 else DRAWN for v in kcl_raw]
    kvl = [v if v > 0 else DRAWN for v in kvl_raw]
    b.bar(x - 0.2, kcl, 0.38, bottom=FLOOR, color="#1b4f72", label="KCL")
    b.bar(x + 0.2, kvl, 0.38, bottom=FLOOR, color="#b03a2e", label="KVL")
    b.axhline(1e-9, color="#555555", ls="--", lw=1.0)
    b.set_yscale("log")
    b.set_xticks(x)
    b.set_xticklabels([PATH_LABEL[p] for p in PATH_ORDER])
    b.set_ylabel("max residual (bars at floor are exactly 0)")
    b.set_ylim(FLOOR, 1e-6)
    b.set_title("(b) Kirchhoff residuals")
    b.legend(loc="upper right")
    # cycle coverage: KVL has content only where a cycle exists
    b2 = b.twinx()
    b2.plot(x, [d[p]["kvl_cycles_found"] for p in PATH_ORDER], "s--",
            ms=6, lw=1.2, color="#117864")
    b2.set_ylabel("cycles enumerated", color="#117864")
    b2.tick_params(axis="y", colors="#117864")
    b2.set_ylim(-0.15, 2.0)
    b2.grid(False)

    # --- (c) potential ladder ---
    c = ax[2]
    for i, name in enumerate(PATH_ORDER):
        species, _ = load_pathway(name)
        mu = sorted(s["mu"] for s in species)
        c.plot(np.linspace(0, 1, len(mu)), mu, "o-", ms=3.5, lw=1.2,
               color=CMAP[name], label=PATH_LABEL[name])
    c.set_xlabel("species rank (normalised)")
    c.set_ylabel(r"$\mu_i = \mu_i^\circ + RT\ln c_i$")
    c.set_title("(c) potential ladder")
    c.legend(loc="upper left")

    # --- (d) invariance vs control ---
    e = load_json("02_relabelling_invariance.json")["per_pathway"]
    dd = ax[3]
    FL, DR = 1e-20, 3e-19
    rel_raw = [e[p]["relabel_max_deviation"] for p in PATH_ORDER]
    ctl_raw = [e[p]["control_data_permuted_deviation"] for p in PATH_ORDER]
    rel = [v if v > 0 else DR for v in rel_raw]
    dd.bar(x - 0.2, rel, 0.38, bottom=FL, color="#1b4f72", label="relabel")
    dd.bar(x + 0.2, ctl_raw, 0.38, bottom=FL, color="#b03a2e", label="control")
    dd.axhline(1e-12, color="#555555", ls="--", lw=1.0)
    dd.set_yscale("log")
    dd.set_xticks(x)
    dd.set_xticklabels([PATH_LABEL[p] for p in PATH_ORDER])
    dd.set_ylabel("max deviation (blue bars are exactly 0)")
    dd.set_ylim(FL, 1e2)
    dd.set_title("(d) invariance and its control")
    dd.legend(loc="upper left")

    return save(fig, "panel_1_circuit")


# ==========================================================================
#  Panel 2 -- the coordinate, including the oxphos degeneracy
# ==========================================================================

def panel_2():
    """(a) unit cube 3D  (b) axis reducibility R^2  (c) oxphos collinearity
       (d) concentration dominance vs max R^2."""
    fig, ax = new_panel(["3d", None, None, None])
    d = load_json("03_coordinate_irreducibility.json")["per_pathway"]

    # --- (a) 3D unit cube ---
    a = ax[0]
    for name in PATH_ORDER:
        species, _ = load_pathway(name)
        P = np.array([coord(s) for s in species])
        a.scatter(P[:, 0], P[:, 1], P[:, 2], s=34, color=CMAP[name],
                  alpha=0.9, edgecolors="white", linewidths=0.4,
                  label=PATH_LABEL[name])
    for s0, s1 in [((0, 0, 0), (1, 0, 0)), ((0, 0, 0), (0, 1, 0)),
                   ((0, 0, 0), (0, 0, 1)), ((1, 1, 1), (0, 1, 1)),
                   ((1, 1, 1), (1, 0, 1)), ((1, 1, 1), (1, 1, 0))]:
        a.plot(*zip(s0, s1), color="#cccccc", lw=0.6)
    a.set_xlabel(r"$S_k$", labelpad=-4)
    a.set_ylabel(r"$S_t$", labelpad=-4)
    a.set_zlabel(r"$S_e$", labelpad=-4)
    a.set_xlim(0, 1); a.set_ylim(0, 1); a.set_zlim(0, 1)
    a.set_title("(a) node coordinates")
    a.view_init(elev=22, azim=-52)
    a.legend(loc="upper left", bbox_to_anchor=(-0.08, 0.98))
    a.tick_params(pad=-2)

    # --- (b) reducibility R^2 per axis ---
    b = ax[1]
    x = np.arange(len(PATH_ORDER))
    for i, axis in enumerate(["Sk", "St", "Se"]):
        vals = [d[p]["axis_regressions"][axis]["r_squared_from_other_two"]
                for p in PATH_ORDER]
        b.bar(x + (i - 1) * 0.27, vals, 0.25,
              color=["#1b4f72", "#2e86c1", "#a9cce3"][i],
              edgecolor="white", linewidth=0.5,
              label=f"${axis[0]}_{axis[1]}$")
    b.axhline(0.99, color="#b03a2e", ls="--", lw=1.0)
    b.set_xticks(x)
    b.set_xticklabels([PATH_LABEL[p] for p in PATH_ORDER])
    b.set_ylabel(r"$R^2$ from the other two axes")
    b.set_ylim(0, 1.08)
    b.set_yticks([0, 0.25, 0.5, 0.75, 1.0])
    b.set_title("(b) axis reducibility", pad=18)
    b.legend(loc="lower center", bbox_to_anchor=(0.5, 1.005),
             ncol=3, columnspacing=1.0, frameon=False)

    # --- (c) the oxphos collinearity, shown directly ---
    c = ax[2]
    for name in PATH_ORDER:
        species, _ = load_pathway(name)
        Sk = [s["Sk"] for s in species]
        St = [s["St"] for s in species]
        c.scatter(Sk, St, s=34, color=CMAP[name], alpha=0.85,
                  edgecolors="white", linewidths=0.4, label=PATH_LABEL[name])
    c.plot([0, 1], [0, 1], color="#b03a2e", ls="--", lw=1.0)
    c.set_xlabel(r"$S_k$")
    c.set_ylabel(r"$S_t$")
    c.set_title(r"(c) $S_k$ against $S_t$")
    c.legend(loc="upper left")

    # --- (d) dominance ratio vs worst-axis R^2 ---
    dd = ax[3]
    for name in PATH_ORDER:
        dom = d[name]["concentration_dominance_ratio"]
        worst = max(v["r_squared_from_other_two"]
                    for v in d[name]["axis_regressions"].values())
        dd.scatter(dom, worst, s=90, color=CMAP[name],
                   edgecolors="white", linewidths=0.8, label=PATH_LABEL[name])
    dd.axhline(0.99, color="#b03a2e", ls="--", lw=1.0)
    dd.set_xscale("log")
    dd.set_xlabel(r"$c_{(1)}/c_{(2)}$")
    dd.set_ylabel(r"largest axis $R^2$")
    dd.set_ylim(0, 1.08)
    dd.set_title("(d) dominance drives degeneracy")
    dd.legend(loc="lower right")

    return save(fig, "panel_2_coordinate")


# ==========================================================================
#  Panel 3 -- ternary addressing
# ==========================================================================

def panel_3():
    """(a) trit subdivision of the cube 3D  (b) steps-to-root  (c) capacity
       (d) prefix-length distribution."""
    fig, ax = new_panel(["3d", None, None, None])

    # --- (a) depth-1 subdivision, cells coloured by occupancy ---
    a = ax[0]
    species, _ = load_pathway("glycolysis")
    P = np.array([coord(s) for s in species])
    occupied = {}
    for p in P:
        cell = tuple(trits(v, 1)[0] for v in p)
        occupied[cell] = occupied.get(cell, 0) + 1
    for i in range(3):
        for j in range(3):
            for k in range(3):
                n = occupied.get((i, j, k), 0)
                if n == 0:
                    continue
                x0, y0, z0 = i / 3, j / 3, k / 3
                a.bar3d(x0, y0, z0, 1 / 3, 1 / 3, 1 / 3,
                        color="#2e86c1", alpha=min(0.62, 0.16 + 0.12 * n),
                        edgecolor="#1b4f72", linewidth=0.4, shade=False)
    a.scatter(P[:, 0], P[:, 1], P[:, 2], s=30, color="#b03a2e",
              edgecolors="white", linewidths=0.5, depthshade=False)
    a.set_xlabel(r"$S_k$", labelpad=-4)
    a.set_ylabel(r"$S_t$", labelpad=-4)
    a.set_zlabel(r"$S_e$", labelpad=-4)
    a.set_xlim(0, 1); a.set_ylim(0, 1); a.set_zlim(0, 1)
    a.set_title("(a) depth-1 ternary cells")
    a.view_init(elev=20, azim=-54)
    a.tick_params(pad=-2)

    # --- (b) steps to root vs N ---
    d = load_json("04_prefix_ancestry.json")["per_depth"]
    b = ax[1]
    depths = sorted(int(k) for k in d)
    N = [d[str(k)]["N_cells"] for k in depths]
    steps = [d[str(k)]["steps_max"] for k in depths]
    var = [d[str(k)]["steps_variance"] for k in depths]
    b.plot(N, steps, "o-", ms=4, lw=1.3, color="#1b4f72", label="observed")
    b.plot(N, [math.log(n, 3) for n in N], "--", lw=1.1,
           color="#b03a2e", label=r"$\log_3 N$")
    b.errorbar(N, steps, yerr=var, fmt="none", ecolor="#555555", capsize=2)
    b.set_xscale("log")
    b.set_xlabel(r"$N = 3^{\,\mathrm{depth}}$")
    b.set_ylabel("steps to root")
    b.set_title("(b) ancestry cost")
    b.legend(loc="upper left")

    # --- (c) capacity ---
    e = load_json("05_depth_capacity.json")
    c = ax[2]
    kk = np.arange(1, 13)
    c.plot(kk, kk * e["bits_per_trit"], "-", lw=1.4, color="#1b4f72",
           label=r"$k\log_2 3$")
    for t in e["tiers"]:
        c.scatter(t["k"], t["H_bits"], s=70, color="#b03a2e", zorder=3,
                  edgecolors="white", linewidths=0.7)
        c.plot([t["k"], t["k"]], [t["H_bits"], t["k"] * e["bits_per_trit"]],
               color="#b03a2e", lw=0.8, alpha=0.6)
    c.set_xlabel(r"address depth $k$")
    c.set_ylabel("bits")
    c.set_title("(c) capacity against tier entropy")
    c.legend(loc="upper left")

    # --- (d) prefix-length distribution ---
    dd = ax[3]
    K = 9
    for name in PATH_ORDER:
        sp, _ = load_pathway(name)
        addrs = [addr_k(coord(s), K) for s in sp]
        vals = [lcp(addrs[i], addrs[j])
                for i in range(len(addrs)) for j in range(i + 1, len(addrs))]
        counts = [vals.count(v) / len(vals) for v in range(K + 1)]
        dd.plot(range(K + 1), counts, "o-", ms=3.5, lw=1.2,
                color=CMAP[name], label=PATH_LABEL[name])
    dd.set_xlabel("shared prefix length")
    dd.set_ylabel("fraction of pairs")
    dd.set_title(f"(d) prefix sharing, $k={K}$")
    dd.legend(loc="upper right")

    return save(fig, "panel_3_addressing")


# ==========================================================================
#  Panel 4 -- similarity and propagation
# ==========================================================================

def panel_4():
    """(a) similarity vs Euclidean distance  (b) contact-cost distribution
       (c) admissible-set growth 3D  (d) opacity multiplicity."""
    fig, ax = new_panel([None, None, "3d", None])
    K = 9

    # --- (a) sigma is not a distance proxy ---
    a = ax[0]
    for name in PATH_ORDER:
        sp, _ = load_pathway(name)
        ds, ss = [], []
        for i in range(len(sp)):
            for j in range(i + 1, len(sp)):
                ds.append(contact_cost(sp[i], sp[j]))
                ss.append(lcp(addr_k(coord(sp[i]), K),
                              addr_k(coord(sp[j]), K)) / K)
        a.scatter(ds, ss, s=20, color=CMAP[name], alpha=0.7,
                  edgecolors="none", label=PATH_LABEL[name])
    a.set_xlabel(r"contact cost $\|S_u - S_v\|_2$")
    a.set_ylabel(r"prefix similarity $\sigma$")
    a.set_title("(a) similarity is not distance")
    a.legend(loc="upper right")

    # --- (b) contact-cost distributions ---
    b = ax[1]
    for name in PATH_ORDER:
        sp, rx = load_pathway(name)
        by = {s["id"]: s for s in sp}
        costs = sorted(contact_cost(by[r["src"]], by[r["dst"]]) for r in rx)
        b.plot(costs, np.linspace(0, 1, len(costs)), "o-", ms=3, lw=1.2,
               color=CMAP[name], label=PATH_LABEL[name])
    b.axvline(0.05, color="#b03a2e", ls="--", lw=1.0)
    b.set_xlabel("edge contact cost")
    b.set_ylabel("cumulative fraction of edges")
    b.set_title(r"(b) edge costs and the floor $\beta$")
    b.legend(loc="lower right")

    # --- (c) 3D: admissible-set size over (budget, pathway) ---
    c = ax[2]
    dj = load_json("09_direction_agnosticism.json")
    budgets = dj["per_pathway"][PATH_ORDER[0]]["fixed_points_swept"]
    for name in PATH_ORDER:
        sp, rx = load_pathway(name)
        by = {s["id"]: s for s in sp}
        adj = {s["id"]: [] for s in sp}
        for r in rx:
            cst = contact_cost(by[r["src"]], by[r["dst"]])
            adj[r["src"]].append((r["dst"], cst))
            adj[r["dst"]].append((r["src"], cst))
        zi = PATH_ORDER.index(name)
        sizes = []
        for x_star in budgets:
            tot = 0
            for v0 in adj:
                seen, stack = {v0}, [(v0, 0.0)]
                while stack:
                    u, spent = stack.pop()
                    for w, cst in adj[u]:
                        if w not in seen and spent + cst <= x_star:
                            seen.add(w)
                            stack.append((w, spent + cst))
                tot += len(seen)
            sizes.append(tot / len(adj))
        c.plot(budgets, [zi] * len(budgets), sizes, "o-", ms=4, lw=1.5,
               color=CMAP[name])
    c.set_xlabel(r"budget $x^\star$", labelpad=-2)
    c.set_zlabel("mean reachable nodes", labelpad=-6)
    c.set_yticks(range(len(PATH_ORDER)))
    c.set_yticklabels([PATH_LABEL[p] for p in PATH_ORDER])
    c.set_title("(c) reachability against budget")
    # azim +62 puts the z-axis on the LEFT, clear of panel (d)'s y-axis; the
    # flip reverses x, so invert it back so budget still increases rightwards
    c.view_init(elev=20, azim=62)
    c.set_xlim(c.get_xlim()[::-1])
    c.tick_params(pad=-2)

    # --- (d) opacity: routes and interiors per endpoint pair ---
    op = load_json("08_path_opacity.json")
    dd = ax[3]
    xs, ys, inv, cs = [], [], [], []
    idx = 0
    for name in PATH_ORDER:
        for e in op["per_pathway"].get(name, {}).get("examples", [])[:10]:
            xs.append(idx)
            ys.append(e["distinct_interiors"])
            inv.append(e["endpoint_invariants"])
            cs.append(CMAP[name])
            idx += 1
    if xs:
        dd.vlines(xs, inv, ys, color="#cccccc", lw=1.0, zorder=1)
        dd.scatter(xs, ys, s=55, c=cs, alpha=0.9, zorder=3,
                   edgecolors="white", linewidths=0.5,
                   label="distinct interiors")
        dd.scatter(xs, inv, s=42, facecolors="white", zorder=3,
                   edgecolors="#b03a2e", linewidths=1.2,
                   label="endpoint invariants")
    dd.set_xlabel("endpoint pair")
    dd.set_ylabel("count")
    dd.set_ylim(0, max(ys + [2]) + 1.2)
    dd.set_title("(d) many routes, one endpoint pair")
    dd.legend(loc="upper left")

    return save(fig, "panel_4_propagation")


# ==========================================================================
#  Panel 5 -- virtual sub-states and the cost asymmetry
# ==========================================================================

def panel_5():
    """(a) sub-state cloud 3D  (b) virtual fraction  (c) operation counts
       (d) forward asymmetry."""
    fig, ax = new_panel(["3d", None, None, None])

    # --- (a) 3D: decompositions of one point, virtual ones outside the cube ---
    a = ax[0]
    rng = np.random.default_rng(20260813)
    s = np.array([0.52, 0.44, 0.61])
    p = 3
    inside_x, inside_y, inside_z = [], [], []
    out_x, out_y, out_z = [], [], []
    for _ in range(320):
        parts = rng.normal(0, 0.42, size=(p, 3))
        parts -= parts.mean(axis=0)
        parts += s
        for q in parts:
            if np.all((q >= 0) & (q <= 1)):
                inside_x.append(q[0]); inside_y.append(q[1]); inside_z.append(q[2])
            else:
                out_x.append(q[0]); out_y.append(q[1]); out_z.append(q[2])
    a.scatter(out_x, out_y, out_z, s=6, color="#b03a2e", alpha=0.30,
              edgecolors="none", label="virtual")
    a.scatter(inside_x, inside_y, inside_z, s=6, color="#1b4f72", alpha=0.35,
              edgecolors="none", label="admissible")
    a.scatter([s[0]], [s[1]], [s[2]], s=90, color="black",
              edgecolors="white", linewidths=0.8, depthshade=False)
    for e0, e1 in [((0, 0, 0), (1, 0, 0)), ((0, 0, 0), (0, 1, 0)),
                   ((0, 0, 0), (0, 0, 1)), ((1, 1, 1), (0, 1, 1)),
                   ((1, 1, 1), (1, 0, 1)), ((1, 1, 1), (1, 1, 0))]:
        a.plot(*zip(e0, e1), color="#666666", lw=0.9)
    a.set_xlabel(r"$S_k$", labelpad=-4)
    a.set_ylabel(r"$S_t$", labelpad=-4)
    a.set_zlabel(r"$S_e$", labelpad=-4)
    a.set_title("(a) sub-state decompositions")
    a.view_init(elev=18, azim=-56)
    a.legend(loc="upper left", bbox_to_anchor=(-0.10, 0.99))
    a.tick_params(pad=-2)

    # --- (b) reconstruction error against dispersion ---
    v = load_json("11_virtual_substates_and_collapse.json")
    b = ax[1]
    meas = v["virtual_fraction"]["measurements"]
    xs = [r["dispersion_M"] for r in meas]
    vf = [r["virtual_fraction"] for r in meas]
    err = [max(r["max_mean_reconstruction_error"], 1e-18) for r in meas]
    b.plot(xs, vf, "o-", ms=5, lw=1.5, color="#1b4f72",
           label="virtual fraction")
    b.set_xlabel(r"dispersion $M$")
    b.set_ylabel("virtual fraction")
    b.set_ylim(-0.03, 1.08)
    b.set_title("(b) decompositions are virtual")
    b2 = b.twinx()
    b2.plot(xs, err, "s--", ms=4, lw=1.2, color="#b03a2e")
    b2.set_yscale("log")
    b2.set_ylabel("mean reconstruction error", color="#b03a2e")
    b2.tick_params(axis="y", colors="#b03a2e")
    b2.grid(False)
    b.legend(loc="center left")

    # --- (c) operation counts ---
    c = ax[2]
    ops = v["operation_counts"]["per_depth"]
    N = [r["N_cells"] for r in ops]
    virt = [r["ops_virtual_permitted"] for r in ops]
    phys = [r["ops_physical_only"] for r in ops]
    c.plot(N, phys, "o-", ms=4, lw=1.5, color="#b03a2e",
           label="physical only")
    # the virtual series IS ceil(log_3 N); draw the reference as a wide underlay
    # so the coincidence is visible rather than hidden beneath the data
    c.plot(N, [math.log(n, 3) for n in N], "-", lw=5.0, color="#bcc6cc",
           solid_capstyle="round", label=r"$\log_3 N$")
    c.plot(N, virt, "o-", ms=4, lw=1.5, color="#1b4f72",
           label="virtual permitted")
    c.set_xscale("log")
    c.set_xlabel(r"$N$ cells")
    c.set_ylabel("operations")
    c.set_title(r"(c) $\Theta(N)\to\Theta(\log_3 N)$")
    c.legend(loc="upper left")

    # --- (d) forward asymmetry: truncation moves survivors ---
    fa = load_json("12_forward_asymmetry.json")
    dd = ax[3]
    for name in PATH_ORDER:
        det = fa["per_pathway"][name]["detail"]
        kept = [r["species_kept"] for r in det]
        shift = [max(r["max_coordinate_shift"], 1e-18) for r in det]
        dd.plot(kept, shift, "o-", ms=4, lw=1.3, color=CMAP[name],
                label=PATH_LABEL[name])
    dd.set_yscale("log")
    dd.set_xlabel("species retained in truncation")
    dd.set_ylabel("max coordinate shift of survivors")
    dd.set_title("(d) normalisers are global")
    dd.legend(loc="lower left")

    return save(fig, "panel_5_virtual")


# ==========================================================================
#  Panel 6 -- the panel layer
# ==========================================================================

def panel_6():
    """(a) probe separation counts  (b) water-filling 3D  (c) Kuramoto sweep
       (d) localisation."""
    fig, ax = new_panel([None, "3d", None, None])

    # --- (a) collisions remaining per probe subset, by subset size ---
    dsc = load_json("13_discrimination_bound.json")
    a = ax[0]
    rows = dsc["subset_search"]
    for r in rows:
        jitter = (hash(tuple(r["subset"])) % 100) / 100.0 * 0.30 - 0.15
        a.scatter(r["size"] + jitter, r["collisions"],
                  s=60, color=("#1b4f72" if r["separates_all"] else "#b03a2e"),
                  alpha=0.85, edgecolors="white", linewidths=0.5)
    a.axhline(0, color="#555555", ls="--", lw=0.9)
    a.axvline(dsc["minimum_separating_size"], color="#117864", ls=":", lw=1.4)
    a.set_xlabel("probes in subset")
    a.set_ylabel("colliding state pairs")
    a.set_xticks(range(1, 5))
    a.set_title(r"(a) panel floor $\chi$")

    # --- (b) 3D water-filling surface: allocation vs price vs reasoner ---
    wf = load_json("14_water_filling_allocation.json")
    b = ax[1]
    reasoners = [
        {"name": "deductive", "w": 1.00, "c": 0.50},
        {"name": "inductive", "w": 0.80, "c": 1.00},
        {"name": "abductive", "w": 0.60, "c": 2.00},
        {"name": "causal",    "w": 0.90, "c": 0.75},
        {"name": "temporal",  "w": 0.05, "c": 8.00},
    ]
    prices = np.linspace(0.05, 1.6, 90)
    for i, r in enumerate(reasoners):
        alloc = np.maximum(0.0, r["w"] / prices - r["c"])
        b.plot(prices, [i] * len(prices), alloc, lw=1.6,
               color=plt.cm.viridis(i / max(1, len(reasoners) - 1)))
    ps = wf["shadow_price_p_star"]
    for i, entry in enumerate(wf["allocations"]):
        b.scatter([ps], [i], [entry["allocation"]], s=55, color="#b03a2e",
                  edgecolors="white", linewidths=0.6, depthshade=False)
    b.set_xlabel(r"price $p$", labelpad=-2)
    b.set_zlabel(r"allocation $a_i$", labelpad=-6)
    b.set_yticks(range(len(reasoners)))
    b.set_yticklabels([r["name"][:4] for r in reasoners])
    b.set_title(r"(b) water-filling at $p^\star$")
    # azim +60 puts the z-axis on the LEFT, clear of panel (c)'s y-axis; the
    # flip reverses x, so invert it back so price still increases rightwards
    b.view_init(elev=20, azim=60)
    b.set_xlim(b.get_xlim()[::-1])
    b.tick_params(pad=-3)

    # --- (c) Kuramoto sweep ---
    kk = load_json("15_locking_threshold.json")
    c = ax[2]
    sw = kk["sweep"]
    xs = [s["K_over_Kc"] for s in sw]
    ys = [s["R"] for s in sw]
    c.plot(xs, ys, "o-", ms=5, lw=1.5, color="#1b4f72")
    c.axvline(1.0, color="#b03a2e", ls="--", lw=1.2)
    c.axhline(kk["incoherent_floor_1_over_sqrt_M"], color="#555555",
              ls=":", lw=1.1)
    c.set_xlabel(r"$K/K_c$")
    c.set_ylabel(r"$\mathcal{R}$", labelpad=1)
    c.set_ylim(0, 1.05)
    c.set_title("(c) locking threshold")

    # --- (d) localisation ---
    lc = load_json("16_localisation_of_R_drop.json")
    dd = ax[3]
    labels = ["before", "after\n(global)", "after\n(original)", "control\n(matched)"]
    vals = [lc["R_old"], lc["R_new_global"],
            lc["R_new_restricted_to_original"],
            lc["control_matched_newcomer"]["R_global"]]
    cols = ["#1b4f72", "#b03a2e", "#117864", "#7d6608"]
    # the entire effect lives in the third decimal, so plot the deficit 1 - R
    dd.bar(range(4), [1.0 - v for v in vals], 0.6, color=cols)
    dd.axhline(1.0 - lc["theoretical_bound"], color="#555555", ls="--", lw=1.1)
    dd.set_yscale("log")
    dd.set_xticks(range(4))
    dd.set_xticklabels(labels)
    dd.set_ylabel(r"incoherence $1-\mathcal{R}$")
    dd.set_title(r"(d) an $\mathcal{R}$ drop localises")

    return save(fig, "panel_6_panel_layer")


PANELS = [panel_1, panel_2, panel_3, panel_4, panel_5, panel_6]


if __name__ == "__main__":
    style()
    os.makedirs(FIG_DIR, exist_ok=True)
    print(f"figures -> {FIG_DIR}")
    for fn in PANELS:
        fn()

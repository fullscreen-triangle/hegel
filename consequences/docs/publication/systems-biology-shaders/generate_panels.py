"""
Generate 5 publication panels for the Systems Biology Shaders paper.
Each panel: white background, 4 charts in a row, at least one 3D chart.
"""

import json
import math
import os
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from matplotlib import cm
from matplotlib.colors import Normalize

OUT = os.path.dirname(os.path.abspath(__file__))

# Load data
with open(os.path.join(OUT, "experiment_1_shell_capacity.json")) as f:
    exp1 = json.load(f)
with open(os.path.join(OUT, "experiment_2_spectral_reconstruction.json")) as f:
    exp2 = json.load(f)
with open(os.path.join(OUT, "experiment_3_disease_detection.json")) as f:
    exp3 = json.load(f)
with open(os.path.join(OUT, "experiment_4_therapeutic_score.json")) as f:
    exp4 = json.load(f)

ACCENT = "#2563EB"
ACCENT2 = "#F59E0B"
ACCENT3 = "#10B981"
ACCENT4 = "#EF4444"
GRAY = "#6B7280"
LIGHT = "#E5E7EB"

plt.rcParams.update({
    "font.family": "sans-serif",
    "font.size": 9,
    "axes.titlesize": 10,
    "axes.titleweight": "bold",
    "axes.spines.top": False,
    "axes.spines.right": False,
    "figure.facecolor": "white",
    "axes.facecolor": "white",
    "savefig.facecolor": "white",
    "savefig.dpi": 300,
    "savefig.bbox": "tight",
})


# ═══════════════════════════════════════════════════════════════
#  PANEL 1: Partition Shell Structure
# ═══════════════════════════════════════════════════════════════

def panel_1():
    fig = plt.figure(figsize=(20, 4.5))

    # 1a — Shell capacity C(n) = 2n²
    ax1 = fig.add_subplot(1, 4, 1)
    ns = [s["n"] for s in exp1["shells"]]
    Cn = [s["C_n_formula"] for s in exp1["shells"]]
    bars = ax1.bar(ns, Cn, color=ACCENT, edgecolor="white", linewidth=0.5, zorder=3)
    for bar, c in zip(bars, Cn):
        ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1.5,
                 str(c), ha="center", va="bottom", fontsize=8, color="#374151")
    ax1.set_xlabel("Principal quantum number n")
    ax1.set_ylabel("Shell capacity C(n)")
    ax1.set_title("C(n) = 2n²")
    ax1.set_xticks(ns)
    ax1.grid(axis="y", alpha=0.3, zorder=0)

    # 1b — 3D subshell decomposition
    ax2 = fig.add_subplot(1, 4, 2, projection="3d")
    bar_n, bar_l, bar_h, bar_c = [], [], [], []
    cmap = cm.viridis
    for shell in exp1["shells"]:
        n = shell["n"]
        for sub in shell["breakdown"]:
            l_val = sub["l"]
            count = sub["subtotal"]
            bar_n.append(n)
            bar_l.append(l_val)
            bar_h.append(count)
            bar_c.append(cmap(l_val / 7.0))

    ax2.bar3d(bar_n, bar_l, [0]*len(bar_n), 0.6, 0.6, bar_h,
              color=bar_c, alpha=0.85, edgecolor="white", linewidth=0.3)
    ax2.set_xlabel("n", labelpad=8)
    ax2.set_ylabel("l", labelpad=8)
    ax2.set_zlabel("States", labelpad=8)
    ax2.set_title("Subshell 2(2l+1)")
    ax2.view_init(elev=25, azim=-50)

    # 1c — Cumulative capacity with noble gases
    ax3 = fig.add_subplot(1, 4, 3)
    cums = [s["cumulative"] for s in exp1["shells"]]
    ax3.plot(ns, cums, "-o", color=ACCENT, markersize=6, zorder=3, linewidth=2)
    ax3.fill_between(ns, cums, alpha=0.08, color=ACCENT)
    nobles = exp1["cumulative_vs_noble_gas"]
    for ng in nobles:
        ax3.axhline(ng["atomic_number_Z"], color=ACCENT4, alpha=0.25, linewidth=0.8, linestyle="--")
        ax3.text(7.15, ng["atomic_number_Z"], ng["noble_gas"],
                 fontsize=7, color=ACCENT4, va="center")
    ax3.set_xlabel("Shell n")
    ax3.set_ylabel("Cumulative electrons")
    ax3.set_title("Noble gas alignment")
    ax3.set_xticks(ns)
    ax3.grid(axis="y", alpha=0.2, zorder=0)

    # 1d — Heatmap: (n, l) → 2(2l+1) states
    ax4 = fig.add_subplot(1, 4, 4)
    grid = np.zeros((7, 7))
    for shell in exp1["shells"]:
        n = shell["n"]
        for sub in shell["breakdown"]:
            grid[n-1, sub["l"]] = sub["subtotal"]
    grid_masked = np.ma.masked_where(grid == 0, grid)
    im = ax4.imshow(grid_masked, cmap="YlOrRd", aspect="auto", origin="lower")
    for i in range(7):
        for j in range(7):
            if grid[i, j] > 0:
                ax4.text(j, i, int(grid[i, j]), ha="center", va="center",
                         fontsize=8, fontweight="bold",
                         color="white" if grid[i, j] > 16 else "#374151")
    ax4.set_xlabel("Azimuthal l")
    ax4.set_ylabel("Principal n")
    ax4.set_xticks(range(7))
    ax4.set_xticklabels(range(7))
    ax4.set_yticks(range(7))
    ax4.set_yticklabels(range(1, 8))
    ax4.set_title("State count per (n, l)")
    plt.colorbar(im, ax=ax4, shrink=0.7, label="States")

    fig.tight_layout(pad=2.0)
    fig.savefig(os.path.join(OUT, "panel_1_shell_capacity.png"))
    plt.close(fig)
    print("  Panel 1 saved.")


# ═══════════════════════════════════════════════════════════════
#  PANEL 2: Spectral Reconstruction
# ═══════════════════════════════════════════════════════════════

def panel_2():
    fig = plt.figure(figsize=(20, 4.5))

    h_data = exp2["species"][0]
    h2_data = exp2["species"][1]
    h2o_data = exp2["species"][2]

    # 2a — H: computed vs NIST wavelength
    ax1 = fig.add_subplot(1, 4, 1)
    h_comp = [l["computed_wavelength_nm"] for l in h_data["lines"]]
    h_nist = [l["nist_wavelength_nm"] for l in h_data["lines"]]
    ax1.scatter(h_nist, h_comp, s=30, c=ACCENT, zorder=3, edgecolors="white", linewidth=0.5)
    lims = [min(h_nist)*0.9, max(h_nist)*1.05]
    ax1.plot(lims, lims, "--", color=GRAY, linewidth=1, alpha=0.6, zorder=2)
    ax1.set_xlabel("NIST wavelength (nm)")
    ax1.set_ylabel("Partition model (nm)")
    ax1.set_title("Hydrogen: model vs NIST")
    ax1.set_xscale("log")
    ax1.set_yscale("log")
    ax1.grid(alpha=0.2, zorder=0)

    # 2b — H2 per-transition error bars
    ax2 = fig.add_subplot(1, 4, 2)
    h2_names = [l["transition"] for l in h2_data["lines"]]
    h2_errs = [l["relative_error_pct"] for l in h2_data["lines"]]
    y_pos = range(len(h2_names))
    colors = [ACCENT3 if e < 0.1 else ACCENT2 if e < 0.2 else ACCENT4 for e in h2_errs]
    ax2.barh(y_pos, h2_errs, color=colors, edgecolor="white", linewidth=0.5, height=0.7)
    ax2.set_yticks(y_pos)
    ax2.set_yticklabels(h2_names, fontsize=7)
    ax2.set_xlabel("Relative error (%)")
    ax2.set_title("H₂ transition errors")
    ax2.axvline(0.1, color=GRAY, linewidth=0.8, linestyle=":", alpha=0.5)
    ax2.grid(axis="x", alpha=0.2, zorder=0)

    # 2c — 3D: H2O transitions in quantum-number space
    ax3 = fig.add_subplot(1, 4, 3, projection="3d")
    h2o_q = [l["quanta"] for l in h2o_data["lines"]]
    h2o_e = [l["relative_error_pct"] for l in h2o_data["lines"]]
    n1 = [q[0] for q in h2o_q]
    n2 = [q[1] for q in h2o_q]
    n3 = [q[2] for q in h2o_q]
    norm = Normalize(vmin=min(h2o_e), vmax=max(h2o_e))
    colors3d = cm.RdYlGn_r(norm(np.array(h2o_e)))
    sc = ax3.scatter(n1, n2, n3, c=h2o_e, cmap="RdYlGn_r", s=80,
                     edgecolors="white", linewidth=0.5, depthshade=True)
    ax3.set_xlabel("n₁", labelpad=6)
    ax3.set_ylabel("n₂", labelpad=6)
    ax3.set_zlabel("n₃", labelpad=6)
    ax3.set_title("H₂O error by mode")
    ax3.view_init(elev=20, azim=-40)
    plt.colorbar(sc, ax=ax3, shrink=0.5, label="Error %", pad=0.12)

    # 2d — Summary: species mean error comparison
    ax4 = fig.add_subplot(1, 4, 4)
    species = ["H", "H₂", "H₂O\nfundamentals", "H₂O\novertones"]
    h2o_fund = [l for l in h2o_data["lines"] if l["mode"] in ("v1", "v2", "v3")]
    h2o_over = [l for l in h2o_data["lines"] if l["mode"] not in ("v1", "v2", "v3")]
    means = [
        h_data["mean_relative_error_pct"],
        h2_data["mean_relative_error_pct"],
        sum(l["relative_error_pct"] for l in h2o_fund) / len(h2o_fund),
        sum(l["relative_error_pct"] for l in h2o_over) / len(h2o_over),
    ]
    maxes = [
        h_data["max_relative_error_pct"],
        h2_data["max_relative_error_pct"],
        max(l["relative_error_pct"] for l in h2o_fund),
        max(l["relative_error_pct"] for l in h2o_over),
    ]
    x = np.arange(len(species))
    w = 0.35
    ax4.bar(x - w/2, means, w, label="Mean", color=ACCENT, edgecolor="white")
    ax4.bar(x + w/2, maxes, w, label="Max", color=ACCENT2, edgecolor="white")
    ax4.axhline(0.1, color=ACCENT4, linewidth=1, linestyle="--", alpha=0.5)
    ax4.axhline(0.2, color=ACCENT4, linewidth=0.8, linestyle=":", alpha=0.3)
    ax4.set_xticks(x)
    ax4.set_xticklabels(species, fontsize=8)
    ax4.set_ylabel("Relative error (%)")
    ax4.set_title("Error by species")
    ax4.legend(fontsize=7, framealpha=0.7)
    ax4.grid(axis="y", alpha=0.2, zorder=0)

    fig.tight_layout(pad=2.0)
    fig.savefig(os.path.join(OUT, "panel_2_spectral_reconstruction.png"))
    plt.close(fig)
    print("  Panel 2 saved.")


# ═══════════════════════════════════════════════════════════════
#  PANEL 3: Circuit Topology & S-Entropy Texture
# ═══════════════════════════════════════════════════════════════

def panel_3():
    fig = plt.figure(figsize=(20, 4.5))

    circ = exp3["circuit"]
    nodes = circ["nodes"]
    edges = circ["edges"]
    tex = exp3["healthy_state"]["s_entropy_texture"]
    fw = exp3["healthy_state"]["flux_weights"]

    N = len(nodes)

    # 3a — Conductance heatmap (adjacency matrix)
    ax1 = fig.add_subplot(1, 4, 1)
    G_mat = np.zeros((N, N))
    for e in edges:
        G_mat[e["src"], e["dst"]] = e["G"]
    G_log = np.log10(G_mat + 1e-3)
    G_masked = np.ma.masked_where(G_mat < 1e-6, G_log)
    im = ax1.imshow(G_masked, cmap="YlOrRd", aspect="auto")
    node_labels = [n["name"][:4] for n in nodes]
    ax1.set_xticks(range(N))
    ax1.set_xticklabels(node_labels, fontsize=6.5, rotation=45, ha="right")
    ax1.set_yticks(range(N))
    ax1.set_yticklabels(node_labels, fontsize=6.5)
    ax1.set_title("log₁₀ Conductance G")
    plt.colorbar(im, ax=ax1, shrink=0.7)

    # 3b — 3D S-entropy texture (Se, Sk, St)
    ax2 = fig.add_subplot(1, 4, 2, projection="3d")
    Se = [t["Se"] for t in tex]
    Sk = [t["Sk"] for t in tex]
    St = [t["St"] for t in tex]
    node_names = [t["node"] for t in tex]
    colors_3d = cm.plasma(np.linspace(0.15, 0.85, N))
    ax2.scatter(Se, Sk, St, c=colors_3d, s=100, edgecolors="white",
                linewidth=0.5, depthshade=True, zorder=3)
    for i in range(N):
        ax2.text(Se[i], Sk[i], St[i] + 0.03, node_names[i][:3],
                 fontsize=5.5, ha="center", zorder=4)
    # Draw edges
    for e in edges:
        s, d = e["src"], e["dst"]
        ax2.plot([Se[s], Se[d]], [Sk[s], Sk[d]], [St[s], St[d]],
                 color=GRAY, alpha=0.2, linewidth=0.5, zorder=1)
    ax2.set_xlabel("Se (electrical)", labelpad=6, fontsize=8)
    ax2.set_ylabel("Sk (kinetic)", labelpad=6, fontsize=8)
    ax2.set_zlabel("St (topological)", labelpad=6, fontsize=8)
    ax2.set_title("S-entropy texture")
    ax2.view_init(elev=20, azim=-55)

    # 3c — Flux per edge (bar chart, log scale)
    ax3 = fig.add_subplot(1, 4, 3)
    flux_h = exp3["healthy_state"]["flux_pattern"]
    edge_names = [e["name"][:8] for e in edges]
    y_pos = range(len(edge_names))
    colors_bar = [ACCENT4 if fw[i] > 0.1 else ACCENT if fw[i] > 0.005 else LIGHT
                  for i in range(len(edges))]
    ax3.barh(y_pos, flux_h, color=colors_bar, edgecolor="white", linewidth=0.5)
    ax3.set_yticks(y_pos)
    ax3.set_yticklabels(edge_names, fontsize=6.5)
    ax3.set_xscale("log")
    ax3.set_xlabel("Flux magnitude")
    ax3.set_title("Edge flux pattern")
    ax3.grid(axis="x", alpha=0.2, zorder=0)

    # 3d — Polar: flux weights around the circuit
    ax4 = fig.add_subplot(1, 4, 4, projection="polar")
    angles = np.linspace(0, 2 * np.pi, len(fw), endpoint=False)
    widths = np.full(len(fw), 2 * np.pi / len(fw))
    colors_polar = cm.coolwarm(np.array(fw) / max(fw))
    ax4.bar(angles, fw, width=widths * 0.85, color=colors_polar,
            edgecolor="white", linewidth=0.5, alpha=0.85)
    ax4.set_xticks(angles)
    ax4.set_xticklabels([e["name"][:5] for e in edges], fontsize=5)
    ax4.set_title("Flux weight distribution", pad=15)
    ax4.set_rlabel_position(90)

    fig.tight_layout(pad=2.0)
    fig.savefig(os.path.join(OUT, "panel_3_circuit_topology.png"))
    plt.close(fig)
    print("  Panel 3 saved.")


# ═══════════════════════════════════════════════════════════════
#  PANEL 4: Disease Detection
# ═══════════════════════════════════════════════════════════════

def panel_4():
    fig = plt.figure(figsize=(20, 4.5))

    single = exp3["single_edge_disruptions"]
    multi = exp3["multi_edge_disruptions"]
    sev = exp3["severity_gradient"]

    # 4a — Single-edge visibility (sorted horizontal bar)
    ax1 = fig.add_subplot(1, 4, 1)
    sorted_single = sorted(single, key=lambda x: x["visibility_V"])
    names = [s["edge_name"][:10] for s in sorted_single]
    Vs = [s["visibility_V"] for s in sorted_single]
    colors_v = [ACCENT4 if v < 0.5 else ACCENT2 if v < 0.95 else ACCENT3 for v in Vs]
    y_pos = range(len(names))
    ax1.barh(y_pos, Vs, color=colors_v, edgecolor="white", linewidth=0.5, height=0.7)
    ax1.axvline(0.95, color=GRAY, linewidth=1, linestyle="--", alpha=0.5)
    ax1.set_yticks(y_pos)
    ax1.set_yticklabels(names, fontsize=6.5)
    ax1.set_xlabel("Visibility V")
    ax1.set_title("Single-edge disruption")
    ax1.set_xlim(0, 1.05)
    ax1.grid(axis="x", alpha=0.2, zorder=0)

    # 4b — 3D surface: severity × edge index → V
    ax2 = fig.add_subplot(1, 4, 2, projection="3d")
    import copy
    edges_data = exp3["circuit"]["edges"]
    nodes_data = exp3["circuit"]["nodes"]
    severities = [10, 30, 50, 70, 90, 99]
    edge_indices = list(range(len(edges_data)))

    # Build grid
    Z = np.zeros((len(severities), len(edge_indices)))
    fw = exp3["healthy_state"]["flux_weights"]
    for si, sev_pct in enumerate(severities):
        for ei in edge_indices:
            reduction = sev_pct / 100.0
            # V = exp(w_k * ln(1 - 0.9*reduction)) approximately
            # More accurate: V = (1-reduction)^(w_k) using geometric model
            ratio = 1.0 - reduction
            if ratio < 1e-10:
                ratio = 1e-10
            Z[si, ei] = math.exp(fw[ei] * math.log(max(ratio, 1e-20)))

    X, Y = np.meshgrid(edge_indices, severities)
    surf = ax2.plot_surface(X, Y, Z, cmap="RdYlGn", alpha=0.85,
                            edgecolor="white", linewidth=0.2)
    ax2.set_xlabel("Edge index", labelpad=8, fontsize=8)
    ax2.set_ylabel("Severity %", labelpad=8, fontsize=8)
    ax2.set_zlabel("Visibility V", labelpad=8, fontsize=8)
    ax2.set_title("Severity × edge → V")
    ax2.view_init(elev=25, azim=-45)

    # 4c — PFK severity gradient line
    ax3 = fig.add_subplot(1, 4, 3)
    sev_pcts = [s["reduction_pct"] for s in sev]
    sev_Vs = [s["visibility_V"] for s in sev]
    ax3.plot(sev_pcts, sev_Vs, "-o", color=ACCENT, markersize=7,
             linewidth=2.5, zorder=3)
    ax3.fill_between(sev_pcts, sev_Vs, alpha=0.08, color=ACCENT)
    ax3.axhline(0.95, color=ACCENT4, linewidth=1, linestyle="--", alpha=0.4)
    ax3.set_xlabel("Conductance reduction (%)")
    ax3.set_ylabel("Visibility V")
    ax3.set_title("PFK severity gradient")
    ax3.grid(alpha=0.2, zorder=0)
    ax3.set_ylim(0.97, 1.001)

    # 4d — Multi-edge disruptions bar
    ax4 = fig.add_subplot(1, 4, 4)
    cats = ["Healthy"] + [f"{m['num_edges_disrupted']} edges" for m in multi]
    vals = [1.0] + [m["visibility_V"] for m in multi]
    colors_m = [ACCENT3] + [ACCENT2 if v > 0.3 else ACCENT4 for v in vals[1:]]
    bars = ax4.bar(cats, vals, color=colors_m, edgecolor="white", linewidth=0.5, zorder=3)
    ax4.axhline(0.3, color=ACCENT4, linewidth=1, linestyle="--", alpha=0.5)
    for bar, v in zip(bars, vals):
        ax4.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.02,
                 f"{v:.3f}", ha="center", fontsize=8, color="#374151")
    ax4.set_ylabel("Visibility V")
    ax4.set_title("Multi-edge disease")
    ax4.set_ylim(0, 1.15)
    ax4.grid(axis="y", alpha=0.2, zorder=0)

    fig.tight_layout(pad=2.0)
    fig.savefig(os.path.join(OUT, "panel_4_disease_detection.png"))
    plt.close(fig)
    print("  Panel 4 saved.")


# ═══════════════════════════════════════════════════════════════
#  PANEL 5: Therapeutic Restoration
# ═══════════════════════════════════════════════════════════════

def panel_5():
    fig = plt.figure(figsize=(20, 4.5))

    pre = exp4["pre_treatment"]
    post = exp4["post_treatment"]
    opt = exp4["optimization"]
    edges_data = exp3["circuit"]["edges"]
    nodes_data = exp3["circuit"]["nodes"]

    # 5a — Before/after comparison
    ax1 = fig.add_subplot(1, 4, 1)
    metrics = ["Visibility V", "Coherence R"]
    pre_vals = [pre["visibility_V"], pre["coherence_R"]]
    post_vals = [post["visibility_V"], post["coherence_R"]]
    x = np.arange(len(metrics))
    w = 0.3
    ax1.bar(x - w/2, pre_vals, w, label="Diseased", color=ACCENT4,
            edgecolor="white", zorder=3)
    ax1.bar(x + w/2, post_vals, w, label="Treated", color=ACCENT3,
            edgecolor="white", zorder=3)
    ax1.axhline(0.7, color=GRAY, linewidth=0.8, linestyle=":", alpha=0.5)
    ax1.axhline(0.9, color=GRAY, linewidth=0.8, linestyle=":", alpha=0.5)
    ax1.set_xticks(x)
    ax1.set_xticklabels(metrics)
    ax1.set_ylabel("Score")
    ax1.set_title("Treatment outcome")
    ax1.legend(fontsize=8)
    ax1.set_ylim(0, 1.15)
    ax1.grid(axis="y", alpha=0.2, zorder=0)

    # 5b — 3D bar: Healthy G vs Diseased G vs Treated G for key edges
    ax2 = fig.add_subplot(1, 4, 2, projection="3d")
    disease_ids = [d["id"] for d in pre["diseased_edges"]]
    boosts = {p["edge_id"]: p["boost_factor"] for p in opt["eta_perturbations"]}

    key_edges = disease_ids
    edge_labels = [edges_data[i]["name"][:8] for i in key_edges]
    healthy_G = [edges_data[i]["G"] for i in key_edges]
    diseased_G = [edges_data[i]["G"] * 0.1 for i in key_edges]
    treated_G = [diseased_G[j] * boosts.get(key_edges[j], 1.0)
                 for j in range(len(key_edges))]

    x_pos = np.arange(len(key_edges))
    dx = 0.25
    ax2.bar3d(x_pos - dx, [0]*len(key_edges), [0]*len(key_edges),
              dx*0.9, 0.8, healthy_G, color=ACCENT, alpha=0.8, label="Healthy")
    ax2.bar3d(x_pos, [0]*len(key_edges), [0]*len(key_edges),
              dx*0.9, 0.8, diseased_G, color=ACCENT4, alpha=0.8, label="Diseased")
    ax2.bar3d(x_pos + dx, [0]*len(key_edges), [0]*len(key_edges),
              dx*0.9, 0.8, treated_G, color=ACCENT3, alpha=0.8, label="Treated")
    ax2.set_xticks(x_pos)
    ax2.set_xticklabels(edge_labels, fontsize=6.5)
    ax2.set_zlabel("Conductance G", labelpad=8, fontsize=8)
    ax2.set_title("Edge conductance restoration")
    ax2.set_yticks([])
    ax2.view_init(elev=20, azim=-40)

    # 5c — Flux pattern comparison: healthy vs diseased vs treated (stacked)
    ax3 = fig.add_subplot(1, 4, 3)
    flux_h = exp3["healthy_state"]["flux_pattern"]

    # Recompute diseased and treated flux from conductances
    import copy
    full_nodes = []
    for n in nodes_data:
        node = dict(n)
        RT = 2.479
        node["mu"] = n["mu"]
        full_nodes.append(node)

    full_edges = []
    for e in edges_data:
        full_edges.append(dict(e))

    def calc_flux(edge_list):
        fluxes = []
        for e in edge_list:
            I = e["G"] * abs(full_nodes[e["src"]]["mu"] - full_nodes[e["dst"]]["mu"])
            fluxes.append(I)
        return fluxes

    dis_edges = [dict(e) for e in full_edges]
    for idx in disease_ids:
        dis_edges[idx]["G"] *= 0.1
    flux_d = calc_flux(dis_edges)

    tre_edges = [dict(e) for e in dis_edges]
    for eid, b in boosts.items():
        tre_edges[eid]["G"] *= b
    flux_t = calc_flux(tre_edges)

    # Normalize for comparison (log scale)
    edge_idx = np.arange(len(full_edges))
    ax3.semilogy(edge_idx, flux_h, "o-", color=ACCENT, markersize=4,
                 linewidth=1.5, label="Healthy", zorder=3)
    ax3.semilogy(edge_idx, flux_d, "s--", color=ACCENT4, markersize=4,
                 linewidth=1.5, label="Diseased", zorder=3)
    ax3.semilogy(edge_idx, flux_t, "^:", color=ACCENT3, markersize=4,
                 linewidth=1.5, label="Treated", zorder=3)
    # Highlight diseased edges
    for idx in disease_ids:
        ax3.axvspan(idx-0.3, idx+0.3, alpha=0.08, color=ACCENT4)
    ax3.set_xlabel("Edge index")
    ax3.set_ylabel("Flux (log)")
    ax3.set_title("Flux pattern comparison")
    ax3.legend(fontsize=7, loc="lower left")
    ax3.grid(alpha=0.2, zorder=0)

    # 5d — Optimization metrics summary (radial/gauge chart)
    ax4 = fig.add_subplot(1, 4, 4)
    criteria = ["V > 0.9", "||η||₀ ≤ 3", "t < 100ms"]
    achieved = [post["visibility_V"], 1.0 - opt["l0_norm"]/3.0,
                1.0 - opt["optimization_time_ms"]/100.0]
    thresholds = [0.9, 0.0, 0.0]
    actual_vals = [f"V={post['visibility_V']:.2f}",
                   f"n={opt['l0_norm']}",
                   f"t={opt['optimization_time_ms']:.1f}ms"]

    y_pos = np.arange(len(criteria))
    bar_vals = [min(v, 1.0) for v in achieved]
    colors_r = [ACCENT3 if v >= t else ACCENT4 for v, t in zip(achieved, thresholds)]

    # Background bars
    ax4.barh(y_pos, [1.0]*len(criteria), color=LIGHT, edgecolor="white",
             height=0.5, zorder=1)
    ax4.barh(y_pos, bar_vals, color=colors_r, edgecolor="white",
             height=0.5, zorder=2)
    for i, (c, v) in enumerate(zip(criteria, actual_vals)):
        ax4.text(1.03, i, v, va="center", fontsize=9, fontweight="bold",
                 color="#374151")
    ax4.set_yticks(y_pos)
    ax4.set_yticklabels(criteria, fontsize=9)
    ax4.set_xlim(0, 1.35)
    ax4.set_xlabel("Achievement ratio")
    ax4.set_title("Optimization criteria")
    ax4.grid(axis="x", alpha=0.2, zorder=0)

    fig.tight_layout(pad=2.0)
    fig.savefig(os.path.join(OUT, "panel_5_therapeutic_restoration.png"))
    plt.close(fig)
    print("  Panel 5 saved.")


# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("Generating panels...")
    panel_1()
    panel_2()
    panel_3()
    panel_4()
    panel_5()
    print(f"\nAll panels saved to: {OUT}")

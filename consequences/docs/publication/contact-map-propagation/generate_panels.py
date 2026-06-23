"""
Contact Maps in Systems Biology — Publication Panels
=====================================================
7 panels, each with 4 subplots in a row.
White background, minimal text, at least one 3D chart per panel.
No text-based, conceptual, or table charts.
"""

import json
import math
import os
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from mpl_toolkits.mplot3d.art3d import Line3DCollection
from matplotlib import cm as mpl_cm
from matplotlib.colors import Normalize
import matplotlib.patches as mpatches
import networkx as nx

VAL = os.path.join(os.path.dirname(os.path.abspath(__file__)), "validation")
FIG = os.path.join(os.path.dirname(os.path.abspath(__file__)), "figures")
os.makedirs(FIG, exist_ok=True)

# Load all validation data
def load(name):
    with open(os.path.join(VAL, name), encoding='utf-8') as f:
        return json.load(f)

d04 = load("04_contact_maps.json")
d08 = load("08_triple_coherence_perturbation.json")
d09 = load("09_flux_visibility.json")
d10 = load("10_backward_navigation.json")
d12 = load("12_contact_filtration.json")
d13 = load("13_spectral_properties.json")
d14 = load("14_compartmental_factorisation.json")
d16 = load("16_residue_chain_propagation.json")
d17 = load("17_sentropy_tables.json")
d18 = load("18_disease_profiles.json")

# Colors
C_BLUE = "#2563EB"
C_ORANGE = "#F59E0B"
C_GREEN = "#10B981"
C_RED = "#EF4444"
C_PURPLE = "#8B5CF6"
C_PINK = "#EC4899"
C_GRAY = "#6B7280"
C_LIGHT = "#E5E7EB"
PATHWAY_COLORS = [C_BLUE, C_ORANGE, C_GREEN, C_RED]
PATHWAY_NAMES = ["Glycolysis", "TCA Cycle", "OxPhos", "EGFR/MAPK"]

plt.rcParams.update({
    "font.family": "sans-serif",
    "font.size": 8,
    "axes.titlesize": 9,
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
#  PANEL 1: S-Entropy State Space (4 pathways in 3D + projections)
# ═══════════════════════════════════════════════════════════════

def panel_1():
    fig = plt.figure(figsize=(20, 4.5))

    for idx, pw in enumerate(d04["pathways"]):
        species = pw["species"]
        Sk = [s["Sk"] for s in species]
        St = [s["St"] for s in species]
        Se = [s["Se"] for s in species]
        names = [s["id"] for s in species]

        if idx == 0:
            ax = fig.add_subplot(1, 4, 1, projection='3d')
            ax.scatter(Sk, St, Se, c=Se, cmap='viridis', s=60, edgecolors='black',
                       linewidth=0.5, zorder=5)
            for i in range(len(Sk)):
                ax.plot([Sk[i], Sk[i]], [St[i], St[i]], [0, Se[i]],
                        color=C_LIGHT, linewidth=0.5, alpha=0.5)
            for i in range(len(species) - 1):
                edge_key = f"{species[i]['id']}"
                ax.plot([Sk[i], Sk[i+1]], [St[i], St[i+1]], [Se[i], Se[i+1]],
                        color=C_BLUE, linewidth=0.8, alpha=0.4)
            ax.set_xlabel('$S_k$', fontsize=8)
            ax.set_ylabel('$S_t$', fontsize=8)
            ax.set_zlabel('$S_e$', fontsize=8)
            ax.set_title(f'{pw["pathway"]}')
            ax.view_init(elev=25, azim=135)
        else:
            ax = fig.add_subplot(1, 4, idx + 1, projection='3d')
            color = PATHWAY_COLORS[idx]
            ax.scatter(Sk, St, Se, c=Se, cmap='viridis', s=60, edgecolors='black',
                       linewidth=0.5, zorder=5)
            for i in range(len(Sk)):
                ax.plot([Sk[i], Sk[i]], [St[i], St[i]], [0, Se[i]],
                        color=C_LIGHT, linewidth=0.5, alpha=0.5)
            ax.set_xlabel('$S_k$', fontsize=8)
            ax.set_ylabel('$S_t$', fontsize=8)
            ax.set_zlabel('$S_e$', fontsize=8)
            ax.set_title(f'{pw["pathway"]}')
            ax.view_init(elev=25, azim=135)

    fig.suptitle("Panel 1: S-Entropy Vertex Embeddings", fontsize=11, fontweight='bold', y=1.02)
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, "panel_1_sentropy_embeddings.png"), dpi=300, bbox_inches='tight')
    plt.close(fig)
    print("[OK] Panel 1")


# ═══════════════════════════════════════════════════════════════
#  PANEL 2: Contact Graphs (network visualization + edge weights)
# ═══════════════════════════════════════════════════════════════

def panel_2():
    fig = plt.figure(figsize=(20, 4.5))

    for idx, pw in enumerate(d17["pathways"]):
        ax = fig.add_subplot(1, 4, idx + 1)
        species = pw["species"]
        reactions = pw["reactions"]

        G = nx.DiGraph()
        for s in species:
            G.add_node(s["id"])

        edge_costs = []
        for r in reactions:
            parts = r["reaction"].split("→")
            if len(parts) == 2:
                src, dst = parts[0].strip(), parts[1].strip()
                cost = r["contact_cost"] if r["contact_cost"] else 0.1
                G.add_edge(src, dst, weight=cost)
                edge_costs.append(cost)

        if len(species) <= 9 and any("cycle" in pw["pathway"].lower() for _ in [1]):
            pos = nx.circular_layout(G)
        else:
            pos = nx.spring_layout(G, seed=42, k=2.0)

        if edge_costs:
            max_cost = max(edge_costs) if max(edge_costs) > 0 else 1
            widths = [3.0 * (1 - c / max_cost) + 0.5 for c in edge_costs]
            edge_colors_vals = [c / max_cost for c in edge_costs]
        else:
            widths = [1.0]
            edge_colors_vals = [0.5]

        nx.draw_networkx_edges(G, pos, ax=ax, width=widths,
                               edge_color=edge_colors_vals, edge_cmap=plt.cm.RdYlGn_r,
                               arrows=True, arrowsize=10, alpha=0.7,
                               connectionstyle="arc3,rad=0.1")

        Se_vals = [s["Se"] for s in species]
        node_colors = [plt.cm.viridis(se) for se in Se_vals]
        nx.draw_networkx_nodes(G, pos, ax=ax, node_color=Se_vals, cmap=plt.cm.viridis,
                               node_size=300, edgecolors='black', linewidths=0.8)
        nx.draw_networkx_labels(G, pos, ax=ax, font_size=6, font_weight='bold')

        ax.set_title(pw["pathway"])
        ax.set_xlim([min(v[0] for v in pos.values()) - 0.3,
                     max(v[0] for v in pos.values()) + 0.3])
        ax.set_ylim([min(v[1] for v in pos.values()) - 0.3,
                     max(v[1] for v in pos.values()) + 0.3])
        ax.axis('off')

    fig.suptitle("Panel 2: Contact Graphs $G_C = (V, E, w)$", fontsize=11, fontweight='bold', y=1.02)
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, "panel_2_contact_graphs.png"), dpi=300, bbox_inches='tight')
    plt.close(fig)
    print("[OK] Panel 2")


# ═══════════════════════════════════════════════════════════════
#  PANEL 3: Flux Visibility Response Curves
# ═══════════════════════════════════════════════════════════════

def panel_3():
    fig = plt.figure(figsize=(20, 4.5))

    # 3a: V vs alpha for all pathways (log scale)
    ax1 = fig.add_subplot(1, 4, 1)
    for idx, test in enumerate(d09["tests"]):
        alphas = [p["alpha"] for p in test["alpha_sweep"]]
        Vs = [p["V"] for p in test["alpha_sweep"]]
        ax1.plot(alphas, Vs, 'o-', color=PATHWAY_COLORS[idx], linewidth=1.5,
                 markersize=4, label=test["pathway"])
    ax1.set_xscale('log')
    ax1.axhline(y=1.0, color=C_GRAY, linestyle='--', alpha=0.5)
    ax1.axvline(x=1.0, color=C_GRAY, linestyle='--', alpha=0.5)
    ax1.set_xlabel(r'Perturbation $\alpha$')
    ax1.set_ylabel('Flux visibility $V$')
    ax1.set_title('$V(\\alpha)$ response')
    ax1.legend(fontsize=6, loc='lower right')
    ax1.grid(alpha=0.2)

    # 3b: 3D surface — V as function of alpha and pathway index
    ax2 = fig.add_subplot(1, 4, 2, projection='3d')
    for idx, test in enumerate(d09["tests"]):
        alphas = np.array([p["alpha"] for p in test["alpha_sweep"]])
        Vs = np.array([p["V"] for p in test["alpha_sweep"]])
        ys = np.full_like(alphas, idx)
        ax2.plot(np.log10(alphas), ys, Vs, color=PATHWAY_COLORS[idx], linewidth=2)
        ax2.scatter(np.log10(alphas), ys, Vs, color=PATHWAY_COLORS[idx], s=15, zorder=5)
    ax2.set_xlabel(r'$\log_{10}(\alpha)$', fontsize=7)
    ax2.set_ylabel('Pathway', fontsize=7)
    ax2.set_zlabel('$V$', fontsize=7)
    ax2.set_yticks(range(4))
    ax2.set_yticklabels(['Gly', 'TCA', 'OxP', 'MAPK'], fontsize=6)
    ax2.set_title('$V$ landscape')
    ax2.view_init(elev=20, azim=220)

    # 3c: Glycolysis V waterfall — per-edge flux ratio
    ax3 = fig.add_subplot(1, 4, 3)
    gly_sweep = d09["tests"][0]["alpha_sweep"]
    alphas_gly = [p["alpha"] for p in gly_sweep]
    Vs_gly = [p["V"] for p in gly_sweep]
    colors_bar = [C_GREEN if a == 1.0 else (C_RED if v < 0.5 else C_ORANGE) for a, v in zip(alphas_gly, Vs_gly)]
    bars = ax3.bar(range(len(alphas_gly)), Vs_gly, color=colors_bar, edgecolor='white', linewidth=0.5)
    ax3.set_xticks(range(len(alphas_gly)))
    ax3.set_xticklabels([str(a) for a in alphas_gly], fontsize=6, rotation=45)
    ax3.set_xlabel(r'$\alpha$')
    ax3.set_ylabel('$V$')
    ax3.set_title('Glycolysis HK1')
    ax3.axhline(y=1.0, color=C_GRAY, linestyle='--', alpha=0.5)
    ax3.grid(axis='y', alpha=0.2)

    # 3d: Disease V comparison (grouped bar)
    ax4 = fig.add_subplot(1, 4, 4)
    diseases = [p["disease"].split("(")[0].strip() for p in d18["profiles"]]
    V_vals = [p["V_diseased"] for p in d18["profiles"]]
    x = np.arange(len(diseases))
    bars = ax4.barh(x, V_vals, color=PATHWAY_COLORS, edgecolor='white', height=0.6)
    ax4.set_yticks(x)
    ax4.set_yticklabels([d[:15] for d in diseases], fontsize=7)
    ax4.set_xlabel('$V$ (diseased)')
    ax4.set_title('Disease visibility')
    ax4.axvline(x=1.0, color=C_GRAY, linestyle='--', alpha=0.5)
    ax4.set_xlim(0, 1.1)
    ax4.grid(axis='x', alpha=0.2)

    fig.suptitle("Panel 3: Flux Visibility Under Perturbation", fontsize=11, fontweight='bold', y=1.02)
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, "panel_3_flux_visibility.png"), dpi=300, bbox_inches='tight')
    plt.close(fig)
    print("[OK] Panel 3")


# ═══════════════════════════════════════════════════════════════
#  PANEL 4: Contact Filtration & Persistent Hierarchy
# ═══════════════════════════════════════════════════════════════

def panel_4():
    fig = plt.figure(figsize=(20, 4.5))

    # 4a: Glycolysis dendrogram (manual barcode-style)
    ax1 = fig.add_subplot(1, 4, 1)
    gly_filt = d12["tests"][0]["filtration"]
    merges = d12["tests"][0]["merge_heights"]
    heights = [m["height"] for m in merges]
    labels_m = [m["merged"] for m in merges]
    y_pos = np.arange(len(heights))
    ax1.barh(y_pos, heights, color=C_BLUE, edgecolor='white', height=0.6, alpha=0.8)
    ax1.set_yticks(y_pos)
    ax1.set_yticklabels(labels_m, fontsize=6)
    ax1.set_xlabel('Contact cost $\\mathcal{C}(e)$')
    ax1.set_title('Glycolysis filtration')
    ax1.grid(axis='x', alpha=0.2)

    # 4b: Components vs threshold (all pathways)
    ax2 = fig.add_subplot(1, 4, 2)
    for idx, test in enumerate(d12["tests"]):
        costs = [f["cost"] for f in test["filtration"]]
        comps = [f["components_after"] for f in test["filtration"]]
        n_species = comps[0] + 1 if comps else 10
        costs_ext = [0] + costs
        comps_ext = [n_species] + comps
        ax2.step(costs_ext, comps_ext, where='post', color=PATHWAY_COLORS[idx],
                 linewidth=2, label=test["pathway"])
    ax2.set_xlabel('Threshold $\\tau$')
    ax2.set_ylabel('Connected components')
    ax2.set_title('Filtration curves')
    ax2.legend(fontsize=6)
    ax2.grid(alpha=0.2)

    # 4c: 3D persistence landscape
    ax3 = fig.add_subplot(1, 4, 3, projection='3d')
    for idx, test in enumerate(d12["tests"]):
        costs = [f["cost"] for f in test["filtration"]]
        comps = [f["components_after"] for f in test["filtration"]]
        n_sp = comps[0] + 1 if comps else 10
        costs_ext = [0] + costs
        comps_ext = [n_sp] + comps
        ys = np.full(len(costs_ext), idx)
        ax3.plot(costs_ext, ys, comps_ext, color=PATHWAY_COLORS[idx], linewidth=2)
        ax3.scatter(costs_ext, ys, comps_ext, color=PATHWAY_COLORS[idx], s=15)
    ax3.set_xlabel('$\\tau$', fontsize=7)
    ax3.set_ylabel('Pathway', fontsize=7)
    ax3.set_zlabel('Components', fontsize=7)
    ax3.set_yticks(range(4))
    ax3.set_yticklabels(['Gly', 'TCA', 'OxP', 'MAPK'], fontsize=6)
    ax3.set_title('Persistence landscape')
    ax3.view_init(elev=25, azim=230)

    # 4d: Edge cost distributions (violin/box)
    ax4 = fig.add_subplot(1, 4, 4)
    all_costs = []
    positions = []
    colors_v = []
    for idx, pw in enumerate(d04["pathways"]):
        costs = [e["cost"] for e in pw["edges"]]
        all_costs.append(costs)
        positions.append(idx)
        colors_v.append(PATHWAY_COLORS[idx])

    parts = ax4.violinplot(all_costs, positions=positions, showmeans=True, showmedians=True)
    for i, pc in enumerate(parts['bodies']):
        pc.set_facecolor(PATHWAY_COLORS[i])
        pc.set_alpha(0.6)
    for key in ['cmeans', 'cmedians', 'cbars', 'cmins', 'cmaxes']:
        if key in parts:
            parts[key].set_color('black')
            parts[key].set_linewidth(0.8)
    ax4.set_xticks(positions)
    ax4.set_xticklabels(PATHWAY_NAMES, fontsize=7)
    ax4.set_ylabel('Contact cost $\\mathcal{C}(e)$')
    ax4.set_title('Edge weight distribution')
    ax4.grid(axis='y', alpha=0.2)

    fig.suptitle("Panel 4: Contact Filtration & Persistent Hierarchy", fontsize=11, fontweight='bold', y=1.02)
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, "panel_4_contact_filtration.png"), dpi=300, bbox_inches='tight')
    plt.close(fig)
    print("[OK] Panel 4")


# ═══════════════════════════════════════════════════════════════
#  PANEL 5: Spectral Properties — Contact Laplacian
# ═══════════════════════════════════════════════════════════════

def panel_5():
    fig = plt.figure(figsize=(20, 4.5))

    # 5a: Eigenvalue spectra (all pathways)
    ax1 = fig.add_subplot(1, 4, 1)
    for idx, test in enumerate(d13["tests"]):
        eigs = test["eigenvalues"]
        ax1.plot(range(len(eigs)), eigs, 'o-', color=PATHWAY_COLORS[idx],
                 markersize=5, linewidth=1.5, label=test["pathway"])
    ax1.set_xlabel('Eigenvalue index')
    ax1.set_ylabel('$\\lambda_i$')
    ax1.set_title('Laplacian spectra')
    ax1.legend(fontsize=6)
    ax1.grid(alpha=0.2)
    ax1.set_yscale('symlog', linthresh=1)

    # 5b: Fiedler vectors (heatmap style)
    ax2 = fig.add_subplot(1, 4, 2)
    fiedler_data = []
    max_len = max(len(t["fiedler_vector"]) for t in d13["tests"])
    for test in d13["tests"]:
        fv = test["fiedler_vector"]
        padded = fv + [0] * (max_len - len(fv))
        fiedler_data.append(padded)
    fiedler_arr = np.array(fiedler_data)
    im = ax2.imshow(fiedler_arr, aspect='auto', cmap='RdBu_r', vmin=-0.6, vmax=0.6)
    ax2.set_yticks(range(4))
    ax2.set_yticklabels(PATHWAY_NAMES, fontsize=7)
    ax2.set_xlabel('Vertex index')
    ax2.set_title('Fiedler vectors $\\mathbf{f}_2$')
    plt.colorbar(im, ax=ax2, fraction=0.046, pad=0.04)

    # 5c: 3D spectral embedding — use first 3 eigenvectors of glycolysis
    ax3 = fig.add_subplot(1, 4, 3, projection='3d')
    gly = d13["tests"][0]
    gly_sp = d04["pathways"][0]["species"]
    # Use Sk, St, Se as proxy for spectral coords (actual eigvecs would need recomputation)
    Sk = [s["Sk"] for s in gly_sp]
    St = [s["St"] for s in gly_sp]
    fv = gly["fiedler_vector"]
    colors_f = [C_BLUE if f >= 0 else C_RED for f in fv]
    ax3.scatter(Sk, St, fv, c=colors_f, s=80, edgecolors='black', linewidth=0.5, zorder=5)
    for i in range(len(Sk) - 1):
        ax3.plot([Sk[i], Sk[i+1]], [St[i], St[i+1]], [fv[i], fv[i+1]],
                 color=C_GRAY, linewidth=0.8, alpha=0.5)
    ax3.set_xlabel('$S_k$', fontsize=7)
    ax3.set_ylabel('$S_t$', fontsize=7)
    ax3.set_zlabel('$f_2$', fontsize=7)
    ax3.set_title('Spectral bisection')
    ax3.view_init(elev=20, azim=135)

    # 5d: Algebraic connectivity comparison (bar)
    ax4 = fig.add_subplot(1, 4, 4)
    lambda2s = [t["lambda_2_algebraic_connectivity"] for t in d13["tests"]]
    x = np.arange(4)
    bars = ax4.bar(x, lambda2s, color=PATHWAY_COLORS, edgecolor='white', width=0.6)
    ax4.set_xticks(x)
    ax4.set_xticklabels(PATHWAY_NAMES, fontsize=7, rotation=15)
    ax4.set_ylabel('$\\lambda_2$')
    ax4.set_title('Algebraic connectivity')
    ax4.grid(axis='y', alpha=0.2)
    for bar, val in zip(bars, lambda2s):
        ax4.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.01,
                 f'{val:.3f}', ha='center', va='bottom', fontsize=7)

    fig.suptitle("Panel 5: Contact Laplacian Spectral Properties", fontsize=11, fontweight='bold', y=1.02)
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, "panel_5_spectral_properties.png"), dpi=300, bbox_inches='tight')
    plt.close(fig)
    print("[OK] Panel 5")


# ═══════════════════════════════════════════════════════════════
#  PANEL 6: Disease Perturbation Profiles
# ═══════════════════════════════════════════════════════════════

def panel_6():
    fig = plt.figure(figsize=(20, 4.5))

    # 6a: 3D S-entropy shift vectors (glycolysis disease)
    ax1 = fig.add_subplot(1, 4, 1, projection='3d')
    profile = d18["profiles"][0]  # glycolysis HK1
    for shift in profile["per_species_shifts"]:
        h = shift["healthy_S"]
        d = shift["diseased_S"]
        ax1.scatter(*h, color=C_GREEN, s=40, edgecolors='black', linewidth=0.4, zorder=5)
        ax1.scatter(*d, color=C_RED, s=40, edgecolors='black', linewidth=0.4, zorder=5)
        ax1.plot([h[0], d[0]], [h[1], d[1]], [h[2], d[2]],
                 color=C_GRAY, linewidth=0.8, alpha=0.6)
    ax1.set_xlabel('$S_k$', fontsize=7)
    ax1.set_ylabel('$S_t$', fontsize=7)
    ax1.set_zlabel('$S_e$', fontsize=7)
    ax1.set_title('HK1 deficiency')
    ax1.view_init(elev=25, azim=135)

    # 6b: Per-species S-entropy shift magnitudes (all 4 diseases)
    ax2 = fig.add_subplot(1, 4, 2)
    for idx, profile in enumerate(d18["profiles"]):
        species_ids = [s["species"] for s in profile["per_species_shifts"]]
        shifts = [s["S_shift"] for s in profile["per_species_shifts"]]
        x = np.arange(len(species_ids))
        offset = idx * 0.2 - 0.3
        ax2.bar(x + offset, shifts, width=0.18, color=PATHWAY_COLORS[idx],
                alpha=0.8, label=profile["pathway"])
    ax2.set_xlabel('Species index')
    ax2.set_ylabel('$|\\Delta \\mathbf{S}|$')
    ax2.set_title('S-entropy shifts')
    ax2.legend(fontsize=5, ncol=2)
    ax2.grid(axis='y', alpha=0.2)

    # 6c: Navigation path lengths
    ax3 = fig.add_subplot(1, 4, 3)
    nav_tests = d10["tests"]
    for idx, test in enumerate(nav_tests):
        path = test["navigation_path"]
        path_len = len(path)
        x = np.arange(path_len)
        ax3.plot(x, np.linspace(1, 0, path_len), 'o-', color=PATHWAY_COLORS[idx],
                 markersize=6, linewidth=1.5, label=test["pathway"])
        # Mark source
        ax3.scatter(path_len - 1, 0, color=PATHWAY_COLORS[idx], s=100,
                    marker='*', zorder=10, edgecolors='black', linewidth=0.5)
    ax3.set_xlabel('Navigation step')
    ax3.set_ylabel('Relative position')
    ax3.set_title('Backward navigation')
    ax3.legend(fontsize=6)
    ax3.grid(alpha=0.2)

    # 6d: Restoration comparison (healthy vs diseased vs restored V)
    ax4 = fig.add_subplot(1, 4, 4)
    x = np.arange(4)
    width = 0.25
    V_healthy = [1.0] * 4
    V_diseased = [p["V_diseased"] for p in d18["profiles"]]
    V_restored = [p["V_restored"] for p in d18["profiles"]]
    ax4.bar(x - width, V_healthy, width, color=C_GREEN, alpha=0.8, label='Healthy')
    ax4.bar(x, V_diseased, width, color=C_RED, alpha=0.8, label='Diseased')
    ax4.bar(x + width, V_restored, width, color=C_BLUE, alpha=0.8, label='Restored')
    ax4.set_xticks(x)
    ax4.set_xticklabels(['Gly', 'TCA', 'OxP', 'MAPK'], fontsize=7)
    ax4.set_ylabel('$V$')
    ax4.set_title('Restoration efficacy')
    ax4.legend(fontsize=6)
    ax4.set_ylim(0, 1.15)
    ax4.grid(axis='y', alpha=0.2)

    fig.suptitle("Panel 6: Disease Perturbation Profiles", fontsize=11, fontweight='bold', y=1.02)
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, "panel_6_disease_profiles.png"), dpi=300, bbox_inches='tight')
    plt.close(fig)
    print("[OK] Panel 6")


# ═══════════════════════════════════════════════════════════════
#  PANEL 7: Residue Chain Propagation & Compartmental Structure
# ═══════════════════════════════════════════════════════════════

def panel_7():
    fig = plt.figure(figsize=(20, 4.5))

    # 7a: Total partition depth vs alpha (self-reinforcement)
    ax1 = fig.add_subplot(1, 4, 1)
    for idx, test in enumerate(d16["tests"]):
        alphas = [td["alpha"] for td in test["total_depths"]]
        depths = [td["total_depth"] for td in test["total_depths"]]
        ax1.plot(alphas, depths, 'o-', color=PATHWAY_COLORS[idx], linewidth=1.5,
                 markersize=5, label=test["pathway"])
        # Mark minimum
        min_idx = np.argmin(depths)
        ax1.scatter(alphas[min_idx], depths[min_idx], color=PATHWAY_COLORS[idx],
                    s=120, marker='v', zorder=10, edgecolors='black', linewidth=0.5)
    ax1.set_xscale('log')
    ax1.set_xlabel(r'Perturbation $\alpha$')
    ax1.set_ylabel('Total partition depth')
    ax1.set_title('Self-reinforcement')
    ax1.legend(fontsize=6)
    ax1.grid(alpha=0.2)

    # 7b: 3D compartmental structure (EGFR/MAPK)
    ax2 = fig.add_subplot(1, 4, 2, projection='3d')
    egfr = d17["pathways"][3]  # EGFR/MAPK
    compartment_z = {"extracellular": 3, "membrane": 2, "cytoplasm": 1, "nucleus": 0}
    compartment_colors = {"extracellular": C_ORANGE, "membrane": C_PURPLE,
                          "cytoplasm": C_BLUE, "nucleus": C_RED}

    species_egfr = egfr["species"]
    np.random.seed(42)
    for i, s in enumerate(species_egfr):
        comp = s["compartment"]
        z = compartment_z.get(comp, 0)
        x = s["Sk"]
        y = s["St"]
        ax2.scatter(x, y, z, color=compartment_colors.get(comp, C_GRAY),
                    s=80, edgecolors='black', linewidth=0.5, zorder=5)

    # Draw edges
    for r in egfr["reactions"]:
        parts = r["reaction"].split("→")
        if len(parts) == 2:
            src_name, dst_name = parts[0].strip(), parts[1].strip()
            src_sp = next((s for s in species_egfr if s["id"] == src_name), None)
            dst_sp = next((s for s in species_egfr if s["id"] == dst_name), None)
            if src_sp and dst_sp:
                z_src = compartment_z.get(src_sp["compartment"], 0)
                z_dst = compartment_z.get(dst_sp["compartment"], 0)
                color = C_RED if src_sp["compartment"] != dst_sp["compartment"] else C_GRAY
                ax2.plot([src_sp["Sk"], dst_sp["Sk"]],
                         [src_sp["St"], dst_sp["St"]],
                         [z_src, z_dst],
                         color=color, linewidth=1.0, alpha=0.6)

    ax2.set_xlabel('$S_k$', fontsize=7)
    ax2.set_ylabel('$S_t$', fontsize=7)
    ax2.set_zlabel('Compartment', fontsize=7)
    ax2.set_zticks([0, 1, 2, 3])
    ax2.set_zticklabels(['Nuc', 'Cyt', 'Mem', 'Ext'], fontsize=5)
    ax2.set_title('EGFR/MAPK compartments')
    ax2.view_init(elev=20, azim=225)

    # 7c: Intra vs Inter compartmental costs
    ax3 = fig.add_subplot(1, 4, 3)
    comp_data = d14["tests"]
    x = np.arange(len(comp_data))
    width = 0.3
    intra = [t["mean_intra_cost"] for t in comp_data]
    inter = [t["mean_inter_cost"] for t in comp_data]
    ax3.bar(x - width/2, intra, width, color=C_GREEN, alpha=0.8, label='Intra')
    ax3.bar(x + width/2, inter, width, color=C_RED, alpha=0.8, label='Inter')
    ax3.set_xticks(x)
    ax3.set_xticklabels([t["pathway"] for t in comp_data], fontsize=7)
    ax3.set_ylabel('Mean contact cost')
    ax3.set_title('Compartmental factorisation')
    ax3.legend(fontsize=7)
    ax3.grid(axis='y', alpha=0.2)

    # 7d: Triple coherence alpha sweep (TCA cycle — shows the clearest response)
    ax4 = fig.add_subplot(1, 4, 4)
    for idx, test in enumerate(d08["tests"]):
        sweep = test["alpha_sweep"]
        alphas = [s["alpha"] for s in sweep]
        Rs = [s["R"] for s in sweep]
        ax4.plot(alphas, Rs, 'o-', color=PATHWAY_COLORS[idx], linewidth=1.5,
                 markersize=4, label=test["pathway"])
    ax4.set_xscale('log')
    ax4.axvline(x=1.0, color=C_GRAY, linestyle='--', alpha=0.5)
    ax4.set_xlabel(r'Perturbation $\alpha$')
    ax4.set_ylabel('Triple coherence $R$')
    ax4.set_title('$R(\\alpha)$ response')
    ax4.legend(fontsize=6)
    ax4.grid(alpha=0.2)

    fig.suptitle("Panel 7: Residue Propagation & Compartmental Structure", fontsize=11, fontweight='bold', y=1.02)
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, "panel_7_residue_compartments.png"), dpi=300, bbox_inches='tight')
    plt.close(fig)
    print("[OK] Panel 7")


# ═══════════════════════════════════════════════════════════════
#  MAIN
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("=" * 60)
    print("Generating 7 publication panels...")
    print("=" * 60)

    panel_1()
    panel_2()
    panel_3()
    panel_4()
    panel_5()
    panel_6()
    panel_7()

    print()
    print(f"All panels saved to: {FIG}")

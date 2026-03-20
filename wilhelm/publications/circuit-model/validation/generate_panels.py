"""
Generate panel charts for 6 validation experiments.
Run from the directory containing this script:
    python generate_panels.py
Reads from results/ subfolder, saves PNG panels to figures/ subfolder.
"""

import os
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D  # noqa: F401

# ---------------------------------------------------------------------------
# Global style
# ---------------------------------------------------------------------------
plt.rcParams.update({
    'figure.facecolor': 'white',
    'axes.facecolor':   'white',
    'font.size':        7,
})

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
FIGURES_DIR = os.path.join(SCRIPT_DIR, 'figures')
os.makedirs(FIGURES_DIR, exist_ok=True)


def _set_3d_white_panes(ax):
    for axis in (ax.xaxis, ax.yaxis, ax.zaxis):
        axis.pane.fill = False
        axis.pane.set_edgecolor('#cccccc')
    try:
        ax.set_box_aspect([1, 1, 1])
    except Exception:
        pass


def _tickparams(ax, labelsize=6, rotation=None):
    ax.tick_params(labelsize=labelsize)
    if rotation is not None:
        for lbl in ax.get_xticklabels():
            lbl.set_rotation(rotation)
            lbl.set_ha('right')


viridis = plt.cm.viridis
plasma  = plt.cm.plasma


# ===========================================================================
# PANEL 1 — Categorical Depth vs Chemical Potential
# ===========================================================================
def panel_exp1():
    species = ["GLC","G6P","F6P","FBP","GAP","BPG","3PG","2PG","PEP","PYR",
               "ATP","ADP","NAD","NADH"]
    conc    = np.array([1.0, 0.083, 0.014, 0.031, 0.019, 0.001, 0.12,
                        0.03, 0.023, 0.051, 2.0, 0.05, 0.5, 0.05])
    H_cat   = np.array([1.990, 5.581, 8.148, 7.001, 7.708, 11.956, 5.049,
                        7.049, 7.432, 6.283, 0.990, 6.312, 2.990, 6.312])
    mu_norm = np.array([-0.0, 3.591, 6.158, 5.012, 5.718, 9.966, 3.059,
                         5.059, 5.442, 4.293, -1.0, 4.322, 1.0, 4.322])
    n = len(species)
    log_conc = np.log10(conc)

    fig, axes = plt.subplots(1, 4, figsize=(16, 4),
                             subplot_kw=None)
    fig.patch.set_facecolor('white')

    # Chart 1 — 2D scatter: log10(conc) vs H_cat, size~conc
    ax = axes[0]
    sizes  = 20 + 200 * (conc / conc.max())
    colors = viridis(H_cat / 12)
    ax.scatter(log_conc, H_cat, s=sizes, c=colors)
    _tickparams(ax)

    # Chart 2 — 2D scatter: mu_norm vs H_cat, color by species index
    ax = axes[1]
    for i in range(n):
        ax.scatter(mu_norm[i], H_cat[i], color=viridis(i / 14), s=30, zorder=3)
    x_ref = np.linspace(mu_norm.min(), mu_norm.max(), 100)
    ax.plot(x_ref, x_ref + 1.99, color='gray', lw=0.8, zorder=2)
    _tickparams(ax)

    # Chart 3 — 3D scatter: log10(conc), H_cat, mu_norm
    ax3 = fig.add_subplot(1, 4, 3, projection='3d')
    axes[2].remove()
    axes[2] = ax3
    sc = ax3.scatter(log_conc, H_cat, mu_norm,
                     c=H_cat / 12, cmap='viridis', s=40)
    _set_3d_white_panes(ax3)
    ax3.tick_params(labelsize=6)

    # Chart 4 — 2D horizontal bar: sorted by H_cat
    ax = axes[3]
    order  = np.argsort(H_cat)
    sorted_H   = H_cat[order]
    sorted_lbl = [species[i][:3] for i in order]
    bar_colors = plasma(sorted_H / 12)
    ax.barh(range(n), sorted_H, color=bar_colors, height=0.7)
    ax.set_yticks(range(n))
    ax.set_yticklabels(sorted_lbl)
    _tickparams(ax, rotation=0)

    plt.tight_layout(pad=0.5)
    out = os.path.join(FIGURES_DIR, 'panel_exp1.png')
    plt.savefig(out, dpi=150, bbox_inches='tight', facecolor='white')
    plt.close(fig)
    print(f'Saved {out}')


# ===========================================================================
# PANEL 2 — Kirchhoff KCL
# ===========================================================================
def panel_exp2():
    sp_names = ["GLC","G6P","F6P","FBP","GAP","BPG","3PG","2PG","PEP","PYR"]
    conc     = np.array([1.00017, 0.08300, 0.01400, 0.03100, 0.01900,
                         0.00100, 0.12000, 0.03000, 0.02300, 0.07295])
    net_flux = np.array([-1.55e-6, -1.54e-8, -2.28e-9, -5.81e-9, -3.76e-9,
                          1.58e-10, -3.91e-8, -5.75e-9, -4.19e-9, 1.63e-6])
    enz_flux = np.array([0.10000, 0.10001, 0.10001, 0.10001, 0.10002,
                         0.10002, 0.10002, 0.10002, 0.10002])
    n_sp = len(conc)
    n_ez = len(enz_flux)
    sp_idx  = np.arange(n_sp)
    ez_idx  = np.arange(n_ez)

    fig, axes = plt.subplots(1, 4, figsize=(16, 4))
    fig.patch.set_facecolor('white')

    # Chart 1 — 2D bar: SS concentrations
    ax = axes[0]
    ax.bar(sp_idx, conc, color=viridis(conc / conc.max()))
    ax.set_xticks(sp_idx)
    ax.set_xticklabels([s[:3] for s in sp_names], rotation=45, ha='right', fontsize=6)
    _tickparams(ax)

    # Chart 2 — 2D bar: |net_flux| log10 scale
    ax = axes[1]
    abs_flux = np.abs(net_flux)
    abs_flux = np.clip(abs_flux, 1e-12, None)
    ax.bar(sp_idx, np.log10(abs_flux), color=viridis(sp_idx / n_sp))
    ax.set_xticks(sp_idx)
    ax.set_xticklabels([s[:3] for s in sp_names], rotation=45, ha='right', fontsize=6)
    _tickparams(ax)

    # Chart 3 — 3D bar: enzyme index vs enzyme_flux vs SS_conc[0:9]
    ax3 = fig.add_subplot(1, 4, 3, projection='3d')
    axes[2].remove()
    axes[2] = ax3
    z_conc = conc[:n_ez]
    dx = dy = 0.4
    colors3d = [viridis(i / n_ez) for i in ez_idx]
    for i in ez_idx:
        ax3.bar3d(i - dx/2, enz_flux[i] - dy/2, 0,
                  dx, dy, z_conc[i],
                  color=colors3d[i], alpha=0.8)
    _set_3d_white_panes(ax3)
    ax3.tick_params(labelsize=6)

    # Chart 4 — 2D scatter: enzyme index vs enzyme_flux
    ax = axes[3]
    ax.plot(ez_idx, enz_flux, color='gray', lw=0.8, zorder=2)
    ax.scatter(ez_idx, enz_flux, color=[viridis(i / n_ez) for i in ez_idx],
               s=40, zorder=3)
    ax.set_xticks(ez_idx)
    _tickparams(ax)

    plt.tight_layout(pad=0.5)
    out = os.path.join(FIGURES_DIR, 'panel_exp2.png')
    plt.savefig(out, dpi=150, bbox_inches='tight', facecolor='white')
    plt.close(fig)
    print(f'Saved {out}')


# ===========================================================================
# PANEL 3 — Backward Trajectory Time-Invariance
# ===========================================================================
def panel_exp3():
    t_query = np.array([50.0, 100.0, 150.0])
    cos_sim = np.array([0.999964, 0.999899, 0.999977])
    rmsds   = np.array([0.111, 0.160, 0.100])

    # starting states: rows = [t1, t2, t3], columns = species 0-9
    starts = np.array([
        [1.777, 0.0875, 0.01467, 0.03271, 0.02011, 0.001043, 0.1317, 0.03166, 0.02420, 0.623],
        [1.587, 0.0868, 0.01456, 0.03244, 0.01993, 0.001036, 0.1298, 0.03140, 0.02401, 0.817],
        [1.429, 0.0861, 0.01445, 0.03216, 0.01975, 0.001029, 0.1279, 0.03113, 0.02382, 0.978],
    ])
    # backward endpoints
    backs = np.array([
        [1.863, 1e-10, 22.16, 1e-10, 5.651, 1e-10, 3.439, 1e-10, 9.697, 1e-10],
        [1.659, 1e-10, 21.97, 1e-10, 5.604, 1e-10, 3.432, 1e-10, 9.688, 1e-10],
        [1.488, 1e-10, 22.17, 1e-10, 5.654, 1e-10, 3.433, 1e-10, 9.703, 1e-10],
    ])

    colors3 = ['#1f77b4', '#ff7f0e', '#2ca02c']

    fig, axes = plt.subplots(1, 4, figsize=(16, 4))
    fig.patch.set_facecolor('white')

    # Chart 1 — 2D scatter: GLC(0) vs PYR(9) for 3 starting states
    ax = axes[0]
    for i in range(3):
        ax.scatter(starts[i, 0], starts[i, 9], color=colors3[i], s=80, marker='o')
    _tickparams(ax)

    # Chart 2 — 2D bar: cosine_similarities
    ax = axes[1]
    bar_c = [viridis(v) for v in [0.2, 0.5, 0.8]]
    ax.bar(np.arange(3), cos_sim, color=bar_c)
    ax.set_xticks(np.arange(3))
    ax.set_xticklabels(['t1', 't2', 't3'], fontsize=6)
    _tickparams(ax)

    # Chart 3 — 3D scatter: GLC(0), F6P(2), PEP(8) for starts + backs
    ax3 = fig.add_subplot(1, 4, 3, projection='3d')
    axes[2].remove()
    axes[2] = ax3
    for i in range(3):
        # starting state
        ax3.scatter(starts[i, 0], starts[i, 2], starts[i, 8],
                    color=colors3[i], s=50, marker='o', zorder=3)
        # backward endpoint (clip tiny values for display)
        bx = backs[i, 0]
        by = max(backs[i, 2], 1e-4)
        bz = max(backs[i, 8], 1e-4)
        ax3.scatter(bx, by, bz,
                    color=colors3[i], s=50, marker='*', zorder=3)
        # connect pair
        ax3.plot([starts[i,0], bx], [starts[i,2], by], [starts[i,8], bz],
                 color=colors3[i], lw=0.8)
    _set_3d_white_panes(ax3)
    ax3.tick_params(labelsize=6)

    # Chart 4 — 2D scatter: rmsds vs t_query
    ax = axes[3]
    ax.scatter(t_query, rmsds, color=[plasma(v) for v in [0.3, 0.6, 0.9]],
               marker='D', s=80)
    _tickparams(ax)

    plt.tight_layout(pad=0.5)
    out = os.path.join(FIGURES_DIR, 'panel_exp3.png')
    plt.savefig(out, dpi=150, bbox_inches='tight', facecolor='white')
    plt.close(fig)
    print(f'Saved {out}')


# ===========================================================================
# PANEL 4 — Fuzzy State Completion
# ===========================================================================
def panel_exp4():
    sp_names  = ["G6P","F6P","FBP","GAP","BPG","3PG","2PG","PEP"]
    true_vals = np.array([0.083, 0.014, 0.031, 0.019, 0.001, 0.12, 0.03, 0.023])
    comp_vals = np.array([0.08300, 0.01400, 0.03100, 0.01900, 0.00100,
                          0.12000, 0.03000, 0.02300])
    prior_val = np.full(8, 0.1)
    rel_err_c = np.array([2.6e-10, 1.0e-10, 4.0e-10, 1.8e-10, 8.5e-13,
                          2.5e-10, 1.9e-10, 3.0e-10])
    rel_err_n = np.array([0.205, 6.143, 2.226, 4.263, 99.0, 0.167, 2.333, 3.348])

    n = 8
    idx = np.arange(n)
    w = 0.35

    fig, axes = plt.subplots(1, 4, figsize=(16, 4))
    fig.patch.set_facecolor('white')

    # Chart 1 — 2D grouped bar: true (viridis) and prior (gray)
    ax = axes[0]
    for i in idx:
        ax.bar(i - w/2, true_vals[i], width=w, color=viridis(i / 8))
        ax.bar(i + w/2, prior_val[i], width=w, color='#aaaaaa')
    ax.set_xticks(idx)
    ax.set_xticklabels([s[:3] for s in sp_names], rotation=45, ha='right', fontsize=6)
    _tickparams(ax)

    # Chart 2 — 2D scatter: true vs completed, y=x reference
    ax = axes[1]
    for i in idx:
        ax.scatter(true_vals[i], comp_vals[i], color=viridis(i / 8), s=40, zorder=3)
    ref = np.linspace(true_vals.min(), true_vals.max(), 100)
    ax.plot(ref, ref, color='gray', lw=0.8, zorder=2)
    _tickparams(ax)

    # Chart 3 — 3D scatter: species index, true_value, completed_value
    ax3 = fig.add_subplot(1, 4, 3, projection='3d')
    axes[2].remove()
    axes[2] = ax3
    ax3.scatter(idx, true_vals, comp_vals,
                c=idx / n, cmap='viridis', s=40)
    _set_3d_white_panes(ax3)
    ax3.tick_params(labelsize=6)

    # Chart 4 — 2D bar log scale: naive (orange) and completion (blue)
    ax = axes[3]
    w2 = 0.35
    naive_plot = np.clip(rel_err_n, 1e-12, None)
    comp_plot  = np.clip(rel_err_c, 1e-12, None)
    ax.bar(idx - w2/2, naive_plot, width=w2, color='orange', label='naive')
    ax.bar(idx + w2/2, comp_plot,  width=w2, color=viridis(0.3), label='completion')
    ax.set_yscale('log')
    ax.set_xticks(idx)
    ax.set_xticklabels([s[:3] for s in sp_names], rotation=45, ha='right', fontsize=6)
    _tickparams(ax)

    plt.tight_layout(pad=0.5)
    out = os.path.join(FIGURES_DIR, 'panel_exp4.png')
    plt.savefig(out, dpi=150, bbox_inches='tight', facecolor='white')
    plt.close(fig)
    print(f'Saved {out}')


# ===========================================================================
# PANEL 5 — Signal vs Drift Velocity
# ===========================================================================
def panel_exp5():
    mechs    = ["HK","PGI","PFK","ALD","GAPDH","PGK","PGM","ENO","PK","hbond"]
    k_cat    = [100, 2000, 200, 300, 500, 700, 400, 600, 400, None]
    v_signal = np.array([0.001, 0.02, 0.002, 0.003, 0.005, 0.007, 0.004,
                         0.006, 0.004, 70510921587946.27])
    v_drift  = np.array([1e-5, 1e-5, 1e-5, 1e-5, 1e-5, 1e-5, 1e-5, 1e-5,
                         1e-5, 2.3e-4])
    ratios   = np.array([100, 2000, 200, 300, 500, 700, 400, 600, 400, 3.07e17])

    n_all = 10
    # enzymatic only (exclude hbond at index 9)
    enz_idx    = np.arange(9)
    k_cat_enz  = np.array([100, 2000, 200, 300, 500, 700, 400, 600, 400], dtype=float)
    v_sig_enz  = v_signal[:9]
    rat_enz    = ratios[:9]

    idx_all = np.arange(n_all)
    idx_lbl = [m[:3] for m in mechs]

    fig, axes = plt.subplots(1, 4, figsize=(16, 4))
    fig.patch.set_facecolor('white')

    # Chart 1 — 2D bar log scale: v_signal for all 10
    ax = axes[0]
    vs_clip = np.clip(v_signal, 1e-12, None)
    ax.bar(idx_all, vs_clip, color=[viridis(i / n_all) for i in idx_all])
    ax.set_yscale('log')
    ax.set_xticks(idx_all)
    ax.set_xticklabels(idx_lbl, rotation=45, ha='right', fontsize=6)
    _tickparams(ax)

    # Chart 2 — 2D bar: log10(ratio) for all 10
    ax = axes[1]
    log_rat = np.log10(np.clip(ratios, 1e-12, None))
    ax.bar(idx_all, log_rat, color=[plasma(i / n_all) for i in idx_all])
    ax.set_xticks(idx_all)
    ax.set_xticklabels(idx_lbl, rotation=45, ha='right', fontsize=6)
    _tickparams(ax)

    # Chart 3 — 3D scatter: enzymatic only, k_cat vs v_signal vs ratio
    ax3 = fig.add_subplot(1, 4, 3, projection='3d')
    axes[2].remove()
    axes[2] = ax3
    ax3.scatter(k_cat_enz, v_sig_enz, rat_enz,
                c=enz_idx / 9, cmap='viridis', s=40)
    _set_3d_white_panes(ax3)
    ax3.tick_params(labelsize=6)

    # Chart 4 — 2D scatter log-log: v_drift vs v_signal, y=x reference
    ax = axes[3]
    vs_clip2 = np.clip(v_signal, 1e-12, None)
    vd_clip  = np.clip(v_drift,  1e-12, None)
    for i in idx_all:
        ax.scatter(vd_clip[i], vs_clip2[i], color=viridis(i / n_all), s=40, zorder=3)
    ref_min = min(vd_clip.min(), vs_clip2.min())
    ref_max = max(vd_clip.max(), vs_clip2.max())
    ref = np.logspace(np.log10(ref_min), np.log10(ref_max), 100)
    ax.plot(ref, ref, color='gray', lw=0.8, zorder=2)
    ax.set_xscale('log')
    ax.set_yscale('log')
    _tickparams(ax)

    plt.tight_layout(pad=0.5)
    out = os.path.join(FIGURES_DIR, 'panel_exp5.png')
    plt.savefig(out, dpi=150, bbox_inches='tight', facecolor='white')
    plt.close(fig)
    print(f'Saved {out}')


# ===========================================================================
# PANEL 6 — Disease Detection
# ===========================================================================
def panel_exp6():
    sp_names   = ["GLC","G6P","F6P","FBP","GAP","BPG","3PG","2PG","PEP","PYR"]
    healthy    = np.array([1.0, 0.083, 0.014, 0.031, 0.019, 0.001, 0.120,
                           0.030, 0.023, 0.051])
    disease_hk = np.array([43.33, 0.00719, 0.00137, 0.00267, 0.00156, 0.000108,
                           0.00637, 0.00260, 0.00210, 1e-10])
    disease_pf = np.array([1.0, 10.66, 1.792, 0.02233, 0.01348, 0.000768,
                           0.07261, 0.02165, 0.01685, 1e-10])

    n = 10
    idx = np.arange(n)
    c_h  = viridis(0.2)
    c_hk = viridis(0.6)
    c_pf = viridis(0.9)

    # clip near-zero to 1e-12 for log bars
    h_plot  = np.clip(healthy,    1e-12, None)
    hk_plot = np.clip(disease_hk, 1e-12, None)
    pf_plot = np.clip(disease_pf, 1e-12, None)

    fig, axes = plt.subplots(1, 4, figsize=(16, 4))
    fig.patch.set_facecolor('white')

    # Chart 1 — 2D grouped bar log scale: 3 conditions, 10 species
    ax = axes[0]
    w = 0.25
    ax.bar(idx - w, h_plot,  width=w, color=c_h,  log=True)
    ax.bar(idx,     hk_plot, width=w, color=c_hk, log=True)
    ax.bar(idx + w, pf_plot, width=w, color=c_pf, log=True)
    ax.set_yscale('log')
    ax.set_xticks(idx)
    ax.set_xticklabels([s[:3] for s in sp_names], rotation=45, ha='right', fontsize=6)
    _tickparams(ax)

    # Chart 2 — 2D scatter log-log: healthy vs disease_HK
    ax = axes[1]
    for i in idx:
        ax.scatter(h_plot[i], hk_plot[i], color=viridis(i / n), s=40, zorder=3)
    ref_min = min(h_plot.min(), hk_plot.min())
    ref_max = max(h_plot.max(), hk_plot.max())
    ref = np.logspace(np.log10(ref_min), np.log10(ref_max), 100)
    ax.plot(ref, ref, color='gray', lw=0.8, zorder=2)
    ax.set_xscale('log')
    ax.set_yscale('log')
    _tickparams(ax)

    # Chart 3 — 3D scatter: log10 of clipped values
    ax3 = fig.add_subplot(1, 4, 3, projection='3d')
    axes[2].remove()
    axes[2] = ax3
    h_log  = np.log10(np.clip(healthy,    1e-4, None))
    hk_log = np.log10(np.clip(disease_hk, 1e-4, None))
    pf_log = np.log10(np.clip(disease_pf, 1e-4, None))
    ax3.scatter(h_log, hk_log, pf_log,
                c=idx / n, cmap='plasma', s=40)
    _set_3d_white_panes(ax3)
    ax3.tick_params(labelsize=6)

    # Chart 4 — 2D bar log scale: coherence eta for 3 conditions
    ax = axes[3]
    # 2.2e-49 displayed as 1e-49 minimum clip
    eta = np.clip([1.0, 1e-12, 2.2e-49], 1e-60, None)
    ax.bar(np.arange(3), eta,
           color=[c_h, c_hk, c_pf])
    ax.set_yscale('log')
    ax.set_xticks(np.arange(3))
    ax.set_xticklabels(['H', 'HK', 'PFK'], fontsize=6)
    _tickparams(ax)

    plt.tight_layout(pad=0.5)
    out = os.path.join(FIGURES_DIR, 'panel_exp6.png')
    plt.savefig(out, dpi=150, bbox_inches='tight', facecolor='white')
    plt.close(fig)
    print(f'Saved {out}')


# ===========================================================================
# Main
# ===========================================================================
if __name__ == '__main__':
    panel_exp1()
    panel_exp2()
    panel_exp3()
    panel_exp4()
    panel_exp5()
    panel_exp6()
    print('All panels generated in:', FIGURES_DIR)

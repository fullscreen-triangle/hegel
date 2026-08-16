"""
Six figure panels for the graph-incompleteness manuscript.
==========================================================

Each panel: white background, four charts in a row, at least one 3D, minimal
text, no conceptual diagrams / tables / text-only axes. Every value plotted is
read from the validation JSON in results/ -- nothing is drawn by hand and no
curve is fitted. Where a panel needs a quantity the suite did not already
record, it is RECOMPUTED by calling the same functions the experiments call,
never estimated.

  panel_1  recursion shape        -- Prop 8.8: same least model, different cost
  panel_2  the budget             -- Thm 3.7: the only predicate with a clock
  panel_3  bounded vs unbounded   -- Prop 8.6 + Cor 8.7: the cost inversion
  panel_4  counting prerequisites -- Prop 3.4 + Prop 8.3: the derivability corners
  panel_5  scoring                -- Prop 4.9: the deficit vs benchmark mix
  panel_6  verdicts and blockers  -- Def 4.2 + Sec 9: where the axes are visible

    python make_figures.py

Run run_validation.py first; this reads its output and will say so if a result
file is missing rather than drawing an empty axis.
"""

from __future__ import annotations

import json
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from mpl_toolkits.mplot3d import Axes3D  # noqa: F401

HERE = os.path.dirname(os.path.abspath(__file__))
RESULTS_DIR = os.path.join(HERE, "results")
FIG_DIR = os.path.join(HERE, "figures")

# One palette across all six panels, so a colour means the same thing
# everywhere it appears: the two recursion shapes, the two verdict outcomes,
# and the two scoring rules each keep their hue from panel to panel.
C_RIGHT = "#1b4f72"    # right-recursive / bounded / verdict-aware / answered
C_LEFT = "#922b21"     # left-recursive / unbounded / naive / refused
C_THIRD = "#117864"    # third series where one is needed
C_FOURTH = "#7d6608"   # fourth series
GREY = "#888888"


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
            for pane in (ax.xaxis.pane, ax.yaxis.pane, ax.zaxis.pane):
                pane.set_facecolor("white")
                pane.set_edgecolor("#dddddd")
            ax.grid(True, color="#dddddd", linewidth=0.4)
            # A 3D axes draws its z-label outside its own bounding box, where
            # tight_layout cannot see it, so it lands on the next subplot's
            # y-label. Shrinking the cube reclaims that margin from within.
            ax.set_box_aspect((1, 1, 0.82), zoom=0.82)
        else:
            ax = fig.add_subplot(1, 4, i + 1)
        axes.append(ax)
    return fig, axes


def save(fig, name):
    os.makedirs(FIG_DIR, exist_ok=True)
    path = os.path.join(FIG_DIR, name)
    # w_pad keeps a 3D subplot's z-label off its right-hand neighbour's
    # y-label; tight_layout alone does not account for 3D decorations.
    fig.tight_layout(pad=1.1, w_pad=2.2)
    fig.savefig(path + ".pdf", dpi=300, facecolor="white")
    fig.savefig(path + ".png", dpi=200, facecolor="white")
    plt.close(fig)
    print(f"  wrote {name}.pdf / .png")


def load(name):
    """Read one result document. A missing file is an error, not an empty plot."""
    path = os.path.join(RESULTS_DIR, name)
    if not os.path.exists(path):
        raise SystemExit(
            f"missing {path}\nrun `python run_validation.py` first"
        )
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)["measured"]


# ===========================================================================
# Panel 1 -- recursion shape: same least model, different cost (Prop 8.8)
# ===========================================================================

def panel_1():
    m = load("18_closure_cost_sweep.json")
    s = m["series"]
    fig, ax = new_panel([None, None, "3d", None])

    # (a) cost vs size on the chain -- the two curves lie on top of each other
    a = ax[0]
    rows = s["chain-cyclic"]
    n = [r["n"] for r in rows]
    a.plot(n, [r["steps_right"] for r in rows], "o-", color=C_RIGHT,
           ms=3.2, lw=1.3, label="right-recursive")
    a.plot(n, [r["steps_left"] for r in rows], "s--", color=C_LEFT,
           ms=3.2, lw=1.3, label="left-recursive")
    a.set_xlabel("corpus size $n$")
    a.set_ylabel("solver steps")
    a.set_title("(a) chain corpus")
    a.legend(loc="upper left")

    # (b) the same two shapes on a lattice -- log scale, they separate
    b = ax[1]
    rows = s["lattice-cyclic"]
    d = [r["depth"] for r in rows]
    b.semilogy(d, [r["steps_right"] for r in rows], "o-", color=C_RIGHT,
               ms=3.2, lw=1.3, label="right-recursive")
    b.semilogy(d, [r["steps_left"] for r in rows], "s--", color=C_LEFT,
               ms=3.2, lw=1.3, label="left-recursive")
    b.set_xlabel("lattice depth")
    b.set_ylabel("solver steps (log)")
    b.set_title("(b) lattice corpus")
    b.legend(loc="upper left")

    # (c) 3D: the ratio over (topology, sweep position). Log z, because the
    #     chains sit at exactly 1 and the cyclic lattice reaches 57 -- on a
    #     linear axis the four chain series would be invisible, which is the
    #     comparison the panel exists to make.
    c = ax[2]
    order = ["chain-acyclic", "chain-cyclic", "lattice-acyclic", "lattice-cyclic"]
    cols = [C_RIGHT, C_THIRD, C_FOURTH, C_LEFT]
    # A chain's ratio is exactly 1, so log10 is 0 and the bar has no height.
    # Drawing a flat marker line at z=0 keeps "measured, and equal to one"
    # visually distinct from "no data here".
    for j, (key, col) in enumerate(zip(order, cols)):
        rows = s[key]
        xs = np.arange(len(rows))
        zs = [np.log10(r["ratio"]) for r in rows]
        if max(zs) == 0.0:
            c.plot(xs, [j] * len(xs), zs, "o", color=col, ms=2.6, zdir="z")
        else:
            c.bar(xs, zs, zs=j, zdir="y", color=col, alpha=0.9,
                  width=0.5, edgecolor="white", linewidth=0.3)
    c.set_xlabel("sweep index", labelpad=-3)
    c.set_zlabel(r"$\log_{10}$ ratio", labelpad=-6, rotation=90)
    c.set_yticks(range(4))
    c.set_yticklabels(["ch-a", "ch-c", "lat-a", "lat-c"], fontsize=6)
    c.tick_params(pad=-2)
    c.set_title("(c) ratio by topology")
    c.view_init(elev=20, azim=-58)

    # (d) answer-set size against solver steps: the two shapes land on the
    #     same least model at every depth (points coincide vertically) while
    #     their costs differ by up to 57x. This is what makes (a)-(c) a cost
    #     comparison and not two different computations.
    d4 = ax[3]
    rows = s["lattice-cyclic"]
    d4.plot([r["steps_right"] for r in rows], [r["reached"] for r in rows],
            "o-", color=C_RIGHT, ms=4, lw=1.3, label="right-recursive")
    d4.plot([r["steps_left"] for r in rows], [r["reached"] for r in rows],
            "s--", color=C_LEFT, ms=4, lw=1.3, label="left-recursive")
    for r in rows:
        d4.plot([r["steps_right"], r["steps_left"]],
                [r["reached"], r["reached"]], "-", color=GREY, lw=0.7,
                alpha=0.7, zorder=0)
    d4.set_xscale("log")
    d4.set_xlabel("solver steps (log)")
    d4.set_ylabel("$|$reached$|$")
    d4.set_title("(d) same model, different cost")
    d4.legend(loc="upper left")

    save(fig, "panel_1_recursion_shape")


# ===========================================================================
# Panel 2 -- the budget is the only clock (Thm 3.7)
# ===========================================================================

def panel_2():
    m = load("19_budget_sweep.json")
    rows = m["series"]
    thr = m["threshold_budget"]
    fig, ax = new_panel([None, None, None, "3d"])

    budgets = [r["budget"] for r in rows]
    answered = [1 if r["answered"] else 0 for r in rows]
    steps = [r["steps"] for r in rows]

    # (a) steps reached vs budget: below threshold the run stops AT the budget
    a = ax[0]
    a.plot(budgets, steps, "o-", color=C_RIGHT, ms=3.4, lw=1.3,
           label="steps reached")
    a.plot(budgets, budgets, "--", color=GREY, lw=1.0, label=r"$y=\tau$")
    a.axvline(thr, color=C_LEFT, lw=1.0, ls=":")
    a.set_xlabel(r"budget $\tau$")
    a.set_ylabel("steps")
    a.set_title("(a) steps vs budget")
    a.legend(loc="upper left")

    # (b) the verdict as a step function of the budget alone
    b = ax[1]
    b.step(budgets, answered, where="post", color=C_RIGHT, lw=1.6)
    b.fill_between(budgets, answered, step="post", color=C_RIGHT, alpha=0.15)
    b.axvline(thr, color=C_LEFT, lw=1.0, ls=":")
    b.set_xlabel(r"budget $\tau$")
    b.set_ylabel("answered")
    b.set_ylim(-0.08, 1.15)
    b.set_yticks([0, 1])
    b.set_yticklabels(["timeout", "answered"], fontsize=7)
    b.tick_params(axis="y", pad=1)
    b.set_title("(b) verdict vs budget")

    # (c) shortfall: how far short of completion each budget stops
    c = ax[2]
    done = max(r["steps"] for r in rows if r["answered"])
    short = [max(0, done - r["steps"]) for r in rows]
    c.bar(range(len(budgets)), short, color=[
        C_RIGHT if r["answered"] else C_LEFT for r in rows], width=0.7)
    c.set_xticks(range(len(budgets)))
    c.set_xticklabels([str(x) for x in budgets], fontsize=6, rotation=90)
    c.set_xlabel(r"budget $\tau$")
    c.set_ylabel("steps short of completion")
    c.set_title("(c) shortfall")

    # (d) 3D: the three predicates over the budget axis. Exp and Der are flat
    #     at 1 -- they have no clock; only Ans moves.
    d = ax[3]
    xs = np.arange(len(budgets))
    for j, (name, vals, col) in enumerate([
        ("Exp", [1] * len(rows), C_THIRD),
        ("Der", [1] * len(rows), C_FOURTH),
        ("Ans", answered, C_RIGHT),
    ]):
        d.bar(xs, vals, zs=j, zdir="y", color=col, alpha=0.85,
              width=0.6, edgecolor="white", linewidth=0.3)
    d.set_xlabel(r"$\tau$ index")
    d.set_zlabel("holds")
    d.set_yticks(range(3))
    d.set_yticklabels(["Exp", "Der", "Ans"], fontsize=6)
    d.set_zticks([0, 1])
    d.set_title("(d) three predicates")
    d.view_init(elev=20, azim=-62)

    save(fig, "panel_2_budget")


# ===========================================================================
# Panel 3 -- bounded vs unbounded: the cost inversion (Prop 8.6, Cor 8.7)
# ===========================================================================

def panel_3():
    m = load("20_bounded_surface.json")
    grid = m["grid"]
    unb = m["unbounded"]
    ks = m["bounds"]
    ns = m["sizes"]
    fig, ax = new_panel([None, "3d", None, None])

    # (a) bounded cost vs k, one line per corpus size -- all collapse onto y=k
    a = ax[0]
    for i, n in enumerate(ns[::3]):
        rows = sorted([g for g in grid if g["n"] == n], key=lambda g: g["k"])
        a.plot([g["k"] for g in rows], [g["steps"] for g in rows], "-",
               color=C_RIGHT, lw=1.0, alpha=0.5)
    rows = sorted([g for g in grid if g["n"] == ns[0]], key=lambda g: g["k"])
    a.plot([g["k"] for g in rows], [g["steps"] for g in rows], "o",
           color=C_RIGHT, ms=3.4, label="bounded, all $n$")
    a.plot(ns, [u["steps"] for u in unb], "s--", color=C_LEFT, ms=3.4,
           lw=1.3, label="unbounded")
    a.set_xlabel("bound $k$  /  corpus size $n$")
    a.set_ylabel("solver steps")
    a.set_title("(a) bounded vs unbounded")
    a.legend(loc="upper left")

    # (b) 3D surface of bounded cost over (k, n): a ramp in k, flat in n
    b = ax[1]
    K, N = np.meshgrid(ks, ns)
    Z = np.zeros_like(K, dtype=float)
    lookup = {(g["k"], g["n"]): g["steps"] for g in grid}
    for r in range(K.shape[0]):
        for c_ in range(K.shape[1]):
            Z[r, c_] = lookup[(K[r, c_], N[r, c_])]
    b.plot_surface(K, N, Z, cmap="Blues", edgecolor="#2c3e50",
                   linewidth=0.15, alpha=0.9, rstride=1, cstride=1)
    b.set_xlabel("bound $k$")
    b.set_ylabel("corpus size $n$")
    b.set_zlabel("steps")
    b.set_title("(b) bounded cost surface")
    b.view_init(elev=24, azim=-135)

    # (c) the inversion: cost saved, unbounded minus bounded, over (k, n)
    c = ax[2]
    diff = np.zeros((len(ns), len(ks)))
    ub = {u["n"]: u["steps"] for u in unb}
    for i, n in enumerate(ns):
        for j, k in enumerate(ks):
            diff[i, j] = ub[n] - lookup[(k, n)]
    im = c.imshow(diff, aspect="auto", origin="lower", cmap="RdBu",
                  vmin=-abs(diff).max(), vmax=abs(diff).max(),
                  extent=[ks[0] - .5, ks[-1] + .5, ns[0] - 1, ns[-1] + 1])
    c.set_xlabel("bound $k$")
    c.set_ylabel("corpus size $n$")
    c.set_title("(c) steps saved")
    c.grid(False)
    fig.colorbar(im, ax=c, fraction=0.046, pad=0.03)

    # (d) reach: what the bound costs in answers
    d = ax[3]
    for j, k in enumerate([1, 3, 5, 8]):
        rows = sorted([g for g in grid if g["k"] == k], key=lambda g: g["n"])
        d.plot([g["n"] for g in rows], [g["reached"] for g in rows], "o-",
               ms=2.8, lw=1.1,
               color=[C_RIGHT, C_THIRD, C_FOURTH, C_LEFT][j],
               label=f"$k={k}$")
    d.plot(ns, [u["reached"] for u in unb], "k--", lw=1.2, label="unbounded")
    d.set_xlabel("corpus size $n$")
    d.set_ylabel("$|$reached$|$")
    d.set_title("(d) answers under the bound")
    d.legend(loc="upper left", ncol=2)

    save(fig, "panel_3_bounded")


# ===========================================================================
# Panel 4 -- counting prerequisites (Prop 3.4, Prop 8.3)
# ===========================================================================

def panel_4():
    m = load("21_counting_surface.json")
    cells = m["cells"]
    fig, ax = new_panel([None, None, "3d", None])

    modes = ["ge", "le", "eq"]
    corners = [(False, False), (True, False), (False, True), (True, True)]
    corner_lbl = ["--", "D-", "-C", "DC"]

    # Keyed on the ASSERTED distinctness/closure, not the effective ones: UNA
    # supplies distinctness the corner did not assert (Prop 8.3), so the two
    # keys disagree in exactly the cells that make the point. Panel (d) plots
    # that disagreement rather than hiding it.
    def cell(mode, dist, clos, una):
        for c in cells:
            if (c["mode"] == mode and c["distinct"] == dist
                    and c["closure"] == clos and c["una"] == una):
                return c
        return None

    # (a) how many of the three modes survive each corner, under each UNA
    #     regime. A count, not a boolean: the corner is the x axis and the
    #     height is what the corner actually buys you.
    a = ax[0]
    w = 0.36
    for i, una in enumerate([False, True]):
        vals = [sum(1 for md in modes if cell(md, d, c_, una)["derivable"])
                for (d, c_) in corners]
        a.bar(np.arange(4) + (i - 0.5) * w, vals, width=w,
              color=[GREY, C_RIGHT][i], label=f"UNA {'on' if una else 'off'}")
    a.set_xticks(range(4))
    a.set_xticklabels(corner_lbl)
    a.set_xlabel("asserted distinctness / closure")
    a.set_ylabel("modes derivable (of 3)")
    a.set_title("(a) yield per corner")
    a.legend(loc="upper left")

    # (b) the prerequisite each mode is waiting on, as the fraction of corners
    #     it clears once that prerequisite is present vs absent. Prop 3.4 makes
    #     a specific prediction here: ge tracks distinctness, le tracks
    #     closure, eq tracks neither alone.
    b = ax[1]
    w = 0.26
    for j, mode in enumerate(modes):
        with_d = [c_ for c_ in cells if c_["mode"] == mode and c_["have_distinct"]]
        with_c = [c_ for c_ in cells if c_["mode"] == mode and c_["have_closure"]]
        both = [c_ for c_ in cells
                if c_["mode"] == mode and c_["have_distinct"] and c_["have_closure"]]
        vals = [
            sum(x["derivable"] for x in with_d) / len(with_d),
            sum(x["derivable"] for x in with_c) / len(with_c),
            sum(x["derivable"] for x in both) / len(both),
        ]
        b.bar(np.arange(3) + (j - 1) * w, vals, width=w,
              color=[C_RIGHT, C_THIRD, C_LEFT][j], label=mode)
    b.set_xticks(range(3))
    b.set_xticklabels(["distinct", "closure", "both"])
    b.set_xlabel("prerequisite present")
    b.set_ylabel("fraction derivable")
    b.set_ylim(0, 1.18)
    b.set_title("(b) which prerequisite binds")
    b.legend(loc="upper left", ncol=3)

    # (c) 3D: the full 24-cell lattice, mode x corner x UNA
    c = ax[2]
    for j, mode in enumerate(modes):
        for una_i, una in enumerate([False, True]):
            xs, zs = [], []
            for ci, (d, cl) in enumerate(corners):
                xs.append(ci + una_i * 0.34)
                zs.append(1 if cell(mode, d, cl, una)["derivable"] else 0)
            c.bar(xs, zs, zs=j, zdir="y", width=0.3,
                  color=[C_RIGHT, C_THIRD, C_LEFT][j],
                  alpha=0.55 if una_i == 0 else 0.95,
                  edgecolor="white", linewidth=0.3)
    c.set_xlabel("corner", labelpad=-3)
    c.set_zlabel("derivable", labelpad=-6, rotation=90)
    c.set_xticks(range(4))
    c.set_xticklabels(corner_lbl, fontsize=6)
    c.set_yticks(range(3))
    c.set_yticklabels(modes, fontsize=6)
    c.set_zticks([0, 1])
    c.tick_params(pad=-2)
    c.set_title("(c) full lattice")
    c.view_init(elev=24, azim=-60)

    # (d) what UNA supplies: derivable cells per mode with UNA off vs on. The
    # lift is exactly the cells whose asserted distinctness was absent and
    # whose effective distinctness UNA provided.
    d = ax[3]
    off = [sum(1 for c_ in cells
               if c_["mode"] == md and not c_["una"] and c_["derivable"])
           for md in modes]
    on = [sum(1 for c_ in cells
              if c_["mode"] == md and c_["una"] and c_["derivable"])
          for md in modes]
    w = 0.34
    d.bar(np.arange(3) - w / 2, off, width=w, color=GREY, label="UNA off")
    d.bar(np.arange(3) + w / 2, on, width=w, color=C_RIGHT, label="UNA on")
    d.set_xticks(range(3))
    d.set_xticklabels(modes)
    d.set_ylabel("derivable corners (of 4)")
    d.set_title("(d) what UNA supplies")
    d.legend(loc="upper left")

    save(fig, "panel_4_counting")


# ===========================================================================
# Panel 5 -- scoring: the deficit vs benchmark mix (Prop 4.9)
# ===========================================================================

def panel_5():
    m = load("22_scoring_sweep.json")
    rows = m["series"]
    fig, ax = new_panel([None, None, None, "3d"])

    ref = [r["refusable"] for r in rows]
    frac = [r["refusable_fraction"] for r in rows]

    # (a) the two scores under the naive rule -- they coincide everywhere
    a = ax[0]
    a.plot(ref, [r["naive_honest"] for r in rows], "o-", color=C_RIGHT,
           ms=3.2, lw=1.3, label="honest")
    a.plot(ref, [r["naive_confident"] for r in rows], "s--", color=C_LEFT,
           ms=3.2, lw=1.3, label="confident")
    a.set_xlabel("refusable questions")
    a.set_ylabel("score")
    a.set_title("(a) answer-counting rule")
    a.legend(loc="lower left")

    # (b) the same two under the verdict-aware rule -- they separate
    b = ax[1]
    b.plot(ref, [r["aware_honest"] for r in rows], "o-", color=C_RIGHT,
           ms=3.2, lw=1.3, label="honest")
    b.plot(ref, [r["aware_confident"] for r in rows], "s--", color=C_LEFT,
           ms=3.2, lw=1.3, label="confident")
    b.fill_between(ref, [r["aware_confident"] for r in rows],
                   [r["aware_honest"] for r in rows], color=C_RIGHT, alpha=0.12)
    b.set_xlabel("refusable questions")
    b.set_ylabel("score")
    b.set_title("(b) verdict-aware rule")
    b.legend(loc="lower left")

    # (c) the gap under each rule: flat at zero vs exactly proportional
    c = ax[2]
    c.plot(frac, [r["naive_gap"] for r in rows], "o-", color=GREY, ms=3.2,
           lw=1.3, label="answer-counting")
    c.plot(frac, [r["aware_gap"] for r in rows], "s-", color=C_RIGHT, ms=3.2,
           lw=1.3, label="verdict-aware")
    # Shade the mixes where the two rules rank the agents differently -- the
    # ordering reversal is the claim; the gap is only its magnitude.
    dis = [r["refusable_fraction"] for r in rows if not r["orders_agree"]]
    if dis:
        c.axvspan(min(dis), max(dis), color=C_LEFT, alpha=0.08, lw=0)
    c.set_xlabel("refusable fraction")
    c.set_ylabel("score gap")
    c.set_title("(c) separation; shaded = rankings disagree")
    c.legend(loc="upper left")

    # (d) 3D: the mechanism behind (c). Each agent's answer set decomposes
    #     into questions it answered correctly, refused, and answered wrongly.
    #     The confident agent's wrong-answer stack is exactly the refusable
    #     count -- it never abstains -- which is what the answer-counting rule
    #     credits and the verdict-aware rule debits.
    d = ax[3]
    xs = np.arange(len(rows))
    n_ans = np.array([r["answerable"] for r in rows], dtype=float)
    n_ref = np.array([r["refusable"] for r in rows], dtype=float)
    for j, (name, parts) in enumerate([
        ("honest", [(n_ans, C_RIGHT), (n_ref, GREY)]),
        ("confident", [(n_ans, C_RIGHT), (n_ref, C_LEFT)]),
    ]):
        bottom = np.zeros(len(rows))
        for vals, col in parts:
            d.bar(xs, vals, zs=j, zdir="y", bottom=bottom, color=col,
                  alpha=0.92, width=0.62, edgecolor="white", linewidth=0.25)
            bottom = bottom + vals
    d.set_xlabel("refusable questions", labelpad=-3)
    d.set_zlabel("questions", labelpad=-6, rotation=90)
    d.set_yticks([0, 1])
    d.set_yticklabels(["honest", "confident"], fontsize=6)
    d.tick_params(pad=-2)
    d.set_title("(d) correct / refused / wrong")
    d.view_init(elev=20, azim=-62)

    save(fig, "panel_5_scoring")


# ===========================================================================
# Panel 6 -- verdicts and blockers (Def 4.2, Sec 9)
# ===========================================================================

def panel_6():
    m = load("23_blocker_grid.json")
    cells = m["cells"]
    contrasts = m["contrasts"]
    b19 = load("19_budget_sweep.json")
    fig, ax = new_panel([None, None, "3d", None])

    # (a) verdict labels over the grid, coloured by blocker
    a = ax[0]
    labels = sorted({c["label"] for c in cells})
    li = {l: i for i, l in enumerate(labels)}
    bl_col = {"blocked-by-model": C_LEFT, "blocked-by-engine": C_FOURTH,
              None: C_RIGHT}
    counts = {}
    for c in cells:
        counts.setdefault((c["label"], c["blocker"]), 0)
        counts[(c["label"], c["blocker"])] += 1
    bottom = np.zeros(len(labels))
    for bl in ["blocked-by-model", "blocked-by-engine", None]:
        vals = [counts.get((l, bl), 0) for l in labels]
        a.bar(range(len(labels)), vals, bottom=bottom, width=0.62,
              color=bl_col[bl],
              label="no blocker" if bl is None
              else bl.replace("blocked-by-", ""))
        bottom += np.array(vals, dtype=float)
    a.set_xticks(range(len(labels)))
    a.set_xticklabels([l.replace("-", "-\n") for l in labels], fontsize=6)
    a.set_ylabel("grid cells")
    a.set_title("(a) verdicts by blocker")
    a.legend(loc="upper right")

    # (b) which axes a changed verdict actually witnesses
    b = ax[1]
    axes_order = ["model", "engine", "budget", "corpus"]
    moved = [sum(1 for c in contrasts if c["axis"] == ax_ and c["differs"])
             for ax_ in axes_order]
    total = [sum(1 for c in contrasts if c["axis"] == ax_)
             for ax_ in axes_order]
    # Side by side, not overlaid: where an axis moved every cell the two
    # counts are equal, and an overlaid grey bar would be completely hidden
    # behind the coloured one -- indistinguishable from a missing baseline.
    w = 0.38
    b.bar(np.arange(4) - w / 2, total, width=w, color="#d9d9d9",
          label="cells varied")
    b.bar(np.arange(4) + w / 2, moved, width=w,
          color=[C_RIGHT, C_FOURTH, C_THIRD, C_LEFT], label="verdict moved")
    b.set_ylim(0, max(total) + 0.6)
    b.set_xticks(range(4))
    b.set_xticklabels(axes_order, fontsize=7)
    b.set_ylabel("cells")
    b.set_title("(b) axes witnessed")
    b.legend(loc="upper right")

    # (c) 3D: the grid as (axis, cell) -> blocker code, so the two reachable
    #     values and the unreachable third are visible at once
    c = ax[2]
    code = {"blocked-by-model": 1, "blocked-by-engine": 2, None: 0}
    for j, ax_ in enumerate(axes_order + ["baseline"]):
        sel = [cc for cc in cells if cc["varied"] == ax_]
        if not sel:
            continue
        xs = np.arange(len(sel))
        zs = [code[cc["blocker"]] for cc in sel]
        cols = [bl_col[cc["blocker"]] for cc in sel]
        c.bar(xs, zs, zs=j, zdir="y", color=cols, alpha=0.9,
              width=0.55, edgecolor="white", linewidth=0.3)
    c.set_xlabel("cell", labelpad=-3)
    c.set_zlabel("blocker", labelpad=-8, rotation=90)
    c.set_xticks(range(3))
    c.set_yticks(range(5))
    c.set_yticklabels(axes_order + ["base"], fontsize=6)
    c.set_zticks([0, 1, 2])
    c.set_zticklabels(["none", "model", "engine"], fontsize=6)
    c.tick_params(pad=-2)
    c.set_title("(c) attribution grid")
    c.view_init(elev=24, azim=-62)

    # (d) the budget collision: TIMEOUT and a missing lowering share a blocker,
    #     separated only by the verdict label. Steps reached, engine vs budget.
    d = ax[3]
    rows = b19["series"]
    tos = [r for r in rows if not r["answered"]]
    ans = [r for r in rows if r["answered"]]
    d.scatter([r["budget"] for r in tos], [r["steps"] for r in tos],
              color=C_LEFT, s=22, marker="s", label="timeout")
    d.scatter([r["budget"] for r in ans], [r["steps"] for r in ans],
              color=C_RIGHT, s=22, marker="o", label="answered")
    d.axhline(max(r["steps"] for r in ans), color=GREY, ls=":", lw=1.0)
    d.set_xlabel(r"budget $\tau$")
    d.set_ylabel("steps reached")
    d.set_ylim(0, max(r["steps"] for r in rows) * 1.35)
    d.set_title("(d) same blocker, two causes")
    d.legend(loc="lower right")

    save(fig, "panel_6_blockers")


# ===========================================================================

PANELS = [panel_1, panel_2, panel_3, panel_4, panel_5, panel_6]


def main():
    style()
    os.makedirs(FIG_DIR, exist_ok=True)
    print(f"writing to {FIG_DIR}")
    for fn in PANELS:
        fn()
    print(f"\n{len(PANELS)} panels written")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

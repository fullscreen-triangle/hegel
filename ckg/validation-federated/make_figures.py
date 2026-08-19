"""
Eight figure panels for the hegel-federated-query manuscript.
=============================================================

Each panel: white background, four charts in a row, at least one 3D, minimal
text, no conceptual diagrams / tables / text-only axes. Every value plotted is
read from results/ -- nothing is drawn by hand and no curve is fitted. Where a
panel needs a quantity the checks did not record as a curve, it comes from
sweeps.py, which varies a parameter and measures by calling the same functions
the checks call.

  panel_1  capability and refusal   -- thm:static, cor:refuse-before-contact
  panel_2  the six verdicts         -- thm:six, cor:onebit
  panel_3  blame and confinement    -- prop:blame, cor:rerun
  panel_4  retention factorises     -- thm:retention(a), prop:cardinality-*
  panel_5  the bounds and their gap -- thm:retention(b,c), rem:injectivity-*
  panel_6  allocation               -- thm:allocation, prop:necessary-not-*
  panel_7  ordering                 -- thm:reorder-cost
  panel_8  routes                   -- thm:route-extent

    python make_figures.py

Run run_validation.py and sweeps.py first; this reads their output and will say
so if a file is missing rather than drawing an empty axis.
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

# One palette across all eight panels, so a colour means the same thing
# wherever it appears: the healthy/answered case, the blocked/refused case,
# and the two auxiliary series each keep their hue from panel to panel.
C_RIGHT = "#1b4f72"    # answered / injective / admitted / cheaper plan
C_LEFT = "#922b21"     # refused / non-injective / rejected / dearer plan
C_THIRD = "#117864"    # third series where one is needed
C_FOURTH = "#7d6608"   # fourth series
GREY = "#888888"

#: Verdict colours. answer is the only one carrying a payload (prin:verdict),
#: so it alone gets the answered hue; the five blocked verdicts are graded.
VERDICT_COLOUR = {
    "answer": C_RIGHT,
    "empty": "#5499c7",
    "surface": C_FOURTH,
    "timeout": "#b9770e",
    "refused": C_LEFT,
    "starved": "#cd6155",
}
VERDICT_ORDER = ["answer", "empty", "surface", "timeout", "refused", "starved"]


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
            f"missing {path}\nrun `python run_validation.py` and "
            f"`python sweeps.py` first"
        )
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def sweeps(key):
    return load("sweeps.json")[key]


def grid_from(cells, xk, yk, zk):
    """Cells carrying (x, y, z) into meshgrid arrays for a surface."""
    xs = sorted({c[xk] for c in cells})
    ys = sorted({c[yk] for c in cells})
    lut = {(c[xk], c[yk]): c[zk] for c in cells}
    X, Y = np.meshgrid(xs, ys)
    Z = np.array([[lut.get((x, y), np.nan) for x in xs] for y in ys])
    return X, Y, Z


# ===========================================================================
# Panel 1 -- the static check: linear cost, and what refusing saves
# ===========================================================================

def panel_1():
    ch = sweeps("check")
    fig, ax = new_panel([None, None, "3d", None])

    # (a) check operations against plan length -- linear, under the bound
    a = ax[0]
    m = [r["m"] for r in ch["linearity"]]
    a.plot(m, [r["operations"] for r in ch["linearity"]], "o-",
           color=C_RIGHT, lw=1.4, ms=4, label="operations performed")
    a.plot(m, [r["bound"] for r in ch["linearity"]], "s--",
           color=GREY, lw=1.2, ms=3.5, label=r"bound $m|\mathrm{Feat}|$")
    a.set_xlabel("steps in plan $m$")
    a.set_ylabel("capability tests")
    a.set_yscale("log")
    a.set_title("(a) checking is linear in the plan")
    a.legend(loc="upper left")

    # (b) requests actually issued, measured at every plan length. Both
    # series are executed counts: the upper is what the well-capable plan
    # spends, the lower is what its ill-capable variant spends after
    # static refusal. cor:refuse-before-contact pins the lower at zero.
    b = ax[1]
    would = [r["would_issue"] for r in ch["linearity"]]
    after = [r["issued_after_refusal"] for r in ch["linearity"]]
    b.fill_between(m, after, would, color=C_LEFT, alpha=0.16)
    b.plot(m, would, "o-", color=C_LEFT, lw=1.4, ms=4,
           label="issued by the admitted plan")
    b.plot(m, after, "s-", color=C_RIGHT, lw=1.6, ms=4,
           label="issued after refusal")
    b.set_xlabel("steps in plan $m$")
    b.set_ylabel("requests issued")
    b.set_ylim(-0.35, max(would) + 0.6)
    b.set_title("(b) refusal happens before contact")
    b.legend(loc="center right")

    # (c) missing features per (source, predicate): the admissibility surface
    c = ax[2]
    mat = ch["matrix"]
    srcs = sorted({r["source"] for r in mat})
    preds = sorted({r["predicate"] for r in mat})
    lut = {(r["source"], r["predicate"]): r["n_missing"] for r in mat}
    Z = np.array([[lut[(s, p)] for s in srcs] for p in preds], dtype=float)
    X, Y = np.meshgrid(np.arange(len(srcs)), np.arange(len(preds)))
    # Integer counts over three sources are a discrete field, not a sheet;
    # a surface would interpolate a step function that has no intermediate
    # values. Bars show the 0/1/2 the checker actually computed.
    dz = Z.ravel()
    cols = [C_RIGHT if v == 0 else ("#c0392b" if v > 1 else C_LEFT)
            for v in dz]
    c.bar3d(X.ravel() - 0.3, Y.ravel() - 0.3, np.zeros_like(dz),
            0.6, 0.6, np.maximum(dz, 0.03), color=cols,
            edgecolor="#ffffff", linewidth=0.2, shade=True)
    c.set_xticks(np.arange(len(srcs)))
    c.set_xticklabels(srcs, fontsize=6)
    c.set_yticks(np.arange(0, len(preds), 3))
    c.set_yticklabels([preds[i][:9] for i in range(0, len(preds), 3)],
                      fontsize=6)
    c.set_zlabel("features missing", fontsize=7)
    c.set_zticks([0, 1, 2])
    c.set_title("(c) what each request would need")

    # (d) admitted vs rejected pairs per source
    d = ax[3]
    adm = [sum(1 for r in mat if r["source"] == s and r["admitted"])
           for s in srcs]
    rej = [sum(1 for r in mat if r["source"] == s and not r["admitted"])
           for s in srcs]
    xs = np.arange(len(srcs))
    d.bar(xs - 0.19, adm, 0.38, color=C_RIGHT, label="admitted")
    d.bar(xs + 0.19, rej, 0.38, color=C_LEFT, label="rejected")
    d.set_xticks(xs)
    d.set_xticklabels(srcs, fontsize=7)
    d.set_ylabel("predicates")
    d.set_title("(d) what each source can be asked")
    d.legend(loc="upper left")

    save(fig, "panel_1_capability")


# ===========================================================================
# Panel 2 -- the six verdicts, and what a boolean interface discards
# ===========================================================================

def panel_2():
    v = sweeps("verdicts")
    fig, ax = new_panel([None, "3d", None, None])

    cells = v["cells"]
    budgets, expects = v["budgets"], v["expects"]
    codes = {name: i for i, name in enumerate(VERDICT_ORDER)}

    # (a) the verdict regions over (budget, expectation)
    a = ax[0]
    lut = {(c["budget"], c["expect"]): c["verdict"] for c in cells}
    img = np.array([[codes[lut[(b, e)]] for b in budgets] for e in expects],
                   dtype=float)
    cmap = matplotlib.colors.ListedColormap(
        [VERDICT_COLOUR[n] for n in VERDICT_ORDER])
    a.imshow(img, origin="lower", aspect="auto", cmap=cmap, vmin=0,
             vmax=len(VERDICT_ORDER) - 1,
             extent=[-0.5, len(budgets) - 0.5, -0.5, len(expects) - 0.5])
    a.set_xticks(range(0, len(budgets), 2))
    a.set_xticklabels([budgets[i] for i in range(0, len(budgets), 2)])
    a.set_yticks(range(0, len(expects), 2))
    a.set_yticklabels(["%.1f" % expects[i]
                       for i in range(0, len(expects), 2)])
    a.set_xlabel("budget (requests)")
    a.set_ylabel(r"declared retention $\eta$")
    a.set_title("(a) budget and honesty select the verdict")
    a.grid(False)
    for n in ("answer", "refused", "starved"):
        a.plot([], [], "s", color=VERDICT_COLOUR[n], ms=6, label=n)
    a.legend(loc="lower right")

    # (b) requests spent as a surface: the cost of reaching each verdict
    b = ax[1]
    X, Y, Z = grid_from(cells, "budget", "expect", "requests")
    b.plot_surface(X, Y, Z, cmap="viridis", edgecolor="#33333322",
                   linewidth=0.2, rstride=1, cstride=1, antialiased=True)
    b.set_xticks([0, 5, 10, 15, 20])
    b.set_xlabel("budget", fontsize=7)
    b.set_ylabel(r"$\eta$", fontsize=7)
    b.set_zlabel("requests spent", fontsize=7)
    b.set_title("(b) spend before the verdict")

    # (c) how many configurations reach each verdict
    c = ax[2]
    counts = v["counts"]
    present = [n for n in VERDICT_ORDER if counts.get(n)]
    c.bar(range(len(present)), [counts[n] for n in present],
          color=[VERDICT_COLOUR[n] for n in present], width=0.62)
    c.set_xticks(range(len(present)))
    c.set_xticklabels(present, fontsize=7)
    c.set_ylabel("configurations")
    c.set_title("(c) verdicts realised by the sweep")

    # (d) the collapse: six values become two under a boolean interface
    d = ax[3]
    t, f = v["one_bit_true"], v["one_bit_false"]
    bottom = 0.0
    for n in present:
        if n == "answer":
            continue
        d.bar(1, counts[n], 0.5, bottom=bottom, color=VERDICT_COLOUR[n])
        bottom += counts[n]
    d.bar(0, counts.get("answer", 0), 0.5, color=VERDICT_COLOUR["answer"])
    d.bar(3, t, 0.5, color=C_RIGHT)
    d.bar(4, f, 0.5, color=GREY)
    d.set_xticks([0, 1, 3, 4])
    n_blocked = sum(1 for n in present if n != "answer")
    d.set_xticklabels(["answer", "blocked\n(%d kinds)" % n_blocked,
                       "true", "false"], fontsize=7)
    d.set_ylabel("configurations")
    d.set_title("(d) six verdicts, one bit")
    d.axvline(2, color="#cccccc", lw=0.8)

    save(fig, "panel_2_verdicts")


# ===========================================================================
# Panel 3 -- blame terminates, and a perturbation is confined
# ===========================================================================

def panel_3():
    bl = sweeps("blame")
    fig, ax = new_panel([None, None, None, "3d"])

    rows = bl["by_length"]
    m = [r["m"] for r in rows]

    # (a) blame-chain length against plan length, under the m-hop bound
    a = ax[0]
    a.plot(m, [r["max_hops"] for r in rows], "o-", color=C_RIGHT, lw=1.4,
           ms=4, label="longest chain")
    a.plot(m, [r["mean_hops"] for r in rows], "^-", color=C_THIRD, lw=1.2,
           ms=4, label="mean chain")
    a.plot(m, [r["bound"] for r in rows], "s--", color=GREY, lw=1.2, ms=3.5,
           label="bound $m$")
    a.set_xlabel("steps in plan $m$")
    a.set_ylabel("hops to the blamed step")
    a.set_title("(a) blame terminates within $m$")
    a.legend(loc="upper left")

    # (b) how much of the plan is starved
    b = ax[1]
    b.bar([r["m"] for r in rows], [r["n_starved"] for r in rows],
          color=C_LEFT, width=0.6, label="starved")
    b.plot(m, [r["n_steps"] for r in rows], "o-", color=GREY, lw=1.2, ms=3.5,
           label="steps executed")
    b.set_xlabel("steps in plan $m$")
    b.set_ylabel("steps")
    b.set_title("(b) starvation spreads downstream")
    b.legend(loc="upper left")

    # (c) a single perturbation and where it first bites
    c = ax[2]
    prop = bl["propagation"]
    pos = [r["perturbed_at"] for r in prop]
    c.plot(pos, [r["n_affected"] for r in prop], "o-", color=C_LEFT, lw=1.4,
           ms=4.5, label="steps affected")
    c.plot(pos, [r["first_affected"] for r in prop], "s-", color=C_RIGHT,
           lw=1.4, ms=4, label="first affected")
    c.plot(pos, [r["n_steps"] for r in prop], "--", color=GREY, lw=1.1,
           label="steps in plan")
    c.set_xticks(pos)
    c.set_xlabel("step perturbed")
    c.set_ylabel("steps")
    c.set_ylim(0, max(r["n_steps"] for r in prop) + 0.6)
    c.set_title("(c) perturbation is confined downstream")
    c.legend(loc="lower left")

    # (d) the reachability cone: which steps a perturbation at i can affect
    d = ax[3]
    n = max(r["n_steps"] for r in prop)
    Xs, Ys, Zs = [], [], []
    for r in prop:
        i = r["perturbed_at"]
        for j in range(1, n + 1):
            Xs.append(i)
            Ys.append(j)
            Zs.append(1.0 if j >= r["first_affected"] else 0.0)
    Xs, Ys, Zs = np.array(Xs), np.array(Ys), np.array(Zs)
    d.bar3d(Xs - 0.35, Ys - 0.35, np.zeros_like(Zs), 0.7, 0.7, Zs,
            color=[C_LEFT if z > 0 else "#e8e8e8" for z in Zs],
            edgecolor="#ffffff", linewidth=0.2, shade=True)
    d.set_xlabel("perturbed at", fontsize=7)
    d.set_ylabel("step", fontsize=7)
    d.set_zlabel("affected", fontsize=7)
    d.set_zticks([0, 1])
    d.set_title("(d) the downstream cone")

    save(fig, "panel_3_blame")


# ===========================================================================
# Panel 4 -- retention factorises; cardinality does not determine the factors
# ===========================================================================

def panel_4():
    card = sweeps("cardinality")
    v7 = load("v7.json")
    v8 = load("v8.json")
    fig, ax = new_panel([None, "3d", None, None])

    cells = card["cells"]

    # (a) the iso-cardinality hyperbolae: same |mu(S)|, any retention
    a = ax[0]
    for out, col in ((12, C_RIGHT), (24, C_THIRD), (48, C_LEFT)):
        fam = sorted([c for c in cells if c["output"] == out],
                     key=lambda c: c["r"])
        if fam:
            a.plot([c["r"] for c in fam], [c["a"] for c in fam], "o-",
                   color=col, lw=1.3, ms=4.5,
                   label=r"$|\mu(S)| = %d$" % out)
    a.set_xlabel(r"retention $r_\mu(S)$")
    a.set_ylabel(r"amplification $a_\mu(S)$")
    a.set_title("(a) equal output, unequal retention")
    a.legend(loc="upper right")

    # (b) the product surface: the only quantity output size reveals
    b = ax[1]
    X, Y, Z = grid_from(cells, "r", "a", "ratio")
    b.plot_surface(X, Y, Z, cmap="cividis", edgecolor="#33333322",
                   linewidth=0.2, rstride=1, cstride=1, antialiased=True)
    b.contour(X, Y, Z, levels=[0.5, 1.0, 2.0], colors="#ffffff",
              linewidths=0.8, offset=0)
    b.set_xlabel(r"$r_\mu$", fontsize=7)
    b.set_ylabel(r"$a_\mu$", fontsize=7)
    b.set_zlabel(r"$|\mu(S)|/|S|$", fontsize=7)
    b.set_title(r"(b) only the product $r\cdot a$ is observable")

    # (c) the measured pair from V8: two maps, one output size
    c = ax[2]
    pair = v8["maps"]
    names = [m["map"] for m in pair]
    rs = [m["retention"] for m in pair]
    aa = [m["amplification"] for m in pair]
    oo = [m["output_size"] for m in pair]
    xs = np.arange(len(names))
    c.bar(xs - 0.26, rs, 0.24, color=C_RIGHT, label=r"$r_\mu$")
    c.bar(xs, aa, 0.24, color=C_FOURTH, label=r"$a_\mu$")
    c.bar(xs + 0.26, [o / max(oo) for o in oo], 0.24, color=GREY,
          label=r"$|\mu(S)|$ (scaled)")
    c.set_xticks(xs)
    c.set_xticklabels(names, fontsize=7)
    c.set_title("(c) the measured counterexample")
    c.legend(loc="upper left")

    # (d) the factorisation along the fixture's chain
    d = ax[3]
    stages = v7["stages"]
    idx = np.arange(1, len(stages) + 1)
    cum, acc = [], 1.0
    for s in stages:
        acc *= s["retention"] * (s["amplification"] or 0.0)
        cum.append(acc)
    d.plot(idx, [s["retention"] for s in stages], "o-", color=C_RIGHT,
           lw=1.4, ms=5, label=r"$r_i$")
    d.plot(idx, [s["amplification"] for s in stages], "^-", color=C_FOURTH,
           lw=1.4, ms=5, label=r"$a_i$")
    d.plot(idx, cum, "s-", color=C_THIRD, lw=1.6, ms=5,
           label=r"$\prod r_j a_j$")
    d.axhline(v7["observed_ratio"], color=C_LEFT, ls=":", lw=1.4,
              label=r"observed $|S_k|/|S_0|$")
    d.set_xticks(idx)
    d.set_xlabel("stage $i$")
    d.set_ylabel("factor")
    d.set_title("(d) the product meets the measurement")
    d.legend(loc="upper right")

    save(fig, "panel_4_retention")


# ===========================================================================
# Panel 5 -- the two bounds, and the hypothesis they both need
# ===========================================================================

def panel_5():
    ret = sweeps("retention")
    bs = sweeps("bounds_surface")
    v16 = load("v16.json")
    fig, ax = new_panel([None, "3d", None, None])

    # (a) rho against min_i r_i: injective points obey the diagonal, others
    # do not. This is thm:retention(b) and its counterexamples in one frame.
    a = ax[0]
    inj = ret["scatter"]["injective"]
    non = ret["scatter"]["non_injective"]
    # The violating points are the claim, so they are drawn last and alone
    # in the alarm colour; non-injective chains that respect the bound are
    # greyed so they do not compete with them. Blue must stay on or below
    # the diagonal -- that is thm:retention(b).
    above = [q for q in non if q["rho"] > q["min_r"] + 1e-12]
    below = [q for q in non if q["rho"] <= q["min_r"] + 1e-12]
    a.fill_between([0, 1], [0, 1], [1, 1], color=C_LEFT, alpha=0.06,
                   linewidth=0)
    a.scatter([q["min_r"] for q in below], [q["rho"] for q in below],
              s=6, color=GREY, alpha=0.28, edgecolors="none",
              label="non-injective, bound holds")
    a.scatter([q["min_r"] for q in inj], [q["rho"] for q in inj], s=9,
              color=C_RIGHT, alpha=0.70, edgecolors="none",
              label="injective")
    a.scatter([q["min_r"] for q in above], [q["rho"] for q in above],
              s=12, color=C_LEFT, alpha=0.80, edgecolors="none",
              label="non-injective, bound fails")
    a.plot([0, 1], [0, 1], color="#333333", lw=1.1, ls="--")
    a.set_xlabel(r"$\min_i r_{\mu_i}$")
    a.set_ylabel(r"surviving fraction $\rho$")
    a.set_xlim(0, 1.02)
    a.set_ylim(0, 1.02)
    a.set_title("(a) the bound holds only under injectivity")
    a.legend(loc="upper left")

    # (b) the sandwich: measured rho between the two bounds over (r1, r2)
    b = ax[1]
    cells = bs["cells"]
    X, Y, Zr = grid_from(cells, "r1", "r2", "rho")
    _, _, Zu = grid_from(cells, "r1", "r2", "upper")
    _, _, Zl = grid_from(cells, "r1", "r2", "lower")
    b.plot_surface(X, Y, Zu, color=C_RIGHT, alpha=0.28, linewidth=0,
                   antialiased=True)
    b.plot_surface(X, Y, Zl, color=C_LEFT, alpha=0.28, linewidth=0,
                   antialiased=True)
    b.plot_wireframe(X, Y, Zr, color="#333333", linewidth=0.55,
                     rstride=1, cstride=1)
    b.set_xlabel(r"$r_1$", fontsize=7)
    b.set_ylabel(r"$r_2$", fontsize=7)
    b.set_zlabel(r"$\rho$", fontsize=7)
    b.set_title("(b) measured $\\rho$ inside the bounds")

    # (c) violation rate against how non-injective the chain is
    c = ax[2]
    bi = ret["by_image_size"]
    c.plot([r["max_image"] for r in bi], [100 * r["rate"] for r in bi], "o-",
           color=C_LEFT, lw=1.5, ms=5, label="violations of (b)")
    c.axhline(0, color=C_RIGHT, lw=1.4, ls="-",
              label="injective chains")
    c.set_xlabel("maximum images per element")
    c.set_ylabel("chains violating (b)  [%]")
    c.set_ylim(-2, max(100 * r["rate"] for r in bi) * 1.25)
    c.set_title("(c) collisions break the bound")
    c.legend(loc="lower right")

    # (d) both bounds, both populations, at n = 5000 each
    d = ax[3]
    r = v16["rates"]
    xs = np.arange(2)
    up = [100 * r["injective"]["upper_rate"],
          100 * r["non_injective"]["upper_rate"]]
    lo = [100 * r["injective"]["lower_rate"],
          100 * r["non_injective"]["lower_rate"]]
    d.bar(xs - 0.19, up, 0.38, color=C_LEFT, label="(b) upper bound")
    d.bar(xs + 0.19, lo, 0.38, color=C_FOURTH, label="(c) lower bound")
    d.set_xticks(xs)
    d.set_xticklabels(["injective", "non-injective"], fontsize=7.5)
    d.set_ylabel("chains violating the bound  [%]")
    d.set_title("(d) injectivity is the hypothesis")
    d.legend(loc="upper left")

    save(fig, "panel_5_bounds")


# ===========================================================================
# Panel 6 -- water-filling allocation
# ===========================================================================

def panel_6():
    al = sweeps("allocation")
    fig, ax = new_panel([None, None, "3d", None])

    curve = al["curve"]
    B = [c["budget"] for c in curve]

    # (a) effort per step as the budget grows -- steps enter in weight order
    a = ax[0]
    for name, col in zip("abcd", (GREY, C_THIRD, C_FOURTH, C_RIGHT)):
        a.plot(B, [c["effort"].get(name, 0.0) for c in curve], "-",
               color=col, lw=1.5, label="$w = %g$" % {"a": 1, "b": 2, "c": 4,
                                                      "d": 8}[name])
    a.set_xscale("log")
    a.set_xlabel("budget $B$")
    a.set_ylabel("effort allotted")
    a.set_title("(a) water filling, in weight order")
    a.legend(loc="upper left")

    # (b) the shadow price and the support, against the budget
    b = ax[1]
    b.plot(B, [c["shadow_price"] for c in curve], "-", color=C_LEFT, lw=1.6,
           label=r"shadow price $p^\ast$")
    b.set_xscale("log")
    b.set_yscale("log")
    b.set_xlabel("budget $B$")
    b.set_ylabel(r"$p^\ast$", color=C_LEFT)
    b.tick_params(axis="y", labelcolor=C_LEFT)
    b2 = b.twinx()
    b2.plot(B, [c["support"] for c in curve], "-", color=C_RIGHT, lw=1.4)
    b2.set_ylabel("steps on support", color=C_RIGHT)
    b2.tick_params(axis="y", labelcolor=C_RIGHT)
    b2.grid(False)
    b2.spines["right"].set_visible(True)
    b.set_title(r"(b) one price clears the budget")

    # (c) total yield over (budget, weight of the fourth step)
    c = ax[2]
    X, Y, Z = grid_from(al["surface"], "budget", "weight", "yield")
    c.plot_surface(np.log2(X), Y, Z, cmap="viridis", edgecolor="#33333322",
                   linewidth=0.2, rstride=1, cstride=1, antialiased=True)
    c.set_xlabel(r"$\log_2 B$", fontsize=7)
    c.set_ylabel("weight $w_d$", fontsize=7)
    c.set_zlabel("total yield", fontsize=7)
    c.set_title("(c) yield attained by the solver")

    # (d) all-or-nothing steps are charged before the optimisation
    d = ax[3]
    sw = al["stepwise"]
    nf = [r["n_fixed"] for r in sw]
    d.bar(nf, [r["charged_first"] for r in sw], 0.6, color=C_LEFT,
          label="charged first")
    d.bar(nf, [r["optimised_budget"] for r in sw], 0.6,
          bottom=[r["charged_first"] for r in sw], color=C_RIGHT,
          label="left to optimise")
    d.set_xlabel("all-or-nothing steps")
    d.set_ylabel("budget")
    d.set_title("(d) fixed costs come off the top")
    d2 = d.twinx()
    d2.plot(nf, [r["shadow_price"] for r in sw], "o-", color="#333333",
            lw=1.3, ms=4)
    d2.set_ylabel(r"$p^\ast$")
    d2.grid(False)
    d2.spines["right"].set_visible(True)
    d.legend(loc="upper left", bbox_to_anchor=(0.0, 0.88))

    save(fig, "panel_6_allocation")


# ===========================================================================
# Panel 7 -- step ordering: equal extent, unequal cost
# ===========================================================================

def panel_7():
    orde = sweeps("ordering")
    v10 = load("v10.json")
    fig, ax = new_panel([None, None, None, "3d"])

    meas = orde["measured"]
    a_plan = next(m for m in meas if m["plan"] == "order_a")
    b_plan = next(m for m in meas if m["plan"] == "order_b")

    # (a) requests spent by the two orderings, step by step
    a = ax[0]
    steps_a = [s["step"] for s in a_plan["per_step"]]
    xs = np.arange(len(steps_a))
    lut_b = {s["step"]: s["spent"] for s in b_plan["per_step"]}
    a.bar(xs - 0.19, [s["spent"] for s in a_plan["per_step"]], 0.38,
          color=C_RIGHT, label="filter first")
    a.bar(xs + 0.19, [lut_b.get(s, 0.0) for s in steps_a], 0.38,
          color=C_LEFT, label="filter last")
    a.set_xticks(xs)
    a.set_xticklabels(steps_a, fontsize=7)
    a.set_ylabel("requests")
    a.set_title("(a) where the cost differs")
    a.legend(loc="upper left")

    # (b) the totals: identical extent, different spend
    b = ax[1]
    b.bar([0, 1], [a_plan["requests"], b_plan["requests"]], 0.5,
          color=[C_RIGHT, C_LEFT], label="requests")
    b.set_xticks([0, 1])
    b.set_xticklabels(["filter first", "filter last"], fontsize=7.5)
    b.set_ylabel("requests")
    b2 = b.twinx()
    b2.plot([0, 1], [a_plan["coverage"], b_plan["coverage"]], "o--",
            color="#333333", lw=1.4, ms=6)
    b2.set_ylabel("identifiers emitted")
    b2.set_ylim(0, max(a_plan["coverage"], b_plan["coverage"]) * 1.6)
    b2.grid(False)
    b2.spines["right"].set_visible(True)
    b.set_title("(b) same extent, fewer requests")

    # (c) the saving as the filter grows more selective
    c = ax[2]
    # The measured surface at the allowance the shipped plans use. These
    # are executed request counts, not a cost model: `model` in the sweep
    # is the closed form and is deliberately not plotted.
    slab = sorted((r for r in orde["surface"] if r["within"] == 60),
                  key=lambda r: r["dropped"])
    dr = [r["dropped"] for r in slab]
    hi_ = [r["order_b_requests"] for r in slab]
    lo_ = [r["order_a_requests"] for r in slab]
    c.plot(dr, hi_, "o-", color=C_LEFT, lw=1.4, ms=4, label="filter last")
    c.plot(dr, lo_, "s-", color=C_RIGHT, lw=1.4, ms=4,
           label="filter first")
    c.fill_between(dr, hi_, lo_, color=C_THIRD, alpha=0.18)
    c.set_xticks(dr)
    c.set_xlabel("identifiers the filter removes")
    c.set_ylabel("requests")
    c.set_title("(c) the saving grows with selectivity")
    c.legend(loc="center left")

    # (d) both orderings executed over (filter size, expansion allowance).
    # Every point is a plan that was parsed, checked and run; the two sheets
    # are measured request counts, not a cost model.
    d = ax[3]
    surf = orde["surface"]
    X, Y, Za = grid_from(surf, "dropped", "within", "order_b_requests")
    _, _, Zb = grid_from(surf, "dropped", "within", "order_a_requests")
    d.plot_surface(X, Y, Za, color=C_LEFT, alpha=0.5, linewidth=0,
                   antialiased=True)
    d.plot_surface(X, Y, Zb, color=C_RIGHT, alpha=0.6, linewidth=0,
                   antialiased=True)
    d.set_xlabel("identifiers filtered", fontsize=7)
    d.set_ylabel("expansion allowance", fontsize=7)
    d.set_zlabel("requests", fontsize=7)
    d.set_title("(d) the gap, both plans executed")

    save(fig, "panel_7_ordering")


# ===========================================================================
# Panel 8 -- two routes: divergence, and its collapse under totality
# ===========================================================================

def panel_8():
    ro = sweeps("routes")
    v11 = load("v11.json")
    fig, ax = new_panel([None, "3d", None, None])

    curve = ro["curve"]
    cov = [r["coverage"] for r in curve]

    # (a) divergence shrinks to zero as both routes become total
    a = ax[0]
    a.plot(cov, [r["symmetric_difference"] for r in curve], "o-",
           color=C_LEFT, lw=1.5, ms=4, label="symmetric difference")
    a.plot(cov, [r["union"] for r in curve], "s-", color=C_RIGHT, lw=1.4,
           ms=4, label="union")
    a.set_xlabel("coverage of each route")
    a.set_ylabel("identifiers")
    a.set_title("(a) divergence vanishes at totality")
    a.legend(loc="center left")

    # (b) divergence over independent coverage for the two routes
    b = ax[1]
    X, Y, Z = grid_from(ro["surface"], "p1", "p2", "symmetric_difference")
    b.plot_surface(X, Y, Z, cmap="magma_r", edgecolor="#33333322",
                   linewidth=0.2, rstride=1, cstride=1, antialiased=True)
    b.set_xlabel("route 1 coverage", fontsize=7)
    b.set_ylabel("route 2 coverage", fontsize=7)
    b.set_zlabel("symmetric difference", fontsize=7)
    b.set_title("(b) the divergence surface")

    # (c) the measured routes from V11, before and after making them total
    c = ax[2]
    part = v11["partial_maps"]
    total = v11["total_maps"]
    keys = ["left_only", "right_only", "symmetric_difference"]
    xs = np.arange(len(keys))
    size = lambda d, k: len(d[k]) if isinstance(d[k], list) else d[k]
    pv = [size(part, k) for k in keys]
    tv = [size(total, k) for k in keys]
    c.bar(xs - 0.19, pv, 0.38, color=C_LEFT, label="partial maps")
    c.bar(xs + 0.19, tv, 0.38, color=C_RIGHT, label="total maps")
    # A measured zero must look different from an absent series.
    for x, v in zip(xs, tv):
        if v == 0:
            c.plot([x + 0.00, x + 0.38], [0, 0], color=C_RIGHT, lw=2.4,
                   solid_capstyle="butt")
    c.set_xticks(xs)
    c.set_xticklabels(["left only", "right only", "sym. diff."], fontsize=7)
    c.set_ylabel("identifiers")
    c.set_title("(c) the measured collapse")
    c.legend(loc="upper right")

    # (d) divergence as a fraction of the union -- a lower bound on the gap
    d = ax[3]
    frac = [(r["symmetric_difference"] / r["union"]) if r["union"] else 0.0
            for r in curve]
    d.plot(cov, frac, "o-", color=C_FOURTH, lw=1.5, ms=4)
    d.fill_between(cov, 0, frac, color=C_FOURTH, alpha=0.18)
    d.set_xlabel("coverage of each route")
    d.set_ylabel("divergence / union")
    d.set_ylim(0, 1.02)
    d.set_title("(d) a lower bound on the coverage gap")

    save(fig, "panel_8_routes")


# ===========================================================================

PANELS = [panel_1, panel_2, panel_3, panel_4,
          panel_5, panel_6, panel_7, panel_8]


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

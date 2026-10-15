"""Render the reach formulas as a transparent PNG (matplotlib mathtext, no LaTeX needed)."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import rcParams

def make(path, width_in=6.1, height_in=1.2, dpi=400, size=12.5):
    rcParams["mathtext.fontset"] = "cm"
    rcParams["mathtext.rm"] = "serif"
    fig = plt.figure(figsize=(width_in, height_in), dpi=dpi)
    lines = [
        r"$\mathrm{helix\ radius\ (Lorentz\ force):}\quad R = \dfrac{p_T}{e\,B}$",
        r"$\mathrm{with}\ p_T\ \mathrm{in\ GeV}/c\ \ \mathrm{and}\ \ c = 2.998 \times 10^{8}\ \mathrm{m/s}:\quad R\,[\mathrm{m}] = \dfrac{p_T\,[\mathrm{GeV}]}{0.2998\; B\,[\mathrm{T}]}$",
        r"$\mathrm{reach\ from\ the\ beam\ line:}\quad 2R \geq r \;\;\Rightarrow\;\; p_T > 0.15\, B\, r$",
        r"$B = 2\,\mathrm{T}:\quad p_T\,[\mathrm{MeV}] > 0.3\; r\,[\mathrm{mm}] \;\;\Rightarrow\;\; 39\ \mathrm{MeV\ (L3)},\ \ 95\ \mathrm{MeV\ (L4)}$",
    ]
    ys = [0.84, 0.52, 0.26, 0.07]
    for y, t in zip(ys, lines):
        fig.text(0.0, y, t, fontsize=size, va="center", ha="left", color="#262626")
    fig.savefig(path, dpi=dpi, transparent=True)
    plt.close(fig)

if __name__ == "__main__":
    import sys
    make(sys.argv[1] if len(sys.argv) > 1 else "formula.png")


def hits_per_layer_log(path, width_in=4.0, height_in=3.1, dpi=300):
    """The 4 Aug slide-5 histogram (SimTrackerHits per BX, whole layer) on a log axis with the values written."""
    import matplotlib.pyplot as plt
    vals = [24.3195, 7.9136, 4.9840, 0.3060, 0.5653]          # summary_numbers.md, all 19,673 BX
    labels = ["L0\n13.9 mm", "L1\n24.2 mm", "L2\n34.8 mm", "L3\n131 mm", "L4\n316 mm"]
    fig, ax = plt.subplots(figsize=(width_in, height_in), dpi=dpi)
    fig.subplots_adjust(left=0.17, right=0.97, top=0.76, bottom=0.2)
    ax.step(range(-1, 6), [vals[0]] + vals + [vals[-1]], where="post", color="#2a78d6", lw=1.6)
    ax.set_xlim(-0.5, 4.5); ax.set_yscale("log"); ax.set_ylim(0.1, 80)
    ax.set_xticks(range(5)); ax.set_xticklabels(labels, fontsize=7.5)
    ax.tick_params(axis="y", labelsize=7.5)
    for i, v in enumerate(vals):
        ax.text(i, v * 1.25, f"{v:.3g}", ha="center", va="bottom", fontsize=8)
    ax.set_ylabel("SimTrackerHits per BX, whole layer", fontsize=8)
    ax.set_xlabel("vertex-barrel layer (L0\u2013L2 inner barrel, L3\u2013L4 MAPS)", fontsize=8)
    ax.grid(axis="y", color="#e5e5e5", lw=0.6); ax.set_axisbelow(True)
    for sp in ("top", "right"): ax.spines[sp].set_visible(False)
    fig.text(0.02, 0.95, "Hits per bunch crossing per layer (the 4 Aug plot, log scale)", fontsize=8.5, weight="bold")
    fig.text(0.02, 0.89, "mean over the 19,673 simulated bunch crossings, no pT cut", fontsize=6.5, color="#595959")
    fig.text(0.02, 0.84, "IPC @ Z, LCC V106.2, central mdi_v2 sim; SimTrackerHits (1 keV simulation cut)", fontsize=6.5, color="#595959")
    fig.savefig(path, dpi=dpi)
    plt.close(fig)

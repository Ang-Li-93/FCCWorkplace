#!/usr/bin/env python3
"""
plot_rz_layout.py  -  ATLAS-ITk-style r-z views of the ALLEGRO/MAPS tracker.

Reads SimTrackerHit collections from a few edm4hep chunk files and shows them in the
(z, r) plane, with eta guide-lines. Two modes (default: both):

  layout     : scatter coloured by sub-detector, MAPS VTXOB (layers 3,4) highlighted.
  occupancy  : 2-D map coloured by occupancy = hits/event per (z,r) cell, log scale,
               so each layer/disk/module is shaded by how busy it is.

  python plot_rz_layout.py --indir <edm4hep dir> --compact <MAPS_o1_v01.xml> \
       --outdir results/qq_10k --nfiles 4 --mode both
"""
from __future__ import annotations
import argparse, glob, math, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "conversion"))
import convert_simhits_to_pixesl as C   # noqa: E402

# collection -> (label, colour, marker size, z-order)
STYLE = {
    "DCHCollection":          ("Drift chamber",       "#bdbdbd", 0.6, 1),
    "SiWrBCollection":        ("Si wrapper (barrel)", "#1f77b4", 2.0, 3),
    "SiWrDCollection":        ("Si wrapper (disks)",  "#1f77b4", 2.0, 3),
    "VertexEndcapCollection": ("Vertex endcap",       "#2ca02c", 2.0, 4),
}
VTXIB = ("Vertex barrel (inner, VTXIB)", "#ff7f0e", 2.0, 5)
VTXOB = ("MAPS VTXOB (layers 3,4, 20 µm)", "#d62728", 6.0, 6)
ALL_COLLS = list(STYLE) + ["VertexBarrelCollection"]


def eta_lines(ax, zmax, rmax):
    for eta in (1.0, 2.0, 3.0, 4.0):
        t = math.tan(2 * math.atan(math.exp(-eta)))
        for sgn in (+1, -1):
            ze = min(zmax, rmax / t)
            ax.plot([0, sgn * ze], [0, ze * t], color="0.5", lw=0.6, ls="--", zorder=0)
        ze = min(zmax, rmax / t)
        ax.text(ze * 0.96, ze * t + rmax * 0.012, f"η = {eta:.0f}",
                color="0.4", fontsize=8, ha="right")


def header(ax):
    ax.text(0.02, 0.93, "FCC-ee  ALLEGRO + MAPS", transform=ax.transAxes,
            fontweight="bold", fontstyle="italic")
    ax.text(0.02, 0.86, "Full simulation, Z→qq @ 91.2 GeV", transform=ax.transAxes,
            fontsize=8)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--indir", required=True)
    ap.add_argument("--compact", required=True, help="for VTXOB layer decode")
    ap.add_argument("--outdir", default="results/qq_10k")
    ap.add_argument("--nfiles", type=int, default=4)
    ap.add_argument("--mode", choices=["layout", "occupancy", "both"], default="both")
    ap.add_argument("--format", nargs="+", default=["pdf", "png"])
    args = ap.parse_args(argv)

    import numpy as np, matplotlib
    from matplotlib.colors import LogNorm
    matplotlib.use("Agg"); import matplotlib.pyplot as plt

    files = sorted(glob.glob(f"{args.indir}/events_*.edm4hep.root"))[: args.nfiles]
    if not files:
        sys.exit(f"no edm4hep files in {args.indir}")
    print(f"[rz] reading {len(files)} files ...", file=sys.stderr)

    pts = {}                       # categorical: key -> (style, [z], [r])
    allz, allr = [], []            # everything (for occupancy)
    n_events = 0
    decoder = None

    def add(key, style, z, r):
        d = pts.setdefault(key, (style, [], []))
        d[1].append(z); d[2].append(r); allz.append(z); allr.append(r)

    for fn in files:
        for _, avail, frame in C.iter_events_podio(fn):
            n_events += 1
            for coll, st in STYLE.items():
                if coll in (avail or []):
                    for h in frame.get(coll):
                        p = h.getPosition(); add(coll, st, p.z, math.hypot(p.x, p.y))
            if "VertexBarrelCollection" in (avail or []):
                if decoder is None:
                    decoder = C.build_decoder(args.compact, "VertexBarrelCollection")
                for h in frame.get("VertexBarrelCollection"):
                    p = h.getPosition(); r = math.hypot(p.x, p.y)
                    lay = decoder.get(h.getCellID(), "layer")
                    add("VTXOB" if lay in (3, 4) else "VTXIB",
                        VTXOB if lay in (3, 4) else VTXIB, p.z, r)

    if not allz:
        sys.exit("no hits found")
    allz = np.array(allz); allr = np.array(allr)
    rmax = allr.max() * 1.05
    zmax = np.abs(allz).max() * 1.05
    outdir = Path(args.outdir); outdir.mkdir(parents=True, exist_ok=True)
    print(f"[rz] {len(allz)} hits over {n_events} events", file=sys.stderr)

    def save(fig, stem):
        for ext in args.format:
            fig.savefig(outdir / f"{stem}.{ext}", bbox_inches="tight", dpi=150)
            print(f"[rz] wrote {outdir/stem}.{ext}")
        plt.close(fig)

    # ---- layout (categorical) ----
    if args.mode in ("layout", "both"):
        fig, ax = plt.subplots(figsize=(9, 4.5))
        for key, (st, zs, rs) in sorted(pts.items(), key=lambda kv: kv[1][0][3]):
            ax.scatter(zs, rs, s=st[2], c=st[1], label=st[0], edgecolors="none", rasterized=True)
        eta_lines(ax, zmax, rmax)
        ax.set_xlim(-zmax, zmax); ax.set_ylim(0, rmax)
        ax.set_xlabel("z [mm]"); ax.set_ylabel("r [mm]"); header(ax)
        ax.legend(loc="upper right", fontsize=7, markerscale=3, framealpha=0.9)
        save(fig, "rz_layout")

    # ---- occupancy: areal hit density (hits/cm^2/event) so thin Si layers stand out ----
    if args.mode in ("occupancy", "both"):
        # 1/(2*pi*r) folds in the azimuthal circumference -> per-hit areal weight on a
        # cylinder; *100 converts mm^-2 -> cm^-2; /n_events -> per event.
        w = 100.0 / (2 * math.pi * np.clip(allr, 1.0, None)) / n_events

        def occ_fig(zlim, rlim, grid, stem, title):
            fig, ax = plt.subplots(figsize=(9.6, 4.6))
            hb = ax.hexbin(allz, allr, C=w, reduce_C_function=np.sum, gridsize=grid,
                           extent=(-zlim, zlim, 0, rlim), cmap="inferno",
                           norm=LogNorm(), linewidths=0.0, mincnt=1e-30)
            cb = fig.colorbar(hb, ax=ax, pad=0.01)
            cb.set_label("areal hit density  [hits / cm$^2$ / event]   (∝ occupancy)")
            eta_lines(ax, zlim, rlim)
            ax.set_xlim(-zlim, zlim); ax.set_ylim(0, rlim)
            ax.set_xlabel("z [mm]"); ax.set_ylabel("r [mm]"); header(ax)
            ax.text(0.02, 0.79, title, transform=ax.transAxes, fontsize=8, color="0.3")
            save(fig, stem)

        occ_fig(zmax, rmax, (170, 80), "rz_occupancy", "full tracker")
        # zoom on the vertex region (incl. MAPS VTXOB at r=130/315 mm)
        occ_fig(900, 360, (150, 90), "rz_occupancy_vertex", "vertex region (MAPS VTXOB = bands at r≈130, 315 mm)")


if __name__ == "__main__":
    main()

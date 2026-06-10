#!/usr/bin/env python3
"""
plot_rz_layout.py  -  detector-demonstration r-z views of the ALLEGRO/MAPS tracker.

Reads SimTrackerHit collections from edm4hep chunk files, folds to |z| (the detector
is symmetric in z) and shows them in the (z, r) plane with eta guide-lines. Two modes
(default: both):

  layout     : scatter coloured by sub-detector, MAPS VTXOB (layers 3,4) highlighted.
  occupancy  : rectangular (z,r) map coloured by areal hit density
               (hits/cm^2/event, log) -- each layer/disk shaded by its occupancy.

The read pass is cached to <outdir>/rz_cache.npz so style tweaks are instant; use
--refresh to force a re-read.

  python plot_rz_layout.py --indir <edm4hep dir> --compact <MAPS_o1_v01.xml> \
       --outdir results/qq_10k --nfiles 200 --mode both
"""
from __future__ import annotations
import argparse, glob, math, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "conversion"))
import convert_simhits_to_pixesl as C   # noqa: E402

# ordered categories: (key, label, colour, marker size, z-order)
# ATLAS-ITk colour scheme: outer tracker BLUE, inner pixels RED, MAPS = boldest red.
CATS = [
    ("DCHCollection",          "Drift chamber",          "#9ecae1", 0.6, 1),
    ("SiWrBCollection",        "Si wrapper (barrel)",    "#08519c", 3.0, 3),
    ("SiWrDCollection",        "Si wrapper (disks)",     "#08519c", 3.0, 3),
    ("VertexEndcapCollection", "Vertex endcap",          "#fb6a4a", 3.0, 4),
    ("VTXIB",                  "Vertex barrel (VTXIB)",  "#fb6a4a", 3.0, 5),
    ("VTXOB",                  "MAPS VTXOB (L3,4 · 20 µm)", "#a50f15", 11.0, 6),
]
COLL_CODE = {"DCHCollection": 0, "SiWrBCollection": 1, "SiWrDCollection": 2,
             "VertexEndcapCollection": 3}   # VertexBarrel -> 4 (VTXIB) or 5 (VTXOB)


def set_style(plt):
    plt.rcParams.update({
        "figure.dpi": 150, "savefig.dpi": 200, "savefig.bbox": "tight",
        "font.size": 12, "axes.titlesize": 13, "axes.labelsize": 13,
        "xtick.labelsize": 10, "ytick.labelsize": 10, "legend.fontsize": 9,
        "xtick.direction": "in", "ytick.direction": "in",
        "xtick.top": True, "ytick.right": True, "xtick.minor.visible": True,
        "ytick.minor.visible": True, "axes.linewidth": 1.1,
    })


def eta_lines(ax, zmax, rmax):
    for eta in (1, 2, 3, 4):
        t = math.tan(2 * math.atan(math.exp(-eta)))
        ze = min(zmax, rmax / t); re = ze * t
        ax.plot([0, ze], [0, re], color="0.45", lw=0.7, ls=(0, (6, 4)), zorder=2)
        ax.text(ze, re, f" η = {eta} ", color="0.2", fontsize=8, ha="right", va="center",
                bbox=dict(boxstyle="round,pad=0.15", fc="white", ec="none", alpha=0.7),
                zorder=3)


def decorate(ax, region, n_events):
    ax.set_xlabel("z  [mm]"); ax.set_ylabel("r  [mm]")
    ax.set_title(f"FCC-ee   ALLEGRO + MAPS  ·  tracker $r$–$z$  ({region})",
                 loc="left", fontweight="bold")
    ax.text(0.015, 0.975, f"Z→qq, √s = 91.2 GeV\n{n_events:,} events",
            transform=ax.transAxes, ha="left", va="top", fontsize=9,
            bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="0.7", alpha=0.85),
            zorder=6)


def read_hits(files, compact, np):
    z, r, cat = [], [], []
    n_events = 0
    decoder = None
    for fn in files:
        for _, avail, frame in C.iter_events_podio(fn):
            n_events += 1
            for coll, code in COLL_CODE.items():
                if coll in (avail or []):
                    for h in frame.get(coll):
                        p = h.getPosition()
                        z.append(abs(p.z)); r.append(math.hypot(p.x, p.y)); cat.append(code)
            if "VertexBarrelCollection" in (avail or []):
                if decoder is None:
                    decoder = C.build_decoder(compact, "VertexBarrelCollection")
                for h in frame.get("VertexBarrelCollection"):
                    p = h.getPosition()
                    lay = decoder.get(h.getCellID(), "layer")
                    z.append(abs(p.z)); r.append(math.hypot(p.x, p.y))
                    cat.append(5 if lay in (3, 4) else 4)
    return np.array(z), np.array(r), np.array(cat, dtype=np.int8), n_events


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--indir", required=True)
    ap.add_argument("--compact", required=True, help="for VTXOB layer decode")
    ap.add_argument("--outdir", default="results/qq_10k")
    ap.add_argument("--nfiles", type=int, default=200)
    ap.add_argument("--mode", choices=["layout", "occupancy", "both"], default="both")
    ap.add_argument("--format", nargs="+", default=["pdf", "png"])
    ap.add_argument("--cmap", default="turbo", help="occupancy colormap (e.g. turbo, viridis, jet)")
    ap.add_argument("--refresh", action="store_true", help="force re-read (ignore cache)")
    args = ap.parse_args(argv)

    import numpy as np, matplotlib
    from matplotlib.colors import LogNorm
    matplotlib.use("Agg"); import matplotlib.pyplot as plt
    set_style(plt)

    outdir = Path(args.outdir); outdir.mkdir(parents=True, exist_ok=True)
    cache = outdir / "rz_cache.npz"

    if cache.exists() and not args.refresh:
        d = np.load(cache)
        z, r, cat, n_events = d["z"], d["r"], d["cat"], int(d["nev"])
        print(f"[rz] loaded cache {cache}  ({len(z)} hits, {n_events} events)", file=sys.stderr)
    else:
        files = sorted(glob.glob(f"{args.indir}/events_*.edm4hep.root"))[: args.nfiles]
        if not files:
            sys.exit(f"no edm4hep files in {args.indir}")
        print(f"[rz] reading {len(files)} files ...", file=sys.stderr)
        z, r, cat, n_events = read_hits(files, args.compact, np)
        np.savez(cache, z=z, r=r, cat=cat, nev=n_events)
        print(f"[rz] {len(z)} hits over {n_events} events -> cached {cache}", file=sys.stderr)

    rmax = r.max() * 1.04
    zmax = z.max() * 1.04

    def save(fig, stem):
        for ext in args.format:
            fig.savefig(outdir / f"{stem}.{ext}")
            print(f"[rz] wrote {outdir/stem}.{ext}")
        plt.close(fig)

    # ---- layout (categorical, true aspect) ----
    if args.mode in ("layout", "both"):
        fig, ax = plt.subplots(figsize=(8.4, 6.2))
        for code, (_, label, col, ms, zo) in enumerate(CATS):
            m = cat == code
            if m.any():
                ax.scatter(z[m], r[m], s=ms, c=col, label=label, edgecolors="none",
                           rasterized=True, zorder=zo)
        eta_lines(ax, zmax, rmax)
        ax.set_xlim(0, zmax); ax.set_ylim(0, rmax); ax.set_aspect("equal")
        decorate(ax, "full", n_events)
        ax.legend(loc="upper left", bbox_to_anchor=(1.02, 1.0), frameon=False,
                  markerscale=3, title="sub-detector",
                  title_fontproperties={"weight": "bold"})
        save(fig, "rz_layout")

    # ---- occupancy: areal hit density (hits/cm^2/event) on a rectangular (z,r) grid ----
    if args.mode in ("occupancy", "both"):
        rcm = np.clip(r, 1.0, None) / 10.0
        w = 1.0 / (2 * math.pi * rcm) / n_events       # cylinder areal weight, per event
        cmap = plt.get_cmap(args.cmap).copy(); cmap.set_bad("white")

        def occ_fig(zlim, rlim, nz, nr, stem, region, equal):
            zedges = np.linspace(0, zlim, nz + 1); redges = np.linspace(0, rlim, nr + 1)
            H, _, _ = np.histogram2d(z, r, bins=[zedges, redges], weights=w)
            H = H / ((zlim / nz) / 10.0)                # / z-width[cm] -> hits/cm^2/event
            H = np.ma.masked_where(H <= 0, H)
            fig, ax = plt.subplots(figsize=(8.8, 6.2) if equal else (9.2, 4.6))
            pcm = ax.pcolormesh(zedges, redges, H.T, norm=LogNorm(), cmap=cmap, shading="flat")
            cb = fig.colorbar(pcm, ax=ax, pad=0.015, fraction=0.046)
            cb.set_label("areal hit density   [hits / cm$^2$ / event]   (∝ occupancy)")
            eta_lines(ax, zlim, rlim); decorate(ax, region, n_events)
            ax.set_xlim(0, zlim); ax.set_ylim(0, rlim)
            if equal:
                ax.set_aspect("equal")
            else:
                for rr, lab in ((130, "VTXOB L3"), (315, "VTXOB L4")):
                    ax.annotate(lab, xy=(zlim, rr), xytext=(-4, 0),
                                textcoords="offset points", ha="right", va="center",
                                fontsize=8, color="white", fontweight="bold")
            save(fig, stem)

        occ_fig(zmax, rmax, 90, 80, "rz_occupancy", "full", equal=True)
        occ_fig(900, 360, 80, 90, "rz_occupancy_vertex", "vertex zoom", equal=False)


if __name__ == "__main__":
    main()

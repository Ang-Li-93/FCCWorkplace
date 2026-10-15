#!/usr/bin/env python3
"""
bib_event_display.py - event display of one bunch crossing (BX) of beam-induced
background from the BIB truth ntuple (ipc_LCC_V106p2_central_truth[_vertex].root).

Needs only numpy, uproot and matplotlib (pip install uproot matplotlib) - no
Key4hep, no geometry files. Each display has three views of the same BX:
  x-y            the vertex barrel end-on (layers L0-L4 drawn as circles)
  r-z            side view, r signed by the sign of y (layers drawn at +-r)
  x-y zoom       the inner barrel (L0-L2)
Vertex hits are marked by what made them:
  primary        a GuineaPig e+/e- itself
  secondary      a particle created in the simulation and stored (> 1 MeV)
  soft secondary an electron created below 1 MeV (not stored; by_secondary = 1)
Filled markers are hits on the vertex barrel, hollow ones hits on the vertex disks.
By default ALL hits of the simulated crossing are drawn, whatever their time (a
looping particle can keep hitting for a microsecond); --tmax 27 keeps one bunch
spacing. With --tracks the ideal helices (uniform 2 T, no energy loss, at most 3
turns, from the production vertex) of the stored charged particles that made a
vertex hit themselves are overlaid: a guide to the eye, not the true trajectory
of a particle that loses energy. With --full (needs the whole-tracker file) the
first two views show the whole tracker, with the drift-chamber and Si-wrapper
hits in grey, and the third one the vertex detector.

Output: <outdir>/bib_display_bx<BX>[_full].<format>  (a rerun overwrites it).

  python3 bib_event_display.py TRUTH.root --list              # BXs with most L3+L4 hits
  python3 bib_event_display.py TRUTH.root --bx 217846 --tracks
  python3 bib_event_display.py TRUTH.root --bx 217846 --tmax 27
  python3 bib_event_display.py TRUTH.root --busiest 5 --outdir displays
"""
import argparse, json, sys
from pathlib import Path

import numpy as np

# vertex-barrel layers: (mean hit radius_mm, half_length_mm)
LAYERS = [(13.91, 96.5), (24.16, 160.9), (34.84, 241.4), (131.33, 162.7), (316.04, 325.9)]
BFIELD_T = 2.0
KAPPA = 0.299792458 * BFIELD_T           # R[mm] = pT[MeV] / KAPPA
FULL_R, FULL_Z = 2150.0, 2450.0          # half-sizes of the whole-tracker views [mm]
BX_SPACING_NS = 27.0

INK, MUTED, GRID, SURFACE = "#0b0b0b", "#898781", "#e1e0d9", "#fcfcfb"
# class -> (label, colour, marker); colours validated all-pairs for CVD safety
CLASSES = [("primary e±", "#2a78d6", "o"),
           ("stored secondary (> 1 MeV)", "#eb6834", "s"),
           ("soft secondary (< 1 MeV e⁻)", "#1baf7a", "^")]
HIT_COLS = ["bx", "det", "layer", "x", "y", "z", "t", "pt", "by_secondary", "mc_gen_status", "barcode"]
PAR_COLS = ["barcode", "charge", "vx", "vy", "vz", "px", "py", "pz", "endz", "gen_status"]


def hit_class(h):
    return np.where(h["by_secondary"] == 1, 2, np.where(h["mc_gen_status"] == 1, 0, 1))


def helix(q, v, p, zend, zmax, turns=3.0, n=600):
    """Points of the ideal helix of one particle, stopped at its endpoint z,
    at |z| = zmax, or after `turns` turns."""
    pt = np.hypot(p[0], p[1])
    if pt <= 0 or q == 0:
        return None
    R = pt / KAPPA
    xc, yc = v[0] + q * R * p[1] / pt, v[1] - q * R * p[0] / pt
    psi0 = np.arctan2(v[1] - yc, v[0] - xc)
    tanl = p[2] / pt
    amax = 2 * np.pi * turns
    if tanl != 0:
        ztarget = np.clip(zend, -zmax, zmax) if np.sign(zend - v[2]) == np.sign(tanl) else np.sign(tanl) * zmax
        amax = min(amax, abs((ztarget - v[2]) / (R * tanl)))
    a = np.linspace(0, amax, n)
    psi = psi0 - q * a                    # q > 0 turns clockwise seen from +z
    return xc + R * np.cos(psi), yc + R * np.sin(psi), v[2] + R * a * tanl


def draw(bx, h, out, tracks, args, n_late):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.lines import Line2D
    plt.rcParams.update({"font.family": "sans-serif", "font.size": 10, "axes.edgecolor": MUTED,
                         "axes.labelcolor": INK, "xtick.color": MUTED, "ytick.color": MUTED,
                         "axes.linewidth": 0.8, "figure.facecolor": SURFACE, "axes.facecolor": SURFACE})
    rmax, full = args.rmax, args.full
    barrel, disks, other = h["det"] == 0, h["det"] == 1, h["det"] > 1
    cls = hit_class(h)
    sign_y = np.where(h["y"] >= 0, 1.0, -1.0)
    sr = np.hypot(h["x"], h["y"]) * sign_y
    zmax = args.zmax
    if full:
        views = [("x", FULL_R, FULL_R, "end-on (x–y), whole tracker"),
                 ("z", FULL_Z, FULL_R, "side view (r–z), whole tracker"),
                 ("x", rmax, rmax, "end-on, vertex detector")]
    else:
        views = [("x", rmax, rmax, "end-on (x–y)"), ("z", zmax, rmax, "side view (r–z)"),
                 ("x", 42.0, 42.0, "end-on, inner barrel zoom")]
    fig, axs = plt.subplots(1, 3, figsize=(16.5, 6.7), gridspec_kw={"width_ratios": [1, 1.25, 1]})
    for ax, (hk, hlim, vlim, title) in zip(axs, views):
        if hk == "x":
            th = np.linspace(0, 2 * np.pi, 361)
            for r, _ in LAYERS:
                ax.plot(r * np.cos(th), r * np.sin(th), color=GRID, lw=1.2, zorder=1)
            ax.set_aspect("equal")
        else:
            for r, hz in LAYERS:
                for s in (1, -1):
                    ax.plot([-hz, hz], [s * r, s * r], color=GRID, lw=1.6, zorder=1)
        for q, v, p, zend in tracks:
            pts = helix(q, v, p, zend, FULL_Z if full else zmax)
            if pts is None:
                continue
            x, y, z = pts
            if hk == "x":
                ax.plot(x, y, color=MUTED, lw=0.7, alpha=0.8, zorder=2)
            else:                             # break the line where r changes sign
                sy = np.where(y >= 0, 1.0, -1.0)
                r = np.hypot(x, y) * sy
                r[np.diff(sy, prepend=sy[0]) != 0] = np.nan
                ax.plot(z, r, color=MUTED, lw=0.7, alpha=0.8, zorder=2)
        hv, vv = (h["x"], h["y"]) if hk == "x" else (h["z"], sr)
        if other.any():
            ax.scatter(hv[other], vv[other], s=5, marker=".", color=MUTED, linewidth=0, zorder=2.5)
        small = hlim > 2 * rmax                 # whole-tracker panels: smaller markers
        for c, (label, colour, marker) in enumerate(CLASSES):
            s = barrel & (cls == c)
            ax.scatter(hv[s], vv[s], s=9 if small else 26, marker=marker, color=colour, edgecolor=SURFACE,
                       linewidth=0.3 if small else 0.6, zorder=4 + c)
            s = disks & (cls == c)
            ax.scatter(hv[s], vv[s], s=7 if small else 20, marker=marker, facecolor="none", edgecolor=colour,
                       linewidth=0.6 if small else 1.0, zorder=3.5)
        ax.set_xlim(-hlim, hlim)
        ax.set_ylim(-vlim, vlim)
        ax.set_xlabel(f"{hk} [mm]")
        ax.set_ylabel("y [mm]" if hk == "x" else "r × sign(y) [mm]")
        ax.set_title(title, loc="left", color=INK, fontsize=11)
        for L, (r, hz) in enumerate(LAYERS):   # name the layers that are resolved in this view
            if hk == "x" and 0.25 * hlim < r < hlim:
                ax.annotate(f"L{L}", (r * 0.7071, r * 0.7071), color=MUTED, fontsize=9,
                            xytext=(3, 3), textcoords="offset points")
            elif hk == "z" and not full and L >= 3:
                ax.annotate(f"L{L}", (min(hz, hlim * 0.93), r), color=MUTED, fontsize=9, xytext=(4, 4),
                            textcoords="offset points")
    per_layer = "  ".join(f"L{L} {int((barrel & (h['layer'] == L)).sum())}" for L in range(len(LAYERS)))
    when = (f"hits before {args.tmax:g} ns ({n_late} later vertex hits not drawn)" if args.tmax is not None
            else f"all hit times ({n_late} vertex hits later than {BX_SPACING_NS:g} ns)")
    fig.suptitle(f"IPC background, LCC V106.2 @ Z — bunch crossing {bx}, {when}\n"
                 f"vertex-barrel hits per layer: {per_layer}      vertex-disk hits: {int(disks.sum())}",
                 x=0.01, y=0.99, ha="left", va="top", color=INK, fontsize=11.5)
    handles = [Line2D([], [], ls="", marker=m, color=c, markeredgecolor=SURFACE, markersize=7,
                      label=f"{lab}: {int(((barrel | disks) & (cls == i)).sum())}") for i, (lab, c, m) in enumerate(CLASSES)]
    handles.append(Line2D([], [], ls="", marker="o", markerfacecolor="none", markeredgecolor=INK, markersize=6,
                          label="hollow = on the vertex disks"))
    if other.any():
        handles.append(Line2D([], [], ls="", marker=".", color=MUTED, markersize=6,
                              label=f"drift chamber + Si wrapper: {int(other.sum())}"))
    if tracks:
        handles.append(Line2D([], [], color=MUTED, lw=0.9,
                              label="ideal helix from the production vertex (no energy loss, ≤ 3 turns)"))
    axs[1].legend(handles=handles, loc="upper center", bbox_to_anchor=(0.5, -0.14), ncol=3, frameon=False,
                  title="vertex hits by what made them", fontsize=9, title_fontsize=9)
    fig.tight_layout(rect=(0, 0.03, 1, 0.92))
    fig.savefig(out, dpi=140)
    plt.close(fig)
    print(f"[display] {out}")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("ntuple", help="BIB truth ntuple (local file; give it before the options)")
    ap.add_argument("--bx", type=int, nargs="*", default=[], metavar="ID", help="bunch-crossing id(s) to draw")
    ap.add_argument("--busiest", type=int, default=0, metavar="N",
                    help="draw the N BXs with most hits on the MAPS layers L3+L4")
    ap.add_argument("--random", type=int, default=0, metavar="N", help="draw N random BXs (seed 1)")
    ap.add_argument("--list", action="store_true", help="print the 20 BXs with most L3+L4 hits and exit")
    ap.add_argument("--tracks", action="store_true",
                    help="overlay ideal helices of the stored charged particles that made a vertex hit themselves")
    ap.add_argument("--tmax", type=float, default=None, metavar="NS",
                    help="draw only hits earlier than this time [ns] (default: all; 27 = one bunch spacing)")
    ap.add_argument("--full", action="store_true", help="whole-tracker views (needs the whole-tracker file)")
    ap.add_argument("--rmax", type=float, default=345.0, metavar="MM", help="half-size of the vertex views [mm]")
    ap.add_argument("--zmax", type=float, default=352.0, metavar="MM",
                    help="half-length of the side view [mm]; 1000 shows all vertex disks")
    ap.add_argument("--outdir", default="displays", help="output directory (default: displays)")
    ap.add_argument("--format", default="png", help="image format (default: png)")
    args = ap.parse_args(argv)

    import uproot
    f = uproot.open(args.ntuple)
    if args.full and 4 not in json.loads(str(f["provenance"])).get("dets_in_file", [4]):
        sys.exit("--full needs the whole-tracker file (ipc_LCC_V106p2_central_truth.root): this one has vertex hits only")
    b = f["bx"].arrays(["bx", "n_hits_vb_L3", "n_hits_vb_L4", "n_hits_vtxb", "first_hit", "n_hits",
                        "first_particle", "n_particles"], library="np")
    maps = b["n_hits_vb_L3"] + b["n_hits_vb_L4"]
    order = np.argsort(-maps, kind="stable")
    if args.list:
        print("BXs with most hits on the MAPS layers L3+L4 (all hit times)")
        print("    bx   L3   L4  vertex-barrel hits")
        for i in order[:20]:
            print(f"{b['bx'][i]:6d} {b['n_hits_vb_L3'][i]:4d} {b['n_hits_vb_L4'][i]:4d} {b['n_hits_vtxb'][i]:6d}")
        return
    rows = [int(np.flatnonzero(b["bx"] == x)[0]) if (b["bx"] == x).any() else sys.exit(f"no BX {x} in the file")
            for x in args.bx]
    rows += list(order[:args.busiest])
    if args.random:
        rows += list(np.random.default_rng(1).choice(len(b["bx"]), args.random, replace=False))
    if not rows:
        sys.exit("nothing to draw: give --bx, --busiest or --random (or --list)")
    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    for i in rows:
        lo, n = int(b["first_hit"][i]), int(b["n_hits"][i])
        h = f["hits"].arrays(HIT_COLS, entry_start=lo, entry_stop=lo + n, library="np")
        vertex = h["det"] <= 1
        if args.tmax is not None:
            keep = h["t"] < args.tmax
            n_late = int((vertex & ~keep).sum())
            h = {k: v[keep] for k, v in h.items()}
        else:
            n_late = int((vertex & (h["t"] > BX_SPACING_NS)).sum())
        tracks = []
        if args.tracks:
            lo, n = int(b["first_particle"][i]), int(b["n_particles"][i])
            p = f["particles"].arrays(PAR_COLS, entry_start=lo, entry_stop=lo + n, library="np")
            linked = np.isin(p["barcode"], h["barcode"][(h["det"] <= 1) & (h["by_secondary"] == 0)])
            for j in np.flatnonzero(linked & (p["charge"] != 0)):
                tracks.append((float(p["charge"][j]), (p["vx"][j], p["vy"][j], p["vz"][j]),
                               (p["px"][j], p["py"][j], p["pz"][j]), float(p["endz"][j])))
        bx = int(b["bx"][i])
        tag = "_full" if args.full else ""
        draw(bx, h, outdir / f"bib_display_bx{bx}{tag}.{args.format}", tracks, args, n_late)


if __name__ == "__main__":
    main()

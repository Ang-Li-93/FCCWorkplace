#!/usr/bin/env python3
"""
bib_display_3d.py - 3D display of one bunch crossing (BX) of beam-induced background,
from the BIB truth ntuple (ipc_LCC_V106p2_central_truth[_vertex].root).

Companion of bib_event_display.py (the 2D views): same input, same hit classes and
colours, same selection options. Axes follow the HEP convention: the beam axis z is
horizontal, y points up, the end-on view is x-y, the projection is orthographic (the
HTML has buttons for the oblique / end-on / side / top views and for switching to
perspective). Per BX it writes

  <outdir>[/BX<BX>]/bib_display3d_bx<BX><view><colour>.html
                          interactive: rotate, zoom, hover a hit for its layer / time /
                          energy / particle, click a legend entry to hide it
  <outdir>[/BX<BX>]/bib_display3d_bx<BX><view><colour>.pdf
                          with --pdf (or --png): static matplotlib 3D views, oblique
                          and end-on; transparent background unless --opaque
  <outdir>[/BX<BX>]/bib_layermap_bx<BX><colour>.html / .pdf
                          with --layermap: the two MAPS layers unrolled (z vs phi) with
                          their stave and module grid; hover gives module, sensor and
                          the 20 um pixel address
  (<view> = "" for the default barrel view, "_vertex" or "_full" for the others;
   <colour> = "" for the default colouring by hit class, "_bylayer" or "_byparticle";
   with --bxdir each crossing goes into its own subdirectory BX<BX>)

The HTML embeds the hits as JSON and loads plotly.js from a CDN (so it needs a network
connection when opened, but no Python). Hits are coloured by what made them (primary
e+-, stored secondary, soft secondary), with --color layer by layer, or with --color
particle one colour per charged particle shared by its hits and its helix (the seven
particles with most direct hits; the rest grey, soft hits pale green); filled markers
for the barrel, hollow ones for the disks. The five barrel layers are drawn as wire
cylinders in one colour per layer (L0 grey, L1 gold, L2 brown, L3 magenta, L4 purple),
the two MAPS layers also as translucent surfaces. With --tracks the ideal
2 T helices (from the truth vertex, momentum and charge; no energy loss) of the stored
charged particles that made a vertex hit themselves are overlaid, a guide to the eye.
The vertex disks are drawn as wire annuli in teal, one shade per disk. --view picks the
box: "barrel" (default; |z| < 352 mm, r < 345 mm: the barrel and disk 1; hits on disks
2-3 are left out and counted in the title), "vertex" (|z| < 960 mm: the barrel and all
three disks) or "full" (whole tracker, needs the whole-tracker file: the drift-chamber
and Si-wrapper hits are added in grey).

  python3 bib_display_3d.py TRUTH.root --list
  python3 bib_display_3d.py TRUTH.root --bx 217846 --tracks --layermap --pdf
  python3 bib_display_3d.py TRUTH.root --busiest 3 --color layer --outdir displays3d
  python3 bib_display_3d.py TRUTH.root --bx 217846 --color particle --turns 20 --layermap --pdf
  python3 bib_display_3d.py TRUTH.root --bx 217846 282205 --tracks --pdf --bxdir --outdir displays3d
"""
import argparse
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from bib_event_display import (BX_SPACING_NS, CLASSES, FULL_R, FULL_Z, LAYERS,  # noqa: E402
                               helix, hit_class)

HIT_COLS = ["bx", "det", "layer", "x", "y", "z", "t", "pt", "edep", "mc_pdg", "by_secondary",
            "mc_gen_status", "barcode", "module", "sensor", "col20", "row20"]
PAR_COLS = ["barcode", "charge", "vx", "vy", "vz", "px", "py", "pz", "endz", "gen_status", "pdg"]
DET_NAMES = {0: "vertex barrel", 1: "vertex disk", 2: "Si wrapper barrel", 3: "Si wrapper disk",
             4: "drift chamber"}
# per-layer colours for the geometry (and for the hits with --color layer); chosen away from
# the hit-class colours of bib_event_display (blue / orange / green): L0 grey, L1 gold, L2 brown,
# L3 magenta, L4 purple
LAYER_COLORS = ["#9a9890", "#c9a227", "#8d5a3b", "#d63384", "#7c3aed"]
# MAPS layers: staves around phi, modules along z (BNL_MAPS geometry, baseline radii)
MAPS_LAYOUT = {3: (23, 8), 4: (51, 16)}
# vertex disks, one entry per side: (|z| of the sensor planes [mm], r_min, r_max [mm]); z = median of the
# truth hits (faces A/B of a disk are 15-33 mm apart), radii = VTXD_rmin/rmax of VertexComplete_o1_v01.xml
DISKS = [(312.2, 36.5, 275.0), (623.7, 70.0, 315.0), (935.0, 105.0, 315.0)]
DISK_COLORS = ["#4fc3b7", "#128f88", "#065f5a"]   # disks 1-3, light to dark teal (away from the layer / hit colours)
# --color particle: one colour per charged particle (the ones with most direct vertex hits), hits + helix alike;
# none of these is a hit-class colour (blue / orange / green) or a layer colour (gold / brown / magenta / purple)
PARTICLE_COLORS = ["#d62728", "#17a2b8", "#ff69b4", "#1f3a93", "#8a9a1b", "#7b1e1e", "#111111"]
PDG_NAMES = {11: "e⁻", -11: "e⁺", 22: "γ", 2212: "proton", 2112: "neutron", -211: "π⁻", 211: "π⁺", 13: "μ⁻", -13: "μ⁺"}
GREY_DARK, SOFT = "#8a8a8a", "#9ccfbd"
# views: half-sizes (r, z) of the drawn box [mm] and the output-file suffix
VIEWS = {"barrel": (345.0, 352.0, ""),             # vertex barrel + disk 1 (default)
         "vertex": (345.0, 960.0, "_vertex"),      # whole vertex detector: barrel + disks 1-3
         "full": (FULL_R, FULL_Z, "_full")}        # whole tracker (needs the whole-tracker file)
PLOTLY_CDN = "https://cdn.plot.ly/plotly-2.35.2.min.js"
GREY, INK, SURFACE, LINE = "#b9b7b0", "#0b0b0b", "#fcfcfb", "#e1e0d9"


# --------------------------------------------------------------------------- helpers
def layers_from_file(f):
    """(radius, half-length, z-offset) in mm of the five barrel layers, from the ntuple's
    provenance record; falls back to the constants of the 2D display."""
    try:
        cfg = json.loads(str(f["provenance"]))["read_pass_config"]["vtx_layers_r_halfz_zoff_mm"]
        return [(float(r), float(hz), float(zo)) for r, hz, zo in cfg]
    except Exception:  # noqa: BLE001
        return [(r, hz, 0.0) for r, hz in LAYERS]


def stave_phase(f):
    """phi [rad] of stave 0 on each MAPS layer, from all barrel hits of the file
    (stave = module // modules-per-stave increases with phi; the phase is the circular
    mean of phi - 2 pi stave / N). Used only to draw the stave grid of the unrolled map."""
    h = f["hits"].arrays(["det", "layer", "module", "x", "y"], library="np")
    out = {}
    for L, (nst, nmod) in MAPS_LAYOUT.items():
        s = (h["det"] == 0) & (h["layer"] == L)
        if not s.any():
            out[L] = 0.0
            continue
        d = np.arctan2(h["y"][s], h["x"][s]) - 2 * np.pi * (h["module"][s] // nmod) / nst
        out[L] = float(np.arctan2(np.sin(d).mean(), np.cos(d).mean()))
    return out


def cylinder_lines(r, halfz, zoff, n_circ=72, n_gen=12):
    """One None-separated polyline drawing a layer as three circles + generatrices,
    in detector coordinates (x, y, z)."""
    xs, ys, zs = [], [], []
    th = np.linspace(0, 2 * np.pi, n_circ + 1)
    for z in (zoff - halfz, zoff, zoff + halfz):
        xs += [round(float(v), 2) for v in r * np.cos(th)] + [None]
        ys += [round(float(v), 2) for v in r * np.sin(th)] + [None]
        zs += [round(z, 2)] * (n_circ + 1) + [None]
    for a in np.linspace(0, 2 * np.pi, n_gen, endpoint=False):
        xs += [round(r * np.cos(a), 2)] * 2 + [None]
        ys += [round(r * np.sin(a), 2)] * 2 + [None]
        zs += [round(zoff - halfz, 2), round(zoff + halfz, 2), None]
    return xs, ys, zs


def disk_lines(zc, rmin, rmax, n_circ=72, n_spoke=8):
    """One None-separated polyline drawing one disk on both sides as wire annuli
    (two circles + spokes), in detector coordinates (x, y, z)."""
    xs, ys, zs = [], [], []
    th = np.linspace(0, 2 * np.pi, n_circ + 1)
    for z in (-zc, zc):
        for r in (rmin, rmax):
            xs += [round(float(v), 2) for v in r * np.cos(th)] + [None]
            ys += [round(float(v), 2) for v in r * np.sin(th)] + [None]
            zs += [round(z, 2)] * (n_circ + 1) + [None]
        for a in np.linspace(0, 2 * np.pi, n_spoke, endpoint=False):
            xs += [round(rmin * np.cos(a), 2), round(rmax * np.cos(a), 2), None]
            ys += [round(rmin * np.sin(a), 2), round(rmax * np.sin(a), 2), None]
            zs += [round(z, 2), round(z, 2), None]
    return xs, ys, zs


def cylinder_surface(r, halfz, zoff, n=61):
    """2 x n grids (detector x, y, z) of a cylinder, for a translucent surface."""
    th = np.linspace(0, 2 * np.pi, n)
    x = np.vstack([r * np.cos(th)] * 2)
    y = np.vstack([r * np.sin(th)] * 2)
    z = np.vstack([np.full(n, zoff - halfz), np.full(n, zoff + halfz)])
    return x, y, z


def fl(a, nd=2):
    return [None if (v is None or np.isnan(v)) else round(float(v), nd) for v in a]


def clipped_helix(q, v, p, zend, lim, zmax, turns=3.0):
    """Ideal helix with the points outside the drawn box blanked (NaN), so a track
    that leaves the view is cut instead of being drawn across the page."""
    pts = helix(q, v, p, zend, zmax, turns=turns, n=max(400, int(150 * turns)))
    if pts is None:
        return None
    x, y, z = (np.array(a, dtype=float) for a in pts)
    out = (np.abs(x) > lim) | (np.abs(y) > lim) | (np.abs(z) > zmax)
    x[out] = y[out] = z[out] = np.nan
    return x, y, z


def hover_text(h, sel, det):
    r = np.hypot(h["x"], h["y"])
    return [f"L{int(l)} {DET_NAMES[det]}<br>r = {rr:.1f} mm, z = {zz:.1f} mm, phi = {np.degrees(np.arctan2(yy, xx)):.1f} deg<br>"
            f"t = {tt:.3f} ns, edep = {e:.1f} keV<br>pdg {int(p)}, pT {pt:.2f} MeV<br>"
            f"module {int(m)}, sensor {int(s)}, pixel (COL {int(c)}, ROW {int(rw)})"
            for l, rr, xx, yy, zz, tt, e, p, pt, m, s, c, rw in zip(
                h["layer"][sel], r[sel], h["x"][sel], h["y"][sel], h["z"][sel], h["t"][sel], h["edep"][sel],
                h["mc_pdg"][sel], h["pt"][sel], h["module"][sel], h["sensor"][sel], h["col20"][sel], h["row20"][sel])]


def particle_palette(h, tracks):
    """barcode -> (colour, label) for the charged particles with the most direct vertex hits
    (--color particle); `tracks` entries are (q, v, p, zend, barcode, pdg)."""
    direct = (h["det"] <= 1) & (h["by_secondary"] == 0)
    bcs, cnt = np.unique(h["barcode"][direct], return_counts=True)
    counts = dict(zip(bcs.tolist(), cnt.tolist()))
    order = sorted(tracks, key=lambda t: -counts.get(t[4], 0))
    pmap = {}
    for k, (q, v, p, zend, bc, pdg) in enumerate(order[:len(PARTICLE_COLORS)]):
        name = PDG_NAMES.get(int(pdg), f"pdg {int(pdg)}")
        pmap[bc] = (PARTICLE_COLORS[k],
                    f"{name}  pT {float(np.hypot(p[0], p[1])):.0f} MeV, pz {float(p[2]):.0f} MeV ({counts.get(bc, 0)} hits)")
    return pmap


def hit_groups(h, color_by, pmap=None):
    """(label, colour, marker, det, selection) per legend entry: by hit class, by layer or by particle."""
    cls = hit_class(h)
    groups = []
    if color_by == "layer":
        for L in range(5):
            groups.append((f"L{L}", LAYER_COLORS[L], "o", 0, (h["det"] == 0) & (h["layer"] == L)))
        groups.append(("vertex disks", "#555555", "o", 1, h["det"] == 1))
    elif color_by == "particle":
        direct = h["by_secondary"] == 0
        used = np.zeros(len(h["x"]), bool)
        for bc, (color, label) in (pmap or {}).items():
            m = direct & (h["barcode"] == bc)
            used |= m
            groups.append((label, color, "o", 0, m & (h["det"] == 0)))
            groups.append((label + " (disk)", color, "o", 1, m & (h["det"] == 1)))
        rest = direct & ~used
        groups.append(("other stored particles", GREY_DARK, "o", 0, rest & (h["det"] == 0)))
        groups.append(("other stored particles (disk)", GREY_DARK, "o", 1, rest & (h["det"] == 1)))
        groups.append(("soft secondary (< 1 MeV e⁻)", SOFT, "^", 0, ~direct & (h["det"] == 0)))
        groups.append(("soft secondary (< 1 MeV e⁻) (disk)", SOFT, "^", 1, ~direct & (h["det"] == 1)))
    else:
        for ci, (label, color, marker) in enumerate(CLASSES):
            groups.append((label, color, marker, 0, (cls == ci) & (h["det"] == 0)))
            groups.append((label + " (disk)", color, marker, 1, (cls == ci) & (h["det"] == 1)))
    return [g for g in groups if g[4].any()]


def title_for(bx, h, n_late, tmax, n_out=0):
    vb = h["det"] == 0
    n3, n4 = int((vb & (h["layer"] == 3)).sum()), int((vb & (h["layer"] == 4)).sum())
    t = (f"IPC LCC V106.2 central, BX {bx}: {int(vb.sum())} vertex-barrel hits "
         f"({n3} on L3, {n4} on L4), {int((h['det'] == 1).sum())} disk hits")
    if n_out:
        t += f" (+{n_out} vertex hits beyond this view)"
    if tmax is not None:
        t += f"; t < {tmax:g} ns ({n_late} later vertex hits dropped)"
    elif n_late:
        t += f"; all times ({n_late} vertex hits after {BX_SPACING_NS:g} ns)"
    return t


# --------------------------------------------------------------------------- 3D figure
# plot axes (x, y, z) = detector (z, x, y): beam axis horizontal, y up, end-on view = x-y
def build_figure(bx, h, tracks, layers, view, n_late, tmax, color_by, n_out=0, pmap=None, turns=3.0):
    traces = []
    lim, zmax, _ = VIEWS[view]
    full = view == "full"

    for i, (rl, hz, zo) in enumerate(layers):
        col = LAYER_COLORS[i]
        if i >= 3:
            sx, sy, sz = cylinder_surface(rl, hz, zo)
            traces.append(dict(type="surface", x=sz.tolist(), y=np.round(sx, 2).tolist(), z=np.round(sy, 2).tolist(),
                               surfacecolor=np.zeros_like(sx).tolist(), colorscale=[[0, col], [1, col]],
                               showscale=False, opacity=0.10, hoverinfo="skip", showlegend=False,
                               name=f"L{i} surface"))
        xs, ys, zs = cylinder_lines(rl, hz, zo)
        traces.append(dict(type="scatter3d", mode="lines", x=zs, y=xs, z=ys,
                           line=dict(color=col, width=2.5 if i >= 3 else 1), opacity=0.7,
                           name=f"L{i} layer  r = {rl:.0f} mm", hoverinfo="skip", legendgroup="geometry"))

    for k, (zc, rmin, rmax) in enumerate(DISKS):
        if zc >= zmax:
            continue
        dx, dy, dz = disk_lines(zc, rmin, rmax)
        traces.append(dict(type="scatter3d", mode="lines", x=dz, y=dx, z=dy, line=dict(color=DISK_COLORS[k], width=2.5),
                           opacity=0.85, hoverinfo="skip", legendgroup="geometry",
                           name=f"disk {k + 1}  |z| = {zc:.0f} mm"))

    if full:
        sel = h["det"] >= 2
        if sel.any():
            r = np.hypot(h["x"], h["y"])
            text = [f"{DET_NAMES.get(int(d), d)}<br>r = {rr:.0f} mm, z = {zz:.0f} mm<br>t = {tt:.2f} ns"
                    for d, rr, zz, tt in zip(h["det"][sel], r[sel], h["z"][sel], h["t"][sel])]
            traces.append(dict(type="scatter3d", mode="markers", x=fl(h["z"][sel], 1), y=fl(h["x"][sel], 1),
                               z=fl(h["y"][sel], 1), marker=dict(size=1.5, color=GREY),
                               name=f"outer tracker ({int(sel.sum())})", text=text, hoverinfo="text"))

    for label, color, _, det, sel in hit_groups(h, color_by, pmap):
        # MAPS-layer (L3/L4) hits are drawn larger whatever the colouring
        size = [6.0 if (l >= 3 and det == 0) else (4.0 if det == 0 else 5.5) for l in h["layer"][sel]]
        traces.append(dict(type="scatter3d", mode="markers",
                           x=fl(h["z"][sel]), y=fl(h["x"][sel]), z=fl(h["y"][sel]),
                           marker=dict(size=size, color=color, symbol="circle" if det == 0 else "circle-open",
                                       line=dict(width=1, color=color)), legendgroup=label,
                           name=f"{label} ({int(sel.sum())})", text=hover_text(h, sel, det), hoverinfo="text"))

    first = True
    for q, v, p, zend, bc, _ in tracks:
        pts = clipped_helix(q, v, p, zend, lim, zmax, turns)
        if pts is None:
            continue
        xyz = dict(x=fl(pts[2]), y=fl(pts[0]), z=fl(pts[1]))
        if pmap and bc in pmap:        # same colour and legend entry as the particle's hits
            col, label = pmap[bc]
            traces.append(dict(type="scatter3d", mode="lines", line=dict(color=col, width=2.5), opacity=0.8,
                               hoverinfo="skip", name=label + ", ideal helix", legendgroup=label, showlegend=False, **xyz))
        else:
            traces.append(dict(type="scatter3d", mode="lines", line=dict(color=INK, width=1.5), opacity=0.45,
                               hoverinfo="skip", name=f"ideal helices ({len(tracks)})", legendgroup="tracks",
                               showlegend=first, **xyz))
            first = False

    axis = dict(showbackground=False, gridcolor=LINE, zerolinecolor=LINE, color="#555")
    layout = dict(title=dict(text=title_for(bx, h, n_late, tmax, n_out), x=0.02, font=dict(size=14)),
                  scene=dict(xaxis=dict(title="z [mm]  (beam axis)", range=[-zmax, zmax], **axis),
                             yaxis=dict(title="x [mm]", range=[-lim, lim], **axis),
                             zaxis=dict(title="y [mm]", range=[-lim, lim], **axis),
                             aspectmode="manual",
                             aspectratio=dict(x=zmax / lim, y=1, z=1),
                             camera=dict(eye=dict(x=1.1, y=1.7, z=0.9), projection=dict(type="orthographic"))),
                  updatemenus=[dict(type="buttons", direction="left", x=0.99, y=0.98, xanchor="right", yanchor="top",
                                    showactive=False, bgcolor="rgba(252,252,251,0.8)", font=dict(size=11),
                                    buttons=[dict(label="oblique", method="relayout",
                                                  args=[{"scene.camera.eye": dict(x=1.1, y=1.7, z=0.9), "scene.camera.up": dict(x=0, y=0, z=1)}]),
                                             dict(label="end-on (x-y)", method="relayout",
                                                  args=[{"scene.camera.eye": dict(x=2.2, y=0, z=0), "scene.camera.up": dict(x=0, y=0, z=1)}]),
                                             dict(label="side (z-y)", method="relayout",
                                                  args=[{"scene.camera.eye": dict(x=0, y=-2.2, z=0), "scene.camera.up": dict(x=0, y=0, z=1)}]),
                                             dict(label="top (z-x)", method="relayout",
                                                  args=[{"scene.camera.eye": dict(x=0, y=0, z=2.2), "scene.camera.up": dict(x=0, y=1, z=0)}]),
                                             dict(label="orthographic", method="relayout",
                                                  args=[{"scene.camera.projection.type": "orthographic"}]),
                                             dict(label="perspective", method="relayout",
                                                  args=[{"scene.camera.projection.type": "perspective"}])])],
                  legend=dict(x=0.01, y=0.98, bgcolor="rgba(252,252,251,0.8)", font=dict(size=11)),
                  margin=dict(l=0, r=0, t=46, b=0), paper_bgcolor=SURFACE, font=dict(size=12, color=INK))
    return dict(data=traces, layout=layout)


# --------------------------------------------------------------------------- unrolled MAPS layers
def layer_grid(L, layers, phase):
    """z boundaries of the modules and phi boundaries [deg] of the staves of MAPS layer L."""
    nst, nmod = MAPS_LAYOUT[L]
    rl, hz, zo = layers[L]
    zb = zo - hz + np.arange(nmod + 1) * (2 * hz / nmod)
    pitch = 360.0 / nst
    pb = (np.degrees(phase[L]) + (np.arange(nst) + 0.5) * pitch + 180.0) % 360.0 - 180.0
    return zb, np.sort(pb), pitch


def build_layermap(bx, h, layers, phase, n_late, tmax, color_by, pmap=None):
    traces = []
    phi = np.degrees(np.arctan2(h["y"], h["x"]))
    panels = [(3, "x", "y"), (4, "x2", "y2")]
    for L, xa, ya in panels:
        zb, pb, pitch = layer_grid(L, layers, phase)
        rl, hz, zo = layers[L]
        gx, gy = [], []
        for z in zb:
            gx += [z, z, None]; gy += [-180, 180, None]
        for p in pb:
            gx += [zo - hz, zo + hz, None]; gy += [p, p, None]
        traces.append(dict(type="scatter", mode="lines", x=fl(gx, 1), y=fl(gy, 2), line=dict(color=LINE, width=1),
                           hoverinfo="skip", showlegend=False, xaxis=xa, yaxis=ya))
        for label, color, marker, det, sel in hit_groups(h, color_by, pmap):
            sel = sel & (h["det"] == 0) & (h["layer"] == L)
            if not sel.any():
                continue
            traces.append(dict(type="scatter", mode="markers", x=fl(h["z"][sel], 1), y=fl(phi[sel], 2),
                               marker=dict(size=8, color=color, line=dict(width=0.5, color=INK)),
                               name=label, legendgroup=label, showlegend=(L == 3), text=hover_text(h, sel, 0),
                               hoverinfo="text", xaxis=xa, yaxis=ya))

    def ax(title, dom, rng):
        return dict(title=title, domain=dom, range=rng, gridcolor=LINE, zerolinecolor=LINE, color="#555",
                    showline=True, linecolor=GREY)
    counts = {L: int(((h["det"] == 0) & (h["layer"] == L)).sum()) for L in (3, 4)}
    sub = {L: f"L{L}  r = {layers[L][0]:.0f} mm: {counts[L]} hits   ({MAPS_LAYOUT[L][0]} staves x "
              f"{MAPS_LAYOUT[L][1]} modules; one row = one stave, one column = one module)" for L in (3, 4)}
    zr = {L: [layers[L][2] - layers[L][1] - 5, layers[L][2] + layers[L][1] + 5] for L in (3, 4)}
    layout = dict(title=dict(text=title_for(bx, h, n_late, tmax), x=0.02, font=dict(size=14)),
                  xaxis=ax("z [mm]", [0, 1], zr[3]), yaxis=ax("phi [deg]", [0.57, 1.0], [-180, 180]),
                  xaxis2=ax("z [mm]", [0, 1], zr[4]), yaxis2=ax("phi [deg]", [0.0, 0.43], [-180, 180]),
                  annotations=[dict(text=sub[3], x=0, y=1.0, xref="paper", yref="paper", xanchor="left",
                                    yanchor="bottom", showarrow=False, font=dict(size=12)),
                               dict(text=sub[4], x=0, y=0.43, xref="paper", yref="paper", xanchor="left",
                                    yanchor="bottom", showarrow=False, font=dict(size=12))],
                  legend=dict(orientation="h", x=0, y=-0.08, font=dict(size=11)),
                  margin=dict(l=60, r=20, t=70, b=60), paper_bgcolor=SURFACE, plot_bgcolor=SURFACE,
                  font=dict(size=12, color=INK))
    return dict(data=traces, layout=layout)


# --------------------------------------------------------------------------- HTML
HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<script src="{cdn}"></script>
<style>
  body {{ margin: 0; font-family: -apple-system, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; background: {bg}; color: #333; }}
  #plot {{ width: 100vw; height: 90vh; }}
  .note {{ padding: 6px 14px 12px; font-size: 13px; color: #555; }}
</style>
</head>
<body>
<div id="plot"></div>
<div class="note">{note}</div>
<script type="application/json" id="fig">{fig}</script>
<script>
  const fig = JSON.parse(document.getElementById("fig").textContent);
  if (window.Plotly) {{
    Plotly.newPlot("plot", fig.data, fig.layout, {{responsive: true, displaylogo: false}});
  }} else {{
    document.getElementById("plot").textContent = "plotly.js could not be loaded from {cdn} (no network?)";
  }}
</script>
</body>
</html>
"""


def write_html(fig, title, out, cdn, note):
    js = json.dumps(fig, separators=(",", ":")).replace("</", "<\\/")
    out.write_text(HTML.format(title=title, cdn=cdn, bg=SURFACE, fig=js, note=note), encoding="utf-8")


# --------------------------------------------------------------------------- PNG
def _plt():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams.update({"font.family": "sans-serif", "font.size": 10, "figure.facecolor": SURFACE,
                         "axes.facecolor": SURFACE, "axes.edgecolor": GREY, "axes.labelcolor": INK,
                         "xtick.color": "#555", "ytick.color": "#555"})
    return plt


def legend_handles(color_by, tracks, layers=None, n_disks=0, pmap=None):
    """Layer colours (lines, when `layers` is given), the shown disks, then the hit colours."""
    from matplotlib.lines import Line2D
    handles = []
    if layers is not None and color_by != "layer":
        handles = [Line2D([], [], color=LAYER_COLORS[L], lw=1.2 if L >= 3 else 0.8, label=f"L{L}  r = {rl:.0f} mm")
                   for L, (rl, _, _) in enumerate(layers)]
    if color_by == "layer":
        handles += [Line2D([], [], marker="o", color=LAYER_COLORS[L], ls="", ms=6, label=f"L{L}  r = {rl:.0f} mm")
                    for L, (rl, _, _) in enumerate(layers)]
    elif color_by == "particle":
        handles += [Line2D([], [], marker="o", color=c, ls="-", lw=1.2, ms=6, label=l) for c, l in (pmap or {}).values()]
        handles.append(Line2D([], [], marker="o", color=GREY_DARK, ls="", ms=5, label="other stored particles"))
        handles.append(Line2D([], [], marker="^", color=SOFT, ls="", ms=6, label="soft secondary (< 1 MeV e⁻)"))
    else:
        handles += [Line2D([], [], marker=m, color=c, ls="", ms=6, label=l) for l, c, m in CLASSES]
    for k in range(n_disks):
        handles.append(Line2D([], [], color=DISK_COLORS[k], lw=1.2, label=f"disk {k + 1}  |z| = {DISKS[k][0]:.0f} mm"))
    handles.append(Line2D([], [], marker="o", mfc="none", mec="#555", ls="", ms=6, label="hollow: vertex disk"))
    if tracks:
        handles.append(Line2D([], [], color=INK, lw=0.8, alpha=0.6, label="ideal 2 T helix"))
    return handles


def draw_static(bx, h, tracks, layers, out, view, title, color_by, pmap=None, turns=3.0, transparent=True):
    """Static 3D views (oblique + end-on); the format follows the suffix of `out` (.pdf, .png, ...)."""
    plt = _plt()
    lim, zmax, _ = VIEWS[view]
    full = view == "full"
    fig = plt.figure(figsize=(15, 7), facecolor=SURFACE)
    for ip, (elev, azim, name) in enumerate([(20, -62, "oblique view"), (0, 0, "end-on (along the beam)")]):
        ax = fig.add_subplot(1, 2, ip + 1, projection="3d", facecolor=SURFACE)
        th = np.linspace(0, 2 * np.pi, 121)
        for i, (rl, hz, zo) in enumerate(layers):          # plot axes (x, y, z) = detector (z, x, y)
            col = LAYER_COLORS[i]
            lw = 1.0 if i >= 3 else 0.5
            if i >= 3:
                sx, sy, sz = cylinder_surface(rl, hz, zo)
                ax.plot_surface(sz, sx, sy, color=col, alpha=0.07, linewidth=0, shade=False)
            for z in (zo - hz, zo + hz):
                ax.plot(np.full_like(th, z), rl * np.cos(th), rl * np.sin(th), color=col, lw=lw)
            for a in np.linspace(0, 2 * np.pi, 8, endpoint=False):
                ax.plot([zo - hz, zo + hz], [rl * np.cos(a)] * 2, [rl * np.sin(a)] * 2, color=col, lw=lw * 0.7)
        for kd, (zc, rmin, rmax) in enumerate(DISKS):      # vertex disks as wire annuli, one colour per disk
            if zc >= zmax:
                continue
            for z in (-zc, zc):
                for rr in (rmin, rmax):
                    ax.plot(np.full_like(th, z), rr * np.cos(th), rr * np.sin(th), color=DISK_COLORS[kd], lw=1.0)
                for a in np.linspace(0, 2 * np.pi, 8, endpoint=False):
                    ax.plot([z, z], [rmin * np.cos(a), rmax * np.cos(a)], [rmin * np.sin(a), rmax * np.sin(a)],
                            color=DISK_COLORS[kd], lw=0.6)
        if full:
            sel = h["det"] >= 2
            ax.scatter(h["z"][sel], h["x"][sel], h["y"][sel], s=1, c=GREY, depthshade=False)
        for label, color, marker, det, sel in hit_groups(h, color_by, pmap):
            s = np.where((h["layer"][sel] >= 3) & (det == 0), 30, 22)
            ax.scatter(h["z"][sel], h["x"][sel], h["y"][sel], s=s, marker=marker,
                       facecolors=color if det == 0 else "none", edgecolors=color, linewidths=0.8, depthshade=False)
        for q, v, p, zend, bc, _ in tracks:
            pts = clipped_helix(q, v, p, zend, lim, zmax, turns)
            if pts is not None:
                if pmap and bc in pmap:
                    ax.plot(pts[2], pts[0], pts[1], color=pmap[bc][0], lw=1.0, alpha=0.8)
                else:
                    ax.plot(pts[2], pts[0], pts[1], color=INK, lw=0.6, alpha=0.45)
        ax.set_xlim(-zmax, zmax); ax.set_ylim(-lim, lim); ax.set_zlim(-lim, lim)
        # end-on: only the r x r face is seen, zoom so a long box (vertex view) does not shrink it
        ax.set_box_aspect((zmax / lim, 1, 1), zoom=1.0 if ip == 0 else min(2.5, max(1.0, 0.85 * zmax / lim)))
        ax.set_xlabel("z [mm]  (beam axis)"); ax.set_ylabel("x [mm]"); ax.set_zlabel("y [mm]")
        ax.view_init(elev=elev, azim=azim)
        ax.set_proj_type("ortho")           # HEP convention: no perspective, a cylinder end-on is one circle
        if elev == 0 and azim == 0:         # end-on: the beam axis points at the viewer, hide it
            ax.set_xticks([]); ax.set_xlabel("")
        ax.set_title(name, fontsize=10, color="#555")
        ax.xaxis.pane.fill = ax.yaxis.pane.fill = ax.zaxis.pane.fill = False
        ax.grid(False)
    handles = legend_handles(color_by, tracks, layers, n_disks=sum(1 for d in DISKS if d[0] < zmax), pmap=pmap)
    ncol = 4 if color_by == "particle" else 5
    fig.legend(handles=handles, loc="lower center", ncol=ncol, frameon=False, fontsize=9)
    fig.suptitle(title, fontsize=11, x=0.02, ha="left")
    fig.tight_layout(rect=(0, 0.04 + 0.028 * ((len(handles) + ncol - 1) // ncol), 1, 0.97))
    fig.savefig(out, dpi=140, transparent=transparent, **({} if transparent else {"facecolor": SURFACE}))
    plt.close(fig)


def draw_layermap_static(bx, h, layers, phase, out, title, color_by, pmap=None, transparent=True):
    """Unrolled z-phi maps of L3 and L4; the format follows the suffix of `out`."""
    plt = _plt()
    phi = np.degrees(np.arctan2(h["y"], h["x"]))
    fig, axs = plt.subplots(2, 1, figsize=(13, 8.5), facecolor=SURFACE, gridspec_kw={"height_ratios": [1, 1.6]})
    for ax, L in zip(axs, (3, 4)):
        zb, pb, pitch = layer_grid(L, layers, phase)
        rl, hz, zo = layers[L]
        for z in zb:
            ax.axvline(z, color=LINE, lw=0.7, zorder=0)
        for p in pb:
            ax.axhline(p, color=LINE, lw=0.5, zorder=0)
        n = 0
        for label, color, marker, det, sel in hit_groups(h, color_by, pmap):
            sel = sel & (h["det"] == 0) & (h["layer"] == L)
            if sel.any():
                ax.scatter(h["z"][sel], phi[sel], s=28, marker=marker, c=color, edgecolors=INK, linewidths=0.4, zorder=3)
                n += int(sel.sum())
        ax.set_xlim(zo - hz - 5, zo + hz + 5); ax.set_ylim(-180, 180)
        ax.set_yticks(range(-180, 181, 60))
        ax.set_ylabel("phi [deg]")
        ax.set_title(f"L{L}  r = {rl:.0f} mm: {n} hits   ({MAPS_LAYOUT[L][0]} staves x {MAPS_LAYOUT[L][1]} modules; "
                     f"one row = one stave, one column = one module)", fontsize=10, loc="left", color=LAYER_COLORS[L])
        for sp in ax.spines.values():
            sp.set_edgecolor(LAYER_COLORS[L]); sp.set_linewidth(1.2)
    axs[1].set_xlabel("z [mm]")
    handles = legend_handles(color_by, [], pmap=pmap)[:-1]
    ncol = min(len(handles), 4 if color_by == "particle" else 5)
    if handles:
        fig.legend(handles=handles, loc="lower center", ncol=ncol, frameon=False, fontsize=9)
    fig.suptitle(title, fontsize=11, x=0.02, ha="left")
    fig.tight_layout(rect=(0, 0.02 + 0.028 * ((len(handles) + ncol - 1) // ncol), 1, 0.97))
    fig.savefig(out, dpi=140, transparent=transparent, **({} if transparent else {"facecolor": SURFACE}))
    plt.close(fig)


# --------------------------------------------------------------------------- main
def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("ntuple", help="BIB truth ntuple (give it before the options)")
    ap.add_argument("--bx", type=int, nargs="*", default=[], metavar="ID", help="bunch-crossing id(s) to draw")
    ap.add_argument("--busiest", type=int, default=0, metavar="N", help="also draw the N BXs with most L3+L4 hits")
    ap.add_argument("--random", type=int, default=0, metavar="N", help="draw N random BXs (seed 1)")
    ap.add_argument("--list", action="store_true", help="print the 20 BXs with most L3+L4 hits and exit")
    ap.add_argument("--color", choices=["class", "layer", "particle"], default="class",
                    help="colour hits by what made them (class), by layer, or one colour per particle with its helix "
                         "(particle, implies --tracks; default: class)")
    ap.add_argument("--tracks", action="store_true", help="overlay ideal helices of the charged particles with a direct vertex hit")
    ap.add_argument("--turns", type=float, default=3.0, metavar="N", help="draw each ideal helix for at most N turns (default 3)")
    ap.add_argument("--tmax", type=float, default=None, metavar="NS", help="keep only hits before this time [ns]")
    ap.add_argument("--view", choices=list(VIEWS), default="barrel",
                    help="box to draw: barrel (vertex barrel + disk 1, default), vertex (barrel + all three disks), "
                         "full (whole tracker; needs the whole-tracker file)")
    ap.add_argument("--full", action="store_true", help="same as --view full")
    ap.add_argument("--layermap", action="store_true", help="also write the unrolled z-phi maps of L3 and L4")
    ap.add_argument("--pdf", action="store_true", help="also write static matplotlib figures as PDF")
    ap.add_argument("--png", action="store_true", help="also write static matplotlib figures as PNG")
    ap.add_argument("--opaque", action="store_true", help="white page behind the PDF/PNG figures (default: transparent background)")
    ap.add_argument("--outdir", default="displays3d", help="output directory (default: displays3d)")
    ap.add_argument("--bxdir", action="store_true", help="write each crossing's files into <outdir>/BX<id>/")
    ap.add_argument("--cdn", default=PLOTLY_CDN, help="plotly.js URL put into the HTML")
    args = ap.parse_args(argv)

    import uproot
    f = uproot.open(args.ntuple)
    dets = json.loads(str(f["provenance"])).get("dets_in_file", [4])
    if args.full:
        args.view = "full"
    if args.color == "particle":
        args.tracks = True
    if args.view == "full" and 4 not in dets:
        sys.exit("--view full needs the whole-tracker file (ipc_LCC_V106p2_central_truth.root)")
    lim, zmax, tag = VIEWS[args.view]
    ctag = "" if args.color == "class" else f"_by{args.color}"              # file-name suffix of the colouring
    tag += ctag
    layers = layers_from_file(f)
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
    rows = []
    for x in args.bx:
        hit = np.flatnonzero(b["bx"] == x)
        if not len(hit):
            sys.exit(f"no BX {x} in the file")
        rows.append(int(hit[0]))
    rows += [int(i) for i in order[:args.busiest]]
    if args.random:
        rows += [int(i) for i in np.random.default_rng(1).choice(len(b["bx"]), args.random, replace=False)]
    if not rows:
        sys.exit("nothing to draw: give --bx, --busiest or --random (or --list)")
    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    phase = stave_phase(f) if args.layermap else None
    note = ("Hits of one simulated bunch crossing (central ALLEGRO mdi_v2 sample, truth ntuple of 2026-10-05). "
            "Filled markers: vertex barrel; hollow: vertex disks; wire cylinders: barrel layers L0-L4, the MAPS "
            "layers L3/L4 also as translucent surfaces. Hover a hit for its layer, time, energy, particle, module, "
            "sensor and pixel; click a legend entry to hide it; drag to rotate, scroll to zoom, double-click to reset.")

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
        inbox = (np.abs(h["z"]) <= zmax) & (np.hypot(h["x"], h["y"]) <= lim)   # keep only what the box shows
        n_out = int(((h["det"] <= 1) & ~inbox).sum())                          # (barrel view: disks 2-3 lie outside)
        h = {k: v[inbox] for k, v in h.items()}
        tracks = []
        if args.tracks:
            lo, n = int(b["first_particle"][i]), int(b["n_particles"][i])
            p = f["particles"].arrays(PAR_COLS, entry_start=lo, entry_stop=lo + n, library="np")
            linked = np.isin(p["barcode"], h["barcode"][(h["det"] <= 1) & (h["by_secondary"] == 0)])
            for j in np.flatnonzero(linked & (p["charge"] != 0)):
                tracks.append((float(p["charge"][j]), (p["vx"][j], p["vy"][j], p["vz"][j]),
                               (p["px"][j], p["py"][j], p["pz"][j]), float(p["endz"][j]),
                               int(p["barcode"][j]), int(p["pdg"][j])))
        pmap = particle_palette(h, tracks) if args.color == "particle" else None
        bx = int(b["bx"][i])
        title = title_for(bx, h, n_late, args.tmax, n_out)
        fig = build_figure(bx, h, tracks, layers, args.view, n_late, args.tmax, args.color, n_out, pmap, args.turns)
        odir = outdir / f"BX{bx}" if args.bxdir else outdir
        odir.mkdir(parents=True, exist_ok=True)
        out = odir / f"bib_display3d_bx{bx}{tag}.html"
        write_html(fig, f"BIB 3D display, BX {bx}", out, args.cdn, note)
        print(f"wrote {out} ({out.stat().st_size // 1024} kB, {len(h['x'])} hits, {len(tracks)} helices)")
        for ext in [e for e, on in (("pdf", args.pdf), ("png", args.png)) if on]:
            outp = odir / f"bib_display3d_bx{bx}{tag}.{ext}"
            draw_static(bx, h, tracks, layers, outp, args.view, title, args.color, pmap, args.turns, transparent=not args.opaque)
            print(f"wrote {outp}")
        if args.layermap:
            lm = build_layermap(bx, h, layers, phase, n_late, args.tmax, args.color, pmap)
            outl = odir / f"bib_layermap_bx{bx}{ctag}.html"
            write_html(lm, f"BIB MAPS layers unrolled, BX {bx}", outl, args.cdn,
                       "The two MAPS layers unrolled: z along the beam, phi around it; one row of the grid is one "
                       "stave, one column one module (2 x 2 chips). Hover a hit for module, sensor and pixel address.")
            print(f"wrote {outl}")
            for ext in [e for e, on in (("pdf", args.pdf), ("png", args.png)) if on]:
                outlp = odir / f"bib_layermap_bx{bx}{ctag}.{ext}"
                draw_layermap_static(bx, h, layers, phase, outlp, title, args.color, pmap, transparent=not args.opaque)
                print(f"wrote {outlp}")


if __name__ == "__main__":
    main()

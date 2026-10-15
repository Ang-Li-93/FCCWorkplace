#!/usr/bin/env python3
"""Generate BNL_MAPS outer-vertex RADIUS variants for the LDRD WP1 occupancy scan.

The MAPS demonstrator = the 2 outer vertex barrel layers (VTXOB, layer ids 3,4).
This scan shifts BOTH layers in radius keeping the 185 mm layer gap, to map BIB
occupancy vs radius. The drift-chamber inner wall (DCH_inner_cyl_R_total=349.8mm)
caps the outer layer at r_out+15mm(clearance) < 349.8 -> r_out <~ 330mm, so the
scan is inward-dominant.

Mechanism (minimal fork, nothing shared is disturbed):
  * VertexComplete_o1_v01.xml was made radius-adaptive ONCE: VTXOB nStaves and
    nModules auto-scale linearly with VTXOB_r_{min,max}_layer, anchored so the
    baseline radii 130/315 reproduce EXACTLY 23/51 staves and 8/16 modules.
  * A variant is therefore produced solely by FORKING DectDimensions with
    different VTXOB_r_{min,max}_layer. Only VertexComplete + DectDimensions ever
    reference those two constants (verified), so this fully controls the radius
    and leaves every other subdetector identical.
  * Pitch is handled downstream at the CONVERTER (resegment mode re-bins COL/ROW
    from hit position at any pitch), so the geometry pitch (20um in the shared
    VertexComplete) is never touched. The variant study uses 25um to match
    Armin's detector-variant studies -> a 25um resegment geometry_config per
    variant.

For each variant this writes, into the k4geo BNL_MAPS compact dir:
    DectDimensions_<tag>.xml              (ALLEGRO DectDimensions, 2 radii changed)
    MAPS_o1_v01_BIB_v2_<tag>.xml          (BIB_v2 master, DectDimensions swapped)
and into fcc_maps_wrapper_pixesl/conversion/:
    geometry_config_<tag>.yaml            (resegment, 25um, variant layer radii)

Usage:  python3 make_radius_variants.py            # generate the default grid
        python3 make_radius_variants.py --dry-run  # print the grid + counts only
"""
import argparse
import math
import os
import re
import sys

# ---- paths -----------------------------------------------------------------
HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
K4GEO = os.path.join(REPO, "k4geo")
BNL_DIR = os.path.join(K4GEO, "FCCee", "BNL_MAPS", "compact", "MAPS_o1_v01")
ALLEGRO_DECT = os.path.join(
    K4GEO, "FCCee", "ALLEGRO", "compact", "ALLEGRO_o1_v03", "DectDimensions.xml")
MASTER_SRC = os.path.join(BNL_DIR, "MAPS_o1_v01_BIB_v2.xml")
CONV_DIR = os.path.join(REPO, "fcc_maps_wrapper_pixesl", "conversion")
GEOMCFG_SRC = os.path.join(CONV_DIR, "geometry_config.yaml")

# ---- baseline anchors (must match VertexComplete + DectDimensions) ---------
R_IN_BASE, R_OUT_BASE = 130.0, 315.0
NST1_BASE, NST2_BASE = 23, 51          # staves at baseline
NMOD1_BASE, NMOD2_BASE = 8, 16         # modules at baseline
MOD_Z = 40.6                            # VTXO_mod_z = 2*19.8 + (2*0.4+0.2) mm
MOD_Z_SPACING = 0.2
SENS_RPHI = 18.6                        # VTXO_sens_rphi_sensitive (per sensor)
SENS_Z = 19.8                           # VTXO_sens_z_sensitive
PITCH_UM = 25.0                         # variant readout pitch (Armin-matched)
DCH_INNER_R = 349.8                     # drift-chamber inner wall (hard ceiling)
RMAX_CLEARANCE = 15.0                   # VTXOB_rmax_clearance

# ---- the grid: (tag, r_in, r_out).  gap kept at baseline 185 mm ------------
GRID = [
    ("r145",  145.0, 330.0),   # max outward before DCH clash (330+15=345 < 349.8)
    ("r130",  130.0, 315.0),   # BASELINE (sim reused from v2 validation)
    ("r100",  100.0, 285.0),
    ("r070",   70.0, 255.0),
]


def rnd(x):
    """round-half-up, matching floor(x+0.5) used in the DD4hep formulas."""
    return int(math.floor(x + 0.5))


def counts(r_in, r_out):
    ns1 = rnd(NST1_BASE * r_in / R_IN_BASE)
    ns2 = rnd(NST2_BASE * r_out / R_OUT_BASE)
    nm1 = rnd(NMOD1_BASE * r_in / R_IN_BASE)
    nm2 = rnd(NMOD2_BASE * r_out / R_OUT_BASE)
    return ns1, ns2, nm1, nm2


def half_length(nmod):
    return (nmod * MOD_Z + (nmod - 1) * MOD_Z_SPACING) / 2.0


def write(path, text):
    with open(path, "w") as fh:
        fh.write(text)
    print("  wrote", os.path.relpath(path, REPO))


def gen_dectdimensions(tag, r_in, r_out):
    with open(ALLEGRO_DECT) as fh:
        txt = fh.read()
    # replace ONLY the two VTXOB radius constants (value="130*mm" etc.)
    txt, n1 = re.subn(r'(<constant name="VTXOB_r_min_layer"\s+value=")[^"]*(")',
                      r'\g<1>%g*mm\g<2>' % r_in, txt)
    txt, n2 = re.subn(r'(<constant name="VTXOB_r_max_layer"\s+value=")[^"]*(")',
                      r'\g<1>%g*mm\g<2>' % r_out, txt)
    if n1 != 1 or n2 != 1:
        sys.exit("ERROR: expected exactly one radius match each, got %d/%d" % (n1, n2))
    # NB: '--' is illegal inside an XML comment (Xerces FATAL), so avoid it.
    header = (
        "<!-- ==========================================================\n"
        "     BNL_MAPS LDRD radius variant '%s': outer-vertex layers at\n"
        "     r_in=%g mm, r_out=%g mm (baseline 130/315). Fork of\n"
        "     ALLEGRO_o1_v03/DectDimensions.xml with ONLY VTXOB_r_min_layer\n"
        "     and VTXOB_r_max_layer changed; everything else identical.\n"
        "     Generated by simulation/make_radius_variants.py (do not hand edit).\n"
        "     ========================================================== -->\n"
    ) % (tag, r_in, r_out)
    # The <?xml ...?> declaration MUST stay at line 1 col 1 (nothing, not even a
    # comment, may precede it) -> insert the header AFTER the first line.
    if txt.startswith("<?xml"):
        first, rest = txt.split("\n", 1)
        out = first + "\n" + header + rest
    else:
        out = header + txt
    write(os.path.join(BNL_DIR, "DectDimensions_%s.xml" % tag), out)


def gen_master(tag, r_in, r_out):
    with open(MASTER_SRC) as fh:
        txt = fh.read()
    inc_old = '<include ref="../../../ALLEGRO/compact/ALLEGRO_o1_v03/DectDimensions.xml" />'
    inc_new = '<include ref="./DectDimensions_%s.xml" />' % tag
    if txt.count(inc_old) != 1:
        sys.exit("ERROR: DectDimensions include not found exactly once in master")
    txt = txt.replace(inc_old, inc_new)
    # tag the <info> title/version so a loaded geometry is self-identifying
    txt = txt.replace('title="BNL_MAPS o1_v01 BIB variant, mdi_v2 (LCC-era MDI)"',
                      'title="BNL_MAPS o1_v01 BIB variant %s (r_in=%g,r_out=%g), mdi_v2"'
                      % (tag, r_in, r_out))
    write(os.path.join(BNL_DIR, "MAPS_o1_v01_BIB_v2_%s.xml" % tag), txt)


def gen_geomcfg(tag, r_in, r_out):
    ns1, ns2, nm1, nm2 = counts(r_in, r_out)
    hl1, hl2 = half_length(nm1), half_length(nm2)
    with open(GEOMCFG_SRC) as fh:
        txt = fh.read()
    # mode decode_cellid -> resegment (re-bin COL/ROW from position at 25um)
    txt = re.sub(r'mode:\s*decode_cellid[^\n]*',
                 'mode: resegment            # variant scan: re-bin COL/ROW from '
                 'position at %g um' % PITCH_UM, txt)
    # pitch 20 -> 25 um
    txt = re.sub(r'pixel_pitch_x_um:\s*\d+[^\n]*',
                 'pixel_pitch_x_um: %g         # variant readout pitch (Armin-matched)'
                 % PITCH_UM, txt)
    txt = re.sub(r'pixel_pitch_y_um:\s*\d+[^\n]*',
                 'pixel_pitch_y_um: %g' % PITCH_UM, txt)
    # per-variant layer radii/half-lengths (for the converter's area/rate metadata)
    layers_block = (
        "layers:\n"
        "  - {id: 3, radius_mm: %.1f, half_length_mm: %.1f}\n"
        "  - {id: 4, radius_mm: %.1f, half_length_mm: %.1f}\n" % (r_in, hl1, r_out, hl2))
    txt = re.sub(r'layers:\n(?:  - \{[^\n]*\}\n)+', layers_block, txt)
    write(os.path.join(CONV_DIR, "geometry_config_%s.yaml" % tag), txt)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    col_off = rnd(SENS_RPHI * 1000.0 / PITCH_UM / 2.0)   # half per-sensor px count
    row_off = rnd(SENS_Z * 1000.0 / PITCH_UM / 2.0)
    print("pitch=%g um -> converter offsets: --col-offset %d --row-offset %d\n"
          % (PITCH_UM, col_off, row_off))
    print("%-6s %6s %6s | %-13s %-13s | %-8s %-8s | env(offsets)" %
          ("tag", "r_in", "r_out", "staves(L3/L4)", "modules(L3/L4)", "hl1", "hl2"))
    for tag, r_in, r_out in GRID:
        ns1, ns2, nm1, nm2 = counts(r_in, r_out)
        env = r_out + RMAX_CLEARANCE
        clash = "  *** DCH CLASH (env=%.1f >= %.1f)" % (env, DCH_INNER_R) if env >= DCH_INNER_R else ""
        print("%-6s %6.1f %6.1f | %2d / %-8d %2d / %-8d | %6.1f %6.1f%s" %
              (tag, r_in, r_out, ns1, ns2, nm1, nm2, half_length(nm1), half_length(nm2), clash))
        if clash:
            sys.exit("ERROR: %s clashes with the drift chamber; fix the grid." % tag)
    if args.dry_run:
        print("\n[dry-run] no files written.")
        return
    print()
    manifest = {"pitch_um": PITCH_UM, "col_offset": col_off, "row_offset": row_off,
                "sensor_rphi_sensitive_mm": SENS_RPHI, "sensor_z_sensitive_mm": SENS_Z,
                "layer_gap_mm": R_OUT_BASE - R_IN_BASE, "variants": []}
    for tag, r_in, r_out in GRID:
        print("[%s] r_in=%g r_out=%g" % (tag, r_in, r_out))
        gen_dectdimensions(tag, r_in, r_out)
        gen_master(tag, r_in, r_out)
        gen_geomcfg(tag, r_in, r_out)
        ns1, ns2, nm1, nm2 = counts(r_in, r_out)
        # per layer: sensitive area (cm^2) and pixel count at PITCH_UM.
        # a module = 2x2 sensors; sensor sensitive = SENS_RPHI x SENS_Z.
        def layer(nstaves, nmod, radius):
            area_mm2 = nstaves * nmod * (2 * SENS_RPHI) * (2 * SENS_Z)
            npix = nstaves * nmod * (2 * round(SENS_RPHI * 1000.0 / PITCH_UM)) \
                                  * (2 * round(SENS_Z * 1000.0 / PITCH_UM))
            return {"radius_mm": radius, "nstaves": nstaves, "nmodules": nmod,
                    "sens_area_cm2": area_mm2 / 100.0, "npix": npix}
        manifest["variants"].append({
            "tag": tag, "r_in_mm": r_in, "r_out_mm": r_out, "is_baseline": tag == "r130",
            "master": "MAPS_o1_v01_BIB_v2_%s.xml" % tag,
            "geomcfg": "geometry_config_%s.yaml" % tag,
            "L3": layer(ns1, nm1, r_in), "L4": layer(ns2, nm2, r_out)})
    import json
    mpath = os.path.join(HERE, "radius_variants_manifest.json")
    write(mpath, json.dumps(manifest, indent=2) + "\n")
    print("\nDone. Smoke-test each new master with 1 BX before production.")


if __name__ == "__main__":
    main()

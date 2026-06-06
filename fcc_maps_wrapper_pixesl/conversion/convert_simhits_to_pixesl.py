#!/usr/bin/env python3
"""
convert_simhits_to_pixesl.py
============================
Convert EDM4hep ``SimTrackerHit`` collections into the PixESL input table:

    BX,COL,ROW,h_time,qin

Default target: the ALLEGRO/BNL_MAPS OUTER vertex barrel layers (VTXOB, layer
ids 3 & 4) in ``VertexBarrelCollection``, read out at 20 um. Because that
readout has a real ``CartesianGridXY`` segmentation, COL/ROW come from DECODING
the SimTrackerHit cellID (layer, x, y) -- mode "decode_cellid" (needs --compact
to build the bitfield decoder). A "barrel_position" fallback maps from the hit
position for collections without a pixel segmentation (e.g. the old SiWr).

Outputs:
  <output>.csv                  strict PixESL table  BX,COL,ROW,h_time,qin
  <output>_extended.csv         + layer,module,sensor,r_mm,z_mm  (for analysis/plots)
  <output>.metadata.json        provenance + counts + offsets

Run ``python convert_simhits_to_pixesl.py --help`` for options.
"""
from __future__ import annotations

import argparse
import json
import math
import subprocess
import sys
from pathlib import Path


# --------------------------------------------------------------------------- #
def die(msg: str, code: int = 1):
    print(f"ERROR: {msg}", file=sys.stderr)
    sys.exit(code)


def load_yaml(path: Path):
    try:
        import yaml
    except Exception as exc:  # noqa: BLE001
        die(f"pyyaml needed ({exc}). Source the Key4hep stack.")
    if not path.is_file():
        die(f"config file not found: {path}")
    return yaml.safe_load(path.read_text())


def git_hash() -> str:
    try:
        out = subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=Path(__file__).resolve().parent, stderr=subprocess.DEVNULL)
        return out.decode().strip()
    except Exception:  # noqa: BLE001
        return "unknown"


_EDEP_TO_EV = {"GeV": 1.0e9, "MeV": 1.0e6, "keV": 1.0e3, "eV": 1.0}
_TIME_TO_PS = {"ns": 1.0e3, "ps": 1.0, "s": 1.0e12, "us": 1.0e6}


def edep_to_qin(edep, unit, eh_eV, default_q, use_edep):
    if use_edep and edep and edep > 0.0:
        return edep * _EDEP_TO_EV[unit] / eh_eV
    return float(default_q)


# --------------------------------------------------------------------------- #
# cellID decoder (dd4hep) -- for the segmented VertexBarrelCollection readout
# --------------------------------------------------------------------------- #
def build_decoder(compact: str, readout: str):
    try:
        import dd4hep
    except Exception as exc:  # noqa: BLE001
        die(f"dd4hep needed for cellID decoding ({exc}). Source setup_MAPS.sh.")
    if not Path(compact).is_file():
        die(f"--compact geometry file not found: {compact}")
    print(f"[convert] loading geometry for cellID decoder: {compact}", file=sys.stderr)
    det = dd4hep.Detector.getInstance()
    det.fromXML(compact)
    try:
        return det.readout(readout).idSpec().decoder()
    except Exception as exc:  # noqa: BLE001
        die(f"could not get decoder for readout '{readout}' ({exc}).")


# --------------------------------------------------------------------------- #
# barrel position->pixel fallback (no segmentation)
# --------------------------------------------------------------------------- #
class BarrelMapper:
    def __init__(self, cfg: dict, pitch_x_mm, pitch_y_mm):
        self.px, self.py = pitch_x_mm, pitch_y_mm
        self.radius = float(cfg["radius_mm"])
        self.half_length = float(cfg["half_length_mm"])
        self.phi0 = float(cfg.get("phi0", 0.0))
        self.z0 = float(cfg.get("z0", 0.0))
        self.mode = str(cfg.get("tile_mode", "wrap")).lower()
        if self.mode == "wrap":
            self.n_col = int(math.ceil(2 * math.pi * self.radius / self.px))
            self.n_row = int(math.ceil(2 * self.half_length / self.py))
            self.sx, self.sy = 2 * math.pi * self.radius, 2 * self.half_length
        else:
            self.n_col = int(cfg["n_col"]); self.n_row = int(cfg["n_row"])
            self.sx = float(cfg["sensor_size_x_mm"]); self.sy = float(cfg["sensor_size_y_mm"])

    def map(self, x, y, z):
        phi = math.atan2(y, x)
        if self.mode == "wrap":
            xl = self.radius * (phi % (2 * math.pi))
            yl = (z - self.z0) + self.half_length
        else:
            dphi = (phi - self.phi0 + math.pi) % (2 * math.pi) - math.pi
            xl = self.radius * dphi + self.sx / 2.0
            yl = (z - self.z0) + self.sy / 2.0
        col, row = int(math.floor(xl / self.px)), int(math.floor(yl / self.py))
        if 0 <= col < self.n_col and 0 <= row < self.n_row:
            return col, row
        return None


# --------------------------------------------------------------------------- #
# podio reader (yields cellID too)
# --------------------------------------------------------------------------- #
def iter_events_podio(input_file):
    try:
        from podio.root_io import Reader
    except Exception:  # noqa: BLE001
        from podio import root_io
        Reader = root_io.Reader
    for i, fr in enumerate(Reader(input_file).get("events")):
        yield i, list(fr.getAvailableCollections()), fr


def pick_collection(want, cfg, available):
    if want:
        if want not in available:
            die(f"collection '{want}' not in file. Available: {sorted(available)}")
        return want
    for cand in cfg["input"]["simhit_collections"]:
        if cand in available:
            return cand
    die(f"no candidate collection found. Tried {cfg['input']['simhit_collections']}; "
        f"available {sorted(available)}")


# --------------------------------------------------------------------------- #
def parse_args(argv=None):
    p = argparse.ArgumentParser(
        description="EDM4hep SimTrackerHits -> PixESL CSV (BX,COL,ROW,h_time,qin).",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    p.add_argument("--input", required=True, help="input EDM4hep .root file")
    p.add_argument("--output", default="outputs/pixesl_hits.csv", help="output CSV")
    p.add_argument("--geometry", default="conversion/geometry_config.yaml")
    p.add_argument("--collections", default="conversion/collections_config.yaml")
    p.add_argument("--collection", default=None, help="force collection name")
    p.add_argument("--compact", default=None,
                   help="ALLEGRO/MAPS compact XML (needed for decode_cellid mode)")
    p.add_argument("--mode", default=None,
                   choices=["decode_cellid", "barrel_position"],
                   help="override target.mode in the geometry YAML")
    p.add_argument("--edep-unit", default="GeV", choices=list(_EDEP_TO_EV))
    p.add_argument("--time-unit", default="ns", choices=list(_TIME_TO_PS))
    p.add_argument("--max-events", type=int, default=None)
    p.add_argument("--bx-offset", type=int, default=0,
                   help="add to the per-file event index -> global BX "
                        "(for condor chunks: chunk*events_per_chunk)")
    return p.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    in_path = Path(args.input)
    if not in_path.is_file():
        die(f"input not found: {in_path}")

    geom = load_yaml(Path(args.geometry))
    coll_cfg = load_yaml(Path(args.collections))
    tgt = geom.get("target", {})
    mode = args.mode or tgt.get("mode", "decode_cellid")
    keep_layers = set(tgt.get("keep_layers", []) or [])
    want_coll = args.collection or tgt.get("collection")

    s = geom["sensor"]
    px = s["pixel_pitch_x_um"] / 1000.0
    py = s["pixel_pitch_y_um"] / 1000.0
    tcfg, ccfg = geom["timing"], geom["charge"]
    use_event_as_bx = bool(tcfg.get("use_event_as_bx", True))
    bx_spacing_ps = float(tcfg.get("bx_spacing_ps", 0.0))
    eh_eV = float(ccfg.get("eh_pair_energy_eV", 3.6))
    default_q = float(ccfg.get("default_qin_electrons", 1500))
    use_edep = bool(ccfg.get("use_edep_if_available", True))
    tscale = _TIME_TO_PS[args.time_unit]

    # ---- decoder / mapper -------------------------------------------------
    decoder = mapper = None
    cf = geom.get("cellid", {})
    if mode == "decode_cellid":
        if not args.compact:
            die("mode 'decode_cellid' needs --compact <MAPS_o1_v01.xml> to build "
                "the cellID decoder. (Or use --mode barrel_position.)")
        # collection name is needed to fetch the readout decoder
        decoder = None  # built after we know the collection
    else:
        mapper = BarrelMapper(geom["barrel_position"], px, py)

    # ---- read, decode/map, collect ---------------------------------------
    raw = []          # (bx, xidx_or_col, yidx_or_row, h_time, qin, layer, module, sensor, r, z)
    n_read = n_acc = n_rej = 0
    chosen = {"name": None, "available": None}
    n_events = 0
    per_layer = {}

    for evt_idx, avail, frame in iter_events_podio(str(in_path)):
        n_events += 1
        if chosen["name"] is None:
            chosen["available"] = avail
            chosen["name"] = pick_collection(want_coll, coll_cfg, avail)
            if mode == "decode_cellid":
                decoder = build_decoder(args.compact, chosen["name"])
        for h in frame.get(chosen["name"]):
            n_read += 1
            pos = h.getPosition()
            r = math.hypot(pos.x, pos.y)
            hit_time_ps = h.getTime() * tscale
            bx = evt_idx
            h_time = hit_time_ps if use_event_as_bx else bx * bx_spacing_ps + hit_time_ps
            qin = edep_to_qin(h.getEDep(), args.edep_unit, eh_eV, default_q, use_edep)

            if mode == "decode_cellid":
                cid = h.getCellID()
                layer = decoder.get(cid, cf.get("field_layer", "layer"))
                if keep_layers and layer not in keep_layers:
                    n_rej += 1
                    continue
                xidx = decoder.get(cid, cf.get("field_x", "x"))
                yidx = decoder.get(cid, cf.get("field_y", "y"))
                module = decoder.get(cid, cf.get("field_module", "module"))
                sensor = decoder.get(cid, cf.get("field_sensor", "sensor"))
                raw.append([bx, xidx, yidx, h_time, qin, layer, module, sensor, r, pos.z])
                per_layer[layer] = per_layer.get(layer, 0) + 1
                n_acc += 1
            else:
                mp = mapper.map(pos.x, pos.y, pos.z)
                if mp is None:
                    n_rej += 1
                    continue
                col, row = mp
                raw.append([bx, col, row, h_time, qin, -1, -1, -1, r, pos.z])
                n_acc += 1
        if args.max_events is not None and n_events >= args.max_events:
            break

    if chosen["name"] is None:
        die("file had no events.")
    if n_acc == 0:
        die(f"0 hits accepted from '{chosen['name']}'. "
            f"keep_layers={sorted(keep_layers)}; check mode/collection.")

    # ---- shift decoded pixel indices to non-negative COL/ROW --------------
    col_off = row_off = 0
    if mode == "decode_cellid":
        col_off = -min(r[1] for r in raw)
        row_off = -min(r[2] for r in raw)
        for r in raw:
            r[1] += col_off
            r[2] += row_off

    # ---- sort BX, h_time, COL, ROW ---------------------------------------
    raw.sort(key=lambda r: (r[0], r[3], r[1], r[2]))

    # ---- write strict + extended CSV -------------------------------------
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    ext = out.with_name(out.stem + "_extended.csv")
    with out.open("w") as f, ext.open("w") as fe:
        f.write("BX,COL,ROW,h_time,qin\n")
        fe.write("BX,COL,ROW,h_time,qin,layer,module,sensor,r_mm,z_mm\n")
        for bx, c, rr, ht, q, lay, mod, sen, r, z in raw:
            f.write(f"{bx},{c},{rr},{ht:.3f},{q:.3f}\n")
            fe.write(f"{bx},{c},{rr},{ht:.3f},{q:.3f},{lay},{mod},{sen},{r:.3f},{z:.3f}\n")

    # ---- metadata ---------------------------------------------------------
    meta = {
        "input_file": str(in_path.resolve()),
        "collection_used": chosen["name"],
        "available_collections": sorted(chosen["available"] or []),
        "mode": mode,
        "keep_layers": sorted(keep_layers),
        "hits_per_layer": {str(k): v for k, v in sorted(per_layer.items())},
        "n_events": n_events,
        "n_simhits_read": n_read,
        "n_hits_accepted": n_acc,
        "n_hits_rejected": n_rej,
        "pixel_pitch_x_um": s["pixel_pitch_x_um"],
        "pixel_pitch_y_um": s["pixel_pitch_y_um"],
        "col_offset": col_off, "row_offset": row_off,
        "layers": geom.get("layers", []),
        "edep_unit": args.edep_unit, "time_unit": args.time_unit,
        "use_event_as_bx": use_event_as_bx, "bx_spacing_ps": bx_spacing_ps,
        "eh_pair_energy_eV": eh_eV,
        "git_hash": git_hash(),
        "output_csv": str(out.resolve()),
        "extended_csv": str(ext.resolve()),
    }
    meta_path = out.with_name(out.stem + ".metadata.json")
    meta_path.write_text(json.dumps(meta, indent=2))

    # ---- report -----------------------------------------------------------
    print("=" * 64)
    print(f"[convert] collection : {chosen['name']}   mode: {mode}")
    print(f"[convert] events     : {n_events}")
    print(f"[convert] SimHits    : {n_read}  accepted: {n_acc}  rejected: {n_rej}")
    if mode == "decode_cellid":
        print(f"[convert] kept layers: {sorted(keep_layers)}  "
              f"hits/layer: {dict(sorted(per_layer.items()))}")
        print(f"[convert] COL/ROW offsets: +{col_off}/+{row_off}")
    print(f"[convert] CSV        -> {out}")
    print(f"[convert] extended   -> {ext}")
    print(f"[convert] metadata   -> {meta_path}")
    print("=" * 64)


if __name__ == "__main__":
    main()

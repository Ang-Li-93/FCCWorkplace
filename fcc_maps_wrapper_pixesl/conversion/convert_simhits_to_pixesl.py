#!/usr/bin/env python3
"""
convert_simhits_to_pixesl.py
============================
Convert EDM4hep ``SimTrackerHit`` collections (e.g. the ALLEGRO silicon-wrapper
``SiWrBCollection``) into a PixESL input table:

    BX,COL,ROW,h_time,qin

Columns
-------
BX      bunch-crossing number (first version: event index)
COL     pixel column, from local x via a simple barrel mapping
ROW     pixel row,    from local y (= z along the barrel) via the same mapping
h_time  hit time in picoseconds
qin     input charge in electrons (from energy deposit, or a default)

Reader
------
Uses ``podio.root_io.Reader`` (the canonical EDM4hep reader, available inside
the Key4hep stack). Falls back to ``uproot`` only if podio is unavailable.

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
# Small helpers
# --------------------------------------------------------------------------- #
def die(msg: str, code: int = 1) -> "None":
    print(f"ERROR: {msg}", file=sys.stderr)
    sys.exit(code)


def require_module(name: str, advice: str):
    try:
        return __import__(name)
    except Exception as exc:  # noqa: BLE001
        die(
            f"required Python module '{name}' could not be imported ({exc}).\n"
            f"       {advice}"
        )


def load_yaml(path: Path):
    yaml = require_module(
        "yaml",
        "Source the Key4hep stack (setup/setup_key4hep.sh) or 'pip install pyyaml'.",
    )
    if not path.is_file():
        die(f"config file not found: {path}")
    with path.open() as fh:
        return yaml.safe_load(fh)


def git_hash() -> str:
    try:
        here = Path(__file__).resolve().parent
        out = subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=here,
            stderr=subprocess.DEVNULL,
        )
        return out.decode().strip()
    except Exception:  # noqa: BLE001
        return "unknown"


def wrap_to_pi(angle: float) -> float:
    """Wrap an angle to [-pi, pi)."""
    return (angle + math.pi) % (2.0 * math.pi) - math.pi


# --------------------------------------------------------------------------- #
# Charge / time conversions
# --------------------------------------------------------------------------- #
_EDEP_TO_EV = {"GeV": 1.0e9, "MeV": 1.0e6, "keV": 1.0e3, "eV": 1.0}
_TIME_TO_PS = {"ns": 1.0e3, "ps": 1.0, "s": 1.0e12, "us": 1.0e6}


def edep_to_qin(edep: float, unit: str, eh_pair_eV: float,
                default_q: float, use_edep: bool) -> float:
    if use_edep and edep and edep > 0.0:
        return edep * _EDEP_TO_EV[unit] / eh_pair_eV
    return float(default_q)


# --------------------------------------------------------------------------- #
# Barrel -> pixel mapping
# --------------------------------------------------------------------------- #
class BarrelMapper:
    """Maps a global (x, y, z) hit position to (COL, ROW) on a barrel layer."""

    def __init__(self, geom: dict):
        s = geom["sensor"]
        w = geom["wrapper"]
        self.pitch_x = s["pixel_pitch_x_um"] / 1000.0  # mm
        self.pitch_y = s["pixel_pitch_y_um"] / 1000.0  # mm
        self.radius = float(w["radius_mm"])
        self.half_length = float(w["half_length_mm"])
        self.phi0 = float(w.get("phi0", 0.0))
        self.z0 = float(w.get("z0", 0.0))
        self.mode = str(w.get("tile_mode", "single")).lower()

        if self.mode == "wrap":
            circ = 2.0 * math.pi * self.radius
            self.n_col = int(math.ceil(circ / self.pitch_x))
            self.n_row = int(math.ceil(2.0 * self.half_length / self.pitch_y))
            self.size_x = circ
            self.size_y = 2.0 * self.half_length
        else:  # "single" tile centred at (phi0, z0)
            self.n_col = int(s["n_col"])
            self.n_row = int(s["n_row"])
            self.size_x = float(s["sensor_size_x_mm"])
            self.size_y = float(s["sensor_size_y_mm"])

    def map(self, x: float, y: float, z: float):
        """Return (COL, ROW) or None if the hit falls outside the grid."""
        phi = math.atan2(y, x)

        if self.mode == "wrap":
            # phi in [0, 2pi): unrolled circumference is the column axis.
            phi_pos = phi % (2.0 * math.pi)
            x_local = self.radius * phi_pos
            y_local = (z - self.z0) + self.half_length  # 0 .. 2*half_length
        else:
            dphi = wrap_to_pi(phi - self.phi0)
            x_local = self.radius * dphi + self.size_x / 2.0
            y_local = (z - self.z0) + self.size_y / 2.0

        col = int(math.floor(x_local / self.pitch_x))
        row = int(math.floor(y_local / self.pitch_y))
        if 0 <= col < self.n_col and 0 <= row < self.n_row:
            return col, row
        return None


# --------------------------------------------------------------------------- #
# Reading SimTrackerHits (podio primary, uproot fallback)
# --------------------------------------------------------------------------- #
def iter_events_podio(input_file: str):
    """Yield (event_index, available_collections, frame) using podio."""
    try:
        from podio.root_io import Reader  # type: ignore
    except Exception:  # noqa: BLE001
        try:
            from podio import root_io  # older API
            Reader = root_io.Reader  # type: ignore
        except Exception as exc:  # noqa: BLE001
            raise ImportError(f"podio not usable: {exc}") from exc

    reader = Reader(input_file)
    frames = reader.get("events")
    for i, frame in enumerate(frames):
        yield i, list(frame.getAvailableCollections()), frame


def read_hits(input_file: str, collection: str, want_collection: str | None,
              collections_cfg: dict, max_events: int | None):
    """
    Generator yielding dict(event, x, y, z, time_ns, edep) per SimTrackerHit.
    Also returns, on first event, the chosen collection name (via .chosen attr).
    Implemented with podio; raises ImportError to let caller try uproot.
    """
    chosen = {"name": None, "available": None}

    def _gen():
        n_events = 0
        for evt_idx, avail, frame in iter_events_podio(input_file):
            n_events += 1
            if chosen["name"] is None:
                chosen["available"] = avail
                chosen["name"] = pick_collection(
                    want_collection, collections_cfg, avail
                )
            coll = frame.get(chosen["name"])
            for h in coll:
                pos = h.getPosition()
                yield {
                    "event": evt_idx,
                    "x": pos.x, "y": pos.y, "z": pos.z,
                    "time_ns": h.getTime(),
                    "edep": h.getEDep(),
                }
            if max_events is not None and n_events >= max_events:
                break
        chosen["n_events"] = n_events

    return _gen, chosen


def pick_collection(want: str | None, cfg: dict, available: list) -> str:
    if want:
        if want not in available:
            die(
                f"requested collection '{want}' not in file.\n"
                f"       Available collections: {sorted(available)}"
            )
        return want
    for cand in cfg["input"]["simhit_collections"]:
        if cand in available:
            return cand
    die(
        "no candidate SimTrackerHit collection found in the file.\n"
        f"       Candidates tried: {cfg['input']['simhit_collections']}\n"
        f"       Available collections: {sorted(available)}"
    )


# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #
def parse_args(argv=None):
    p = argparse.ArgumentParser(
        description="Convert EDM4hep SimTrackerHits to a PixESL CSV "
                    "(BX,COL,ROW,h_time,qin).",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    p.add_argument("--input", required=True,
                   help="input EDM4hep .root file (podio)")
    p.add_argument("--output", default="outputs/pixesl_hits_zinclusive.csv",
                   help="output PixESL CSV path")
    p.add_argument("--geometry", default="conversion/geometry_config.yaml",
                   help="geometry/sensor YAML config")
    p.add_argument("--collections", default="conversion/collections_config.yaml",
                   help="collections YAML config (priority list)")
    p.add_argument("--collection", default=None,
                   help="force a specific SimTrackerHit collection name")
    p.add_argument("--edep-unit", default="GeV",
                   choices=list(_EDEP_TO_EV.keys()),
                   help="unit of SimTrackerHit energy deposit")
    p.add_argument("--time-unit", default="ns",
                   choices=list(_TIME_TO_PS.keys()),
                   help="unit of SimTrackerHit time")
    p.add_argument("--max-events", type=int, default=None,
                   help="process at most N events (debug)")
    return p.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)

    in_path = Path(args.input)
    if not in_path.is_file():
        die(f"input file not found: {in_path}")

    geom = load_yaml(Path(args.geometry))
    coll_cfg = load_yaml(Path(args.collections))
    mapper = BarrelMapper(geom)

    tcfg = geom["timing"]
    ccfg = geom["charge"]
    use_event_as_bx = bool(tcfg.get("use_event_as_bx", True))
    bx_spacing_ps = float(tcfg.get("bx_spacing_ps", 0.0))
    eh_eV = float(ccfg.get("eh_pair_energy_eV", 3.6))
    default_q = float(ccfg.get("default_qin_electrons", 1500))
    use_edep = bool(ccfg.get("use_edep_if_available", True))
    time_scale = _TIME_TO_PS[args.time_unit]

    # --- read hits (podio, fallback uproot) --------------------------------
    try:
        gen_factory, chosen = read_hits(
            str(in_path), None, args.collection, coll_cfg, args.max_events
        )
        hit_iter = gen_factory()
        backend = "podio"
    except ImportError:
        print("[convert] podio not available; falling back to uproot.",
              file=sys.stderr)
        hit_iter, chosen, backend = _read_hits_uproot(
            str(in_path), args.collection, coll_cfg, args.max_events
        )

    # --- loop & map --------------------------------------------------------
    rows = []
    n_read = n_acc = n_rej = 0
    events_seen = set()
    for hit in hit_iter:
        n_read += 1
        events_seen.add(hit["event"])
        mp = mapper.map(hit["x"], hit["y"], hit["z"])
        if mp is None:
            n_rej += 1
            continue
        col, row = mp
        bx = hit["event"]
        hit_time_ps = hit["time_ns"] * time_scale
        h_time = hit_time_ps if use_event_as_bx else bx * bx_spacing_ps + hit_time_ps
        qin = edep_to_qin(hit["edep"], args.edep_unit, eh_eV, default_q, use_edep)
        rows.append((bx, col, row, h_time, qin))
        n_acc += 1

    coll_name = chosen.get("name")
    n_events = chosen.get("n_events", len(events_seen))

    if coll_name is None:
        die("could not determine a collection (file had no events?).")

    # --- sort: BX, h_time, COL, ROW ----------------------------------------
    rows.sort(key=lambda r: (r[0], r[3], r[1], r[2]))

    # --- write CSV ---------------------------------------------------------
    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w") as fh:
        fh.write("BX,COL,ROW,h_time,qin\n")
        for bx, col, row, h_time, qin in rows:
            fh.write(f"{bx},{col},{row},{h_time:.3f},{qin:.3f}\n")

    # --- metadata JSON -----------------------------------------------------
    meta = {
        "input_file": str(in_path.resolve()),
        "reader_backend": backend,
        "collection_used": coll_name,
        "available_collections": sorted(chosen.get("available") or []),
        "n_events": n_events,
        "n_simhits_read": n_read,
        "n_hits_accepted": n_acc,
        "n_hits_rejected": n_rej,
        "pixel_pitch_x_um": geom["sensor"]["pixel_pitch_x_um"],
        "pixel_pitch_y_um": geom["sensor"]["pixel_pitch_y_um"],
        "n_col_effective": mapper.n_col,
        "n_row_effective": mapper.n_row,
        "sensor_size_x_mm": mapper.size_x,
        "sensor_size_y_mm": mapper.size_y,
        "wrapper_radius_mm": mapper.radius,
        "wrapper_half_length_mm": mapper.half_length,
        "mapping_mode": mapper.mode,
        "edep_unit": args.edep_unit,
        "time_unit": args.time_unit,
        "use_event_as_bx": use_event_as_bx,
        "bx_spacing_ps": bx_spacing_ps,
        "eh_pair_energy_eV": eh_eV,
        "git_hash": git_hash(),
        "output_csv": str(out_path.resolve()),
    }
    meta_path = out_path.with_suffix(out_path.suffix + ".metadata.json")
    if out_path.suffix == ".csv":
        meta_path = out_path.with_name(out_path.stem + ".metadata.json")
    with meta_path.open("w") as fh:
        json.dump(meta, fh, indent=2)

    # --- report ------------------------------------------------------------
    print("=" * 64)
    print(f"[convert] backend           : {backend}")
    print(f"[convert] collection used   : {coll_name}")
    print(f"[convert] events            : {n_events}")
    print(f"[convert] SimTrackerHits    : {n_read}")
    print(f"[convert] accepted          : {n_acc}")
    print(f"[convert] rejected (off-grid): {n_rej}")
    print(f"[convert] mapping mode      : {mapper.mode} "
          f"(grid {mapper.n_col} x {mapper.n_row})")
    print(f"[convert] CSV    -> {out_path}")
    print(f"[convert] meta   -> {meta_path}")
    if n_acc == 0:
        print("[convert] WARNING: 0 hits accepted. If using tile_mode='single', "
              "try 'wrap' in geometry_config.yaml, or check the collection.",
              file=sys.stderr)
    print("=" * 64)


# --------------------------------------------------------------------------- #
# uproot fallback (best-effort; podio is preferred)
# --------------------------------------------------------------------------- #
def _read_hits_uproot(input_file, want_collection, coll_cfg, max_events):
    uproot = require_module(
        "uproot",
        "Source the Key4hep stack, or 'pip install uproot awkward'.",
    )
    f = uproot.open(input_file)
    if "events" not in f:
        die(f"no 'events' TTree in {input_file}. Keys: {f.keys()}")
    tree = f["events"]
    branches = [b.split(".")[0] for b in tree.keys()]
    available = sorted(set(branches))
    name = pick_collection(want_collection, coll_cfg, available)

    px = tree[f"{name}.position.x"].array(library="np")
    py = tree[f"{name}.position.y"].array(library="np")
    pz = tree[f"{name}.position.z"].array(library="np")
    # time / EDep branch names vary slightly across edm4hep versions
    tarr = _first_branch(tree, [f"{name}.time", f"{name}.t"])
    earr = _first_branch(tree, [f"{name}.EDep", f"{name}.eDep", f"{name}.energy"])

    chosen = {"name": name, "available": available,
              "n_events": len(px) if max_events is None else min(max_events, len(px))}

    def _gen():
        n = len(px)
        if max_events is not None:
            n = min(n, max_events)
        for evt in range(n):
            xs, ys, zs = px[evt], py[evt], pz[evt]
            ts = tarr[evt] if tarr is not None else [0.0] * len(xs)
            es = earr[evt] if earr is not None else [0.0] * len(xs)
            for j in range(len(xs)):
                yield {"event": evt, "x": xs[j], "y": ys[j], "z": zs[j],
                       "time_ns": ts[j], "edep": es[j]}

    return _gen(), chosen, "uproot"


def _first_branch(tree, names):
    for n in names:
        if n in tree:
            return tree[n].array(library="np")
    return None


if __name__ == "__main__":
    main()

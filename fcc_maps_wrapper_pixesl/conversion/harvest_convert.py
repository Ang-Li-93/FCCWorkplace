#!/usr/bin/env python3
"""
harvest_convert.py  -  fast merge of many ddsim chunk files into ONE PixESL CSV.

Loads the dd4hep cellID decoder ONCE, then streams every events_<chunk>.edm4hep.root
in --indir, decoding VTXOB hits and assigning a global BX = chunk*NPER + event.
Reuses the helpers in convert_simhits_to_pixesl.py.

  python harvest_convert.py --indir <edm4hep dir> --output <csv> --nper 50 \
       --compact <MAPS_o1_v01.xml> --geometry geometry_config.yaml \
       --collections collections_config.yaml
"""
from __future__ import annotations
import argparse, glob, json, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import convert_simhits_to_pixesl as C   # noqa: E402


def chunk_index(fname: str):
    stem = Path(fname).name[len("events_"):-len(".edm4hep.root")]
    try:
        return int(stem)
    except ValueError:
        return None


def main(argv=None):
    ap = argparse.ArgumentParser(description="Merge ddsim chunks -> one PixESL CSV.")
    ap.add_argument("--indir", required=True)
    ap.add_argument("--output", required=True)
    ap.add_argument("--nper", type=int, required=True, help="events per chunk file")
    ap.add_argument("--compact", required=True)
    ap.add_argument("--geometry", default="conversion/geometry_config.yaml")
    ap.add_argument("--collections", default="conversion/collections_config.yaml")
    ap.add_argument("--edep-unit", default="GeV", choices=list(C._EDEP_TO_EV))
    ap.add_argument("--time-unit", default="ns", choices=list(C._TIME_TO_PS))
    args = ap.parse_args(argv)

    geom = C.load_yaml(Path(args.geometry))
    coll_cfg = C.load_yaml(Path(args.collections))
    tgt = geom.get("target", {})
    keep_layers = set(tgt.get("keep_layers", []) or [])
    want_coll = tgt.get("collection")
    cf = geom.get("cellid", {})
    s = geom["sensor"]; tc = geom["timing"]; cc = geom["charge"]
    use_event_as_bx = bool(tc.get("use_event_as_bx", True))
    bx_spacing = float(tc.get("bx_spacing_ps", 0.0))
    eh = float(cc.get("eh_pair_energy_eV", 3.6))
    dq = float(cc.get("default_qin_electrons", 1500))
    use_edep = bool(cc.get("use_edep_if_available", True))
    tscale = C._TIME_TO_PS[args.time_unit]

    files = sorted(glob.glob(f"{args.indir}/events_*.edm4hep.root"))
    files = [f for f in files if chunk_index(f) is not None]
    if not files:
        C.die(f"no events_*.edm4hep.root in {args.indir}")
    print(f"[harvest] {len(files)} chunk files; loading decoder once ...", file=sys.stderr)

    decoder = collname = None
    raw = []; per_layer = {}
    n_read = n_acc = n_rej = 0; n_events = 0; n_files_ok = 0

    for f in files:
        off = chunk_index(f) * args.nper
        try:
            for evt_idx, avail, frame in C.iter_events_podio(f):
                if decoder is None:
                    collname = C.pick_collection(want_coll, coll_cfg, avail)
                    decoder = C.build_decoder(args.compact, collname)
                n_events += 1
                bx = evt_idx + off
                for h in frame.get(collname):
                    n_read += 1
                    cid = h.getCellID()
                    layer = decoder.get(cid, cf.get("field_layer", "layer"))
                    if keep_layers and layer not in keep_layers:
                        n_rej += 1; continue
                    import math
                    r = math.hypot(h.getPosition().x, h.getPosition().y)
                    ht = h.getTime() * tscale
                    if not use_event_as_bx:
                        ht = bx * bx_spacing + ht
                    qin = C.edep_to_qin(h.getEDep(), args.edep_unit, eh, dq, use_edep)
                    raw.append([bx,
                                decoder.get(cid, cf.get("field_x", "x")),
                                decoder.get(cid, cf.get("field_y", "y")),
                                ht, qin, layer,
                                decoder.get(cid, cf.get("field_module", "module")),
                                decoder.get(cid, cf.get("field_sensor", "sensor")),
                                r, h.getPosition().z])
                    per_layer[layer] = per_layer.get(layer, 0) + 1
                    n_acc += 1
            n_files_ok += 1
        except Exception as exc:  # noqa: BLE001
            print(f"[harvest] WARN skipping {f}: {exc}", file=sys.stderr)

    if n_acc == 0:
        C.die("0 hits accepted across all chunks.")

    col_off = -min(r[1] for r in raw); row_off = -min(r[2] for r in raw)
    for r in raw:
        r[1] += col_off; r[2] += row_off
    raw.sort(key=lambda r: (r[0], r[3], r[1], r[2]))

    out = Path(args.output); out.parent.mkdir(parents=True, exist_ok=True)
    ext = out.with_name(out.stem + "_extended.csv")
    with out.open("w") as fo, ext.open("w") as fe:
        fo.write("BX,COL,ROW,h_time,qin\n")
        fe.write("BX,COL,ROW,h_time,qin,layer,module,sensor,r_mm,z_mm\n")
        for bx, c, rr, ht, q, lay, mod, sen, r, z in raw:
            fo.write(f"{bx},{c},{rr},{ht:.3f},{q:.3f}\n")
            fe.write(f"{bx},{c},{rr},{ht:.3f},{q:.3f},{lay},{mod},{sen},{r:.3f},{z:.3f}\n")

    meta = {"indir": str(Path(args.indir).resolve()), "n_chunk_files": n_files_ok,
            "nper": args.nper, "collection_used": collname,
            "keep_layers": sorted(keep_layers),
            "hits_per_layer": {str(k): v for k, v in sorted(per_layer.items())},
            "n_events": n_events, "n_simhits_read": n_read,
            "n_hits_accepted": n_acc, "n_hits_rejected": n_rej,
            "col_offset": col_off, "row_offset": row_off,
            "pixel_pitch_x_um": s["pixel_pitch_x_um"], "pixel_pitch_y_um": s["pixel_pitch_y_um"],
            "layers": geom.get("layers", []), "git_hash": C.git_hash(),
            "output_csv": str(out.resolve()), "extended_csv": str(ext.resolve())}
    out.with_name(out.stem + ".metadata.json").write_text(json.dumps(meta, indent=2))

    print("=" * 64)
    print(f"[harvest] files: {n_files_ok}/{len(files)}  events: {n_events}")
    print(f"[harvest] SimHits {n_read}  accepted {n_acc}  rejected {n_rej}")
    print(f"[harvest] hits/layer: {dict(sorted(per_layer.items()))}")
    print(f"[harvest] CSV      -> {out}")
    print(f"[harvest] extended -> {ext}")
    print("=" * 64)


if __name__ == "__main__":
    main()

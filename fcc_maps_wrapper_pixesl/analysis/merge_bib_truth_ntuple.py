#!/usr/bin/env python3
"""
merge_bib_truth_ntuple.py - merge bib_truth_part*.npz (make_bib_truth_ntuple.py)
into one flat ROOT file readable with plain ROOT / uproot / RDataFrame:

  hits        one row per SimTrackerHit (sorted by bx, det, layer, t), with the
              linked MCParticle and its primary ancestor copied onto the row
  particles   MCParticles linked to hits + ancestors + far-reaching primaries
  bx          one row per bunch crossing; first_hit/n_hits and
              first_particle/n_particles give the entry ranges in the two trees
  h_prim_logpt_cost   (log10 pT/MeV, |cos theta|) of ALL primaries
  provenance  JSON string (inputs, units, conventions)

and, next to it, <out>_primaries.root with the slim all-primaries dump.

With --pixesl-csv the 20 um MAPS pixel address (COL,ROW) of the extended PixESL
CSV is joined onto the vertex-barrel layer 3/4 hits (col20,row20; -1 elsewhere).
With --dets 0,1 only the hits of those detectors are written (a light
vertex-only file) and the particle table shrinks to the particles linked to
them, their ancestors and the primaries predicted to reach L3/L4.

  python3 merge_bib_truth_ntuple.py --partdir P --out F.root --expect 100 \
      [--pixesl-csv pixesl_..._extended.csv] [--dets 0,1]
"""
import argparse, glob, hashlib, json, subprocess, sys
from pathlib import Path

import numpy as np

DETS = ["vtxb", "vtxe", "siwrb", "siwrd", "dch"]          # det code 0..4
NLAY = 5
STEP = 250_000                                            # rows per basket


def code_version():
    """repository state plus a checksum of the two scripts (they may be uncommitted)"""
    here = Path(__file__).resolve().parent
    try:
        rev = subprocess.check_output(["git", "-C", str(here), "describe", "--always", "--dirty"], text=True).strip()
    except Exception:  # noqa: BLE001
        rev = "unknown"
    sha = {f: hashlib.sha256((here / f).read_bytes()).hexdigest()[:16]
           for f in ("make_bib_truth_ntuple.py", "merge_bib_truth_ntuple.py")}
    return {"git": rev, "sha256_16": sha}


def key(bx, idx):
    return bx.astype(np.int64) * 1_000_000 + idx.astype(np.int64)


def write_tree(f, name, cols, title):
    # no 8-bit branches: TTree::Draw/Scan read Char_t as characters ("det==0" fails)
    cols = {k: v.astype(np.int32) if v.dtype == np.int8 else v for k, v in cols.items()}
    n = len(next(iter(cols.values())))
    f.mktree(name, {k: v.dtype for k, v in cols.items()}, title=title)
    for i in range(0, max(n, 1), STEP):
        f[name].extend({k: v[i:i + STEP] for k, v in cols.items()})
    print(f"  tree {name}: {n} rows, {len(cols)} branches")


def join_pixesl(csv, h, sel):
    """Match every extended-CSV row to one layer-3/4 vertex-barrel hit."""
    import pandas as pd
    df = pd.read_csv(csv)
    idx = np.flatnonzero(sel)
    if len(df) != len(idx):
        sys.exit(f"ERROR: {csv} has {len(df)} rows but the ntuple has {len(idx)} MAPS-layer hits")
    groups = {}
    for i in idx:
        groups.setdefault((int(h["bx"][i]), int(h["layer"][i]), int(h["module"][i]),
                           int(h["sensor"][i])), []).append(i)
    col = np.full(len(h["bx"]), -1, np.int32)
    row = np.full(len(h["bx"]), -1, np.int32)
    worst = 0.0
    rad = np.hypot(h["x"], h["y"])
    for bx, c, r, tps, qin, lay, mod, sen, rr, z in zip(df.BX, df.COL, df.ROW, df.h_time, df.qin, df.layer,
                                                         df.module, df.sensor, df.r_mm, df.z_mm):
        cand = groups.get((bx, lay, mod, sen))
        if not cand:
            sys.exit(f"ERROR: no ntuple hit left for CSV row bx={bx} layer={lay} module={mod} sensor={sen}")
        # the CSV prints 3 decimals: z and r can each be off by 0.5 um, the time
        # by 0.0005 ps, the charge by the float32 rounding of edep
        d = np.array([abs(h["t"][i] * 1e3 - tps) + abs(h["z"][i] - z) * 1e3 + abs(rad[i] - rr) * 1e3
                      + abs(h["edep"][i] * 1e3 / 3.6 - qin) for i in cand])
        j = int(np.argmin(d))
        if len(d) > 1 and np.partition(d, 1)[1] < 2.2:
            sys.exit(f"ERROR: ambiguous PixESL match for bx={bx} layer={lay} module={mod} sensor={sen}")
        worst = max(worst, d[j])
        i = cand.pop(j)
        col[i], row[i] = c, r
    if worst > 1.1:
        sys.exit(f"ERROR: PixESL join residual {worst} (ps + um + um + e-) too large")
    print(f"  joined {len(df)} PixESL rows (worst residual {worst:.2e})")
    return col, row


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--partdir", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--expect", type=int, default=None, help="expected number of parts")
    ap.add_argument("--pixesl-csv", default=None)
    ap.add_argument("--dets", default=None,
                    help="comma-separated det codes to keep (default: all five)")
    ap.add_argument("--source", default="", help="provenance: input sample description")
    args = ap.parse_args()

    import uproot
    parts = sorted(glob.glob(f"{args.partdir}/bib_truth_part*.npz"))
    if args.expect is not None and len(parts) != args.expect:
        sys.exit(f"ERROR: found {len(parts)} parts, expected {args.expect}")
    acc, hprim, xe, ye, nfiles, config, ntotal = {}, None, None, None, 0, set(), set()
    for p in parts:
        d = np.load(p)
        nfiles += int(d["n_files"])
        ntotal.add(int(d["n_files_total"]))
        config.add(str(d["config"]))
        for k in d.files:
            if k == "hprim":
                hprim = d[k] if hprim is None else hprim + d[k]
            elif k == "hprim_xe":
                xe, ye = d["hprim_xe"], d["hprim_ye"]
            elif k not in ("hprim_ye", "n_files", "n_files_total", "config"):
                acc.setdefault(k, []).append(d[k])
    if len(config) != 1 or ntotal != {nfiles}:
        sys.exit(f"ERROR: parts disagree: {len(config)} configurations, {nfiles} files read, "
                 f"input directory listed as {sorted(ntotal)} files")
    config = json.loads(config.pop())
    a = {k: np.concatenate(v) for k, v in acc.items()}
    print(f"merged {len(parts)} parts: {nfiles} BXs, {len(a['hit_bx'])} hits, "
          f"{len(a['par_bx'])} particles, {len(a['prim_bx'])} primaries (dump)")

    # ---- particles (sorted by bx, mc_index) --------------------------------
    o = np.lexsort((a["par_mc_index"], a["par_bx"]))
    par = {k[4:]: v[o] for k, v in a.items() if k.startswith("par_")}
    pkey = key(par["bx"], par["mc_index"])
    if len(np.unique(pkey)) != len(pkey):
        sys.exit("ERROR: duplicate (bx, mc_index) in particles")

    # ---- hits (sorted by bx, det, layer, t) --------------------------------
    o = np.lexsort((a["hit_t"], a["hit_layer"], a["hit_det"], a["hit_bx"]))
    h = {k[4:]: v[o] for k, v in a.items() if k.startswith("hit_")}
    ip = np.searchsorted(pkey, key(h["bx"], h["mc_index"]))
    if not np.array_equal(pkey[ip], key(h["bx"], h["mc_index"])):
        sys.exit("ERROR: hit with a linked particle missing from the particle table")
    dets = sorted(int(x) for x in args.dets.split(",")) if args.dets else list(range(len(DETS)))
    if args.dets:
        s = np.isin(h["det"], dets)
        h, ip = {k: v[s] for k, v in h.items()}, ip[s]
        flag = np.zeros(len(pkey), np.int8)           # same bits as the read pass
        flag[ip] |= 1
        has = par["parent_index"] >= 0
        prow = np.searchsorted(pkey, key(par["bx"], np.where(has, par["parent_index"], par["mc_index"])))
        cur = np.unique(ip)
        while len(cur):
            up = prow[cur[has[cur]]]
            new = up[(flag[up] & 3) == 0]
            flag[up] |= 2
            cur = np.unique(new)
        flag[(par["gen_status"] == 1) & (par["pred_all"][:, 3:].sum(axis=1) > 0)] |= 4
        s = flag > 0
        remap = np.cumsum(s) - 1
        par = {k: v[s] for k, v in par.items()}
        par["flags"], pkey, ip = flag[s], pkey[s], remap[ip]
        print(f"  --dets {dets}: {len(h['bx'])} hits, {len(pkey)} particles kept")
    ia = np.searchsorted(pkey, key(h["bx"], par["prim_index"][ip]))
    if not np.array_equal(pkey[ia], key(h["bx"], par["prim_index"][ip])):
        sys.exit("ERROR: primary ancestor missing from the particle table")

    hits = {
        "bx": h["bx"], "det": h["det"], "layer": h["layer"], "side": h["side"],
        "module": h["module"], "sensor": h["sensor"], "ix": h["ix"], "iy": h["iy"],
        "cellID": h["cellID"],
        "x": h["x"], "y": h["y"], "z": h["z"],
        "r": np.hypot(h["x"], h["y"]).astype(np.float32),
        "phi": np.arctan2(h["y"], h["x"]).astype(np.float32),
        "t": h["t"], "edep": h["edep"], "pathlen": h["pathlen"],
        "px": h["px"], "py": h["py"], "pz": h["pz"],
        "pt": np.hypot(h["px"], h["py"]).astype(np.float32),
        "p": np.sqrt(h["px"].astype(np.float64)**2 + h["py"].astype(np.float64)**2
                     + h["pz"].astype(np.float64)**2).astype(np.float32),
        "quality": h["quality"],
        "by_secondary": ((h["quality"] >> 30) & 1).astype(np.int8),
        "hit_index": h["index"],
        "mc_index": h["mc_index"], "barcode": key(h["bx"], h["mc_index"]),
    }
    for k in ("pdg", "gen_status", "sim_status", "charge", "px", "py", "pz",
              "vx", "vy", "vz", "time", "depth", "parent_index"):
        hits[f"mc_{k}"] = par[k][ip]
    hits["mc_pt"] = np.hypot(par["px"][ip], par["py"][ip]).astype(np.float32)
    hits["prim_index"] = par["prim_index"][ip]
    for k in ("pdg", "px", "py", "pz", "vx", "vy", "vz"):
        hits[f"prim_{k}"] = par[k][ia]
    hits["prim_pt"] = np.hypot(par["px"][ia], par["py"][ia]).astype(np.float32)

    maps = (h["det"] == 0) & (h["layer"] >= 3)
    if args.pixesl_csv:
        hits["col20"], hits["row20"] = join_pixesl(args.pixesl_csv, h, maps)

    # ---- per-particle hit counts -------------------------------------------
    particles = {"bx": par["bx"], "mc_index": par["mc_index"], "barcode": pkey}
    for k in ("flags", "pdg", "gen_status", "sim_status", "charge", "mass", "time",
              "vx", "vy", "vz", "endx", "endy", "endz", "px", "py", "pz",
              "pendx", "pendy", "pendz", "parent_index", "prim_index", "depth",
              "n_daughters", "helix_R", "helix_rmin", "helix_rmax"):
        particles[k] = par[k]
    for name in ("pred_first", "pred_turn1", "pred_all"):
        for L in range(NLAY):
            particles[f"{name}_L{L}"] = np.ascontiguousarray(par[name][:, L])
    npar = len(pkey)
    particles["n_hits"] = np.bincount(ip, minlength=npar).astype(np.int32)
    direct = hits["by_secondary"] == 0
    for L in range(NLAY):
        s = (h["det"] == 0) & (h["layer"] == L)
        particles[f"n_hits_vb_L{L}"] = np.bincount(ip[s], minlength=npar).astype(np.int32)
        particles[f"n_direct_vb_L{L}"] = np.bincount(ip[s & direct], minlength=npar).astype(np.int32)

    # ---- per-BX table ------------------------------------------------------
    o = np.argsort(a["bx_bx"])
    bxid = a["bx_bx"][o].astype(np.int32)
    if len(np.unique(bxid)) != len(bxid) or len(bxid) != nfiles:
        sys.exit("ERROR: duplicate or missing BX ids")
    bx = {"bx": bxid, "n_mc": a["bx_n_mc"][o].astype(np.int32),
          "n_prim": a["bx_n_prim"][o].astype(np.int32),
          "sum_e_prim": a["bx_sum_e_prim"][o].astype(np.float32)}
    for i, dname in enumerate(DETS):
        bx[f"n_hits_{dname}"] = np.ascontiguousarray(a["bx_n_hits_det"][o][:, i])
    for L in range(NLAY):
        bx[f"n_hits_vb_L{L}"] = np.ascontiguousarray(a["bx_n_hits_vb"][o][:, L])
    for name in ("pred_first", "pred_turn1", "pred_all"):
        for L in range(NLAY):
            bx[f"{name}_L{L}"] = np.ascontiguousarray(a[f"bx_{name}"][o][:, L])
    bx["first_hit"] = np.searchsorted(hits["bx"], bxid, side="left").astype(np.int64)
    bx["n_hits"] = (np.searchsorted(hits["bx"], bxid, side="right") - bx["first_hit"]).astype(np.int32)
    bx["first_particle"] = np.searchsorted(par["bx"], bxid, side="left").astype(np.int64)
    bx["n_particles"] = (np.searchsorted(par["bx"], bxid, side="right") - bx["first_particle"]).astype(np.int32)
    if bx["n_hits"].sum() != len(hits["bx"]):
        sys.exit("ERROR: hits with a BX id missing from the BX table")

    prov = {
        "sample": args.source, "n_bx": nfiles, "n_parts": len(parts),
        "code": code_version(), "read_pass_config": config,
        "units": "mm, ns, MeV (momenta, mass), keV (edep)",
        "det": dict(enumerate(DETS)), "dets_in_file": dets,
        "hit": "one hit = one Geant4 track during one stay in one sensor (DD4hep "
               "Geant4TrackerWeightedAction); x,y,z = midpoint of its first and last stored step; "
               "px,py,pz,pt,p = mean of the track momentum at those two points (half the entry "
               "momentum for a track that stops in the sensor); edep, pathlen = sums over the stored "
               "steps; steps depositing <= 1 keV are not stored (edep ~10-20% low for e+- below "
               "100 MeV; a track re-entering the same sensor can be merged into one hit); "
               "ix,iy = pixel of the first stored step; hit_index = index in the collection of "
               "output_<bx>.root",
        "truth": "mc_* = MCParticle linked to the hit = nearest stored ancestor of the track that "
                 "made it; by_secondary=1 (quality bit 30): that track itself is not stored "
                 "(a secondary created below 1 MeV); prim_* = primary (GuineaPig) ancestor; "
                 "barcode = bx*1e6 + mc_index, mc_index = index in MCParticles of output_<bx>.root",
        "helix": "helix_*, pred_* = ideal helix (uniform field, vacuum: no beam pipe, no energy "
                 "loss; not a hit prediction) vs the vertex-barrel cylinders L0-L4: first crossing "
                 "inside the layer length (0/1), first turn (0-2), all turns (capped); NaN/0 for "
                 "neutral particles",
        "particle_flags": "bit0 linked to a hit in this file, bit1 ancestor of a linked particle, "
                          "bit2 primary with helix reach r >= reach_mm (all five detectors) or "
                          "predicted to cross L3/L4 (--dets files)",
    }
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    tmp = out.with_name(f".{out.name}.tmp")
    with uproot.recreate(tmp, compression=uproot.ZLIB(4)) as f:
        write_tree(f, "hits", hits, "SimTrackerHits with MC truth (1 row = 1 hit)")
        write_tree(f, "particles", particles, "MCParticles linked to hits, ancestors, far-reaching primaries")
        write_tree(f, "bx", bx, "per bunch crossing")
        f["h_prim_logpt_cost"] = (hprim, xe, ye)
        f["provenance"] = json.dumps(prov, indent=1)
    tmp.rename(out)
    print(f"-> {out}")

    if args.dets:
        return
    o = np.lexsort((a["prim_mc_index"], a["prim_bx"]))
    prim = {k[5:]: v[o] for k, v in a.items() if k.startswith("prim_")}
    pout = out.with_name(out.stem + "_primaries.root")
    tmp = pout.with_name(f".{pout.name}.tmp")
    with uproot.recreate(tmp, compression=uproot.ZLIB(4)) as f:
        write_tree(f, "primaries", prim, "all primaries above the dump pT threshold (MeV, mm)")
    tmp.rename(pout)
    print(f"-> {pout}")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
make_bib_truth_ntuple.py - parallel read pass for the BIB hit-level truth ntuple.

Reads every NSLICES-th file (offset SLICE) of a central EDM4hep directory
(1 file = 1 event = 1 bunch crossing) with uproot -- no podio, no geometry
load -- and writes bib_truth_part<SLICE>.npz holding

  hit_*   every SimTrackerHit of the tracker collections (vertex barrel/disks,
          Si wrapper, drift chamber): position, time, EDep, the hit momentum,
          the EDM4hep quality word and the index of the linked MCParticle
  par_*   the MCParticles that are linked to >=1 hit, all their ancestors, and
          every primary whose ideal helix reaches r >= --reach-mm
  bx_*    per-BX counters + the helix prediction (crossings per vertex layer)
  prim_*  slim dump of all primaries with pT > --prim-ptmin (independent
          re-derivations of the helix prediction start from this)
  hprim   (log10 pT, |cos theta|) histogram of ALL primaries

Merge with merge_bib_truth_ntuple.py into the single ROOT file.

Conventions of the central files (ddsim / DD4hep v01-36, Geant4TrackerWeightedAction
with HitPositionCombination=2, filter.tracker=edep1kev, Geant4TCUserParticleHandler
with minimalKineticEnergy=1 MeV), checked against the DD4hep source:
 - one hit = one Geant4 track during one stay in one sensor. Position = midpoint
   of its first and last stored step, momentum = mean of the momenta at those two
   points (half the entry momentum for a track that stops in the sensor), EDep
   and path length = sums over the stored steps. Steps depositing <= 1 keV are
   not stored, so EDep and path are ~10-20% low for e+- below 100 MeV, and a
   track that re-enters the same sensor can be merged into one hit;
 - the cellID pixel (ix, iy) is that of the first stored step, not of the position;
 - the MCParticle link points to the nearest STORED ancestor of the track that
   made the hit. Secondaries created below 1 MeV (inside r < 2.1 m, |z| < 3.2 m)
   are not stored; a hit made by such a track has quality bit 30
   ("produced by secondary") set.
The helix columns are an ideal calculation (uniform field, vacuum), not a hit
prediction: no beam pipe, no energy loss, no multiple scattering.

Units out: mm, ns, MeV (momenta, masses), keV (EDep).

  python3 make_bib_truth_ntuple.py --indir D --outdir O --slice K --nslices N
"""
import argparse, glob, json, re, sys
from pathlib import Path

import numpy as np

# det code -> collection (silicon share one cellID layout; the DCH has its own)
COLLECTIONS = ["VertexBarrelCollection", "VertexEndcapCollection",
               "SiWrBCollection", "SiWrDCollection", "DCHCollection"]
DCH_LAYERS_PER_SUPERLAYER = 8

# Vertex barrel layers for the helix prediction: (radius_mm, half_length_mm,
# z_offset_mm). Radii = mean hit radius of the layer (the flat sensors span
# 13.70-14.53, 23.72-24.89, 34.00-35.90, 130.50-133.66, 315.19-317.60 mm);
# half-lengths and z offsets = sensitive z range of the layer.
VTX_LAYERS = [(13.91, 96.5, 0.0), (24.16, 160.9, 0.5), (34.84, 241.4, 0.0),
              (131.33, 162.7, -1.0), (316.04, 325.9, 1.0)]
BFIELD_T = 2.0
C_LIGHT = 0.299792458          # GeV/(T m)  ->  R[mm] = pT[MeV] / (C_LIGHT*B[T])
MAX_TURNS = 500                # cap for the ideal (vacuum) looper count


def parse_encoding(enc):
    """'system:0:5,side:5:-2,...' -> {name: (offset, width, signed)}"""
    fields, off = {}, 0
    for item in enc.split(","):
        parts = item.split(":")
        if len(parts) == 3:
            name, off, width = parts[0], int(parts[1]), int(parts[2])
        else:
            name, width = parts[0], int(parts[1])
        fields[name] = (off, abs(width), width < 0)
        off += abs(width)
    return fields


def decode(cellid, field):
    off, width, signed = field
    v = ((cellid >> np.uint64(off)) & np.uint64((1 << width) - 1)).astype(np.int64)
    if signed:
        v = np.where(v >= (1 << (width - 1)), v - (1 << width), v)
    return v


def read_encodings(f):
    md = f["metadata"]
    keys = md["GPStringKeys"].array(library="np")[0]
    vals = md["GPStringValues"].array(library="np")[0]
    enc = {}
    for k, v in zip(keys, vals):
        k = str(k)
        if k.endswith("__CellIDEncoding"):
            enc[k[:-len("__CellIDEncoding")]] = parse_encoding(str(list(v)[0]))
    return enc


def helix_crossings(q, px, py, pz, vx, vy, vz):
    """Ideal helix (uniform B along +z, no material) of each particle vs the
    vertex-barrel cylinders. Returns R, rmin, rmax [mm] (NaN for neutral
    particles) and three integer (n, nlayer) arrays: first crossing inside the
    layer length (0/1), crossings inside the layer length during the first turn
    (0..2), and over all turns (each of the two crossings capped at MAX_TURNS)."""
    pt = np.hypot(px, py)
    sq, aq = np.sign(q), np.abs(q)
    ok = (pt > 0) & (aq > 0)
    R = np.where(ok, pt / (C_LIGHT * BFIELD_T * np.where(aq > 0, aq, 1.0)), np.nan)
    safe_pt = np.where(pt > 0, pt, 1.0)
    q = sq                                    # only the sense of rotation from here on
    # centre: q>0 turns clockwise seen from +z (F = q v x B, B along +z)
    xc = vx + q * R * py / safe_pt
    yc = vy - q * R * px / safe_pt
    c = np.hypot(xc, yc)
    rmax, rmin = c + R, np.abs(c - R)
    phic = np.arctan2(yc, xc)
    psi0 = np.arctan2(vy - yc, vx - xc)
    tanl = pz / safe_pt                       # dz / d(transverse path)
    n = len(pt)
    first = np.zeros((n, len(VTX_LAYERS)), np.int16)
    turn1 = np.zeros_like(first)
    allt = np.zeros_like(first)
    for il, (rl, hz, zoff) in enumerate(VTX_LAYERS):
        hit = ok & (rmin < rl) & (rmax > rl) & (c > 0)
        if not hit.any():
            continue
        k = np.clip((rl**2 - c[hit]**2 - R[hit]**2) / (2 * c[hit] * R[hit]), -1, 1)
        a = np.arccos(k)
        # angle travelled (>0, direction of motion = -q) to the two solutions; a
        # particle born on the layer radius meets its own start point one turn later
        d1 = np.mod(-q[hit] * (phic[hit] + a - psi0[hit]), 2 * np.pi)
        d2 = np.mod(-q[hit] * (phic[hit] - a - psi0[hit]), 2 * np.pi)
        d1 = np.where((d1 < 1e-9) | (d1 > 2 * np.pi - 1e-9), 2 * np.pi, d1)
        d2 = np.where((d2 < 1e-9) | (d2 > 2 * np.pi - 1e-9), 2 * np.pi, d2)
        dlo, dhi = np.minimum(d1, d2), np.maximum(d1, d2)
        Rh, tl, z0 = R[hit], tanl[hit], vz[hit] - zoff
        inz = lambda d: (np.abs(z0 + Rh * d * tl) <= hz) & (d < 2 * np.pi)   # noqa: E731
        f = inz(dlo).astype(np.int16)
        t1 = f + inz(dhi)
        # all turns: z advances by dzt per turn; count the turns m in
        # [0, MAX_TURNS) with |zc + m*dzt| <= hz (the first ones may be outside)
        na = np.zeros(hit.sum(), np.int64)
        dzt = 2 * np.pi * Rh * tl
        for d in (dlo, dhi):
            zc = z0 + Rh * d * tl
            with np.errstate(divide="ignore", invalid="ignore"):
                m1, m2 = (-hz - zc) / dzt, (hz - zc) / dzt
            cnt = (np.minimum(np.floor(np.maximum(m1, m2)), MAX_TURNS - 1)
                   - np.maximum(np.ceil(np.minimum(m1, m2)), 0) + 1)
            cnt = np.where(dzt == 0, np.where(np.abs(zc) <= hz, MAX_TURNS, 0), np.clip(cnt, 0, MAX_TURNS))
            na += np.nan_to_num(cnt).astype(np.int64)
        first[hit, il], turn1[hit, il] = f, t1
        allt[hit, il] = na
    return R, rmin, rmax, first, turn1, allt


def process_file(fn, uproot, acc, args, encodings):
    m = re.search(r"output_(\d+)\.root$", fn)
    if not m:
        raise RuntimeError(f"cannot parse BX id from {fn}")
    bx = int(m.group(1))
    with uproot.open(fn) as f:
        t = f["events"]
        if t.num_entries != 1:
            raise RuntimeError(f"{fn}: expected 1 event, found {t.num_entries}")
        mcb = ["PDG", "generatorStatus", "simulatorStatus", "charge", "time", "mass",
               "vertex.x", "vertex.y", "vertex.z", "endpoint.x", "endpoint.y", "endpoint.z",
               "momentum.x", "momentum.y", "momentum.z",
               "momentumAtEndpoint.x", "momentumAtEndpoint.y", "momentumAtEndpoint.z",
               "parents_begin", "parents_end", "daughters_begin", "daughters_end"]
        hb = ["cellID", "eDep", "time", "pathLength", "quality", "position.x", "position.y",
              "position.z", "momentum.x", "momentum.y", "momentum.z"]
        names = [f"MCParticles/MCParticles.{b}" for b in mcb]
        names += ["_MCParticles_parents/_MCParticles_parents.index"]
        for c in COLLECTIONS:
            names += [f"{c}/{c}.{b}" for b in hb] + [f"_{c}_particle/_{c}_particle.index"]
        a = t.arrays(names, library="np")
    mc = {b: a[f"MCParticles/MCParticles.{b}"][0] for b in mcb}
    par_idx = a["_MCParticles_parents/_MCParticles_parents.index"][0]
    nmc = len(mc["PDG"])

    # first parent (-1 for none) and primary ancestor by pointer jumping
    npar = (mc["parents_end"] - mc["parents_begin"]).astype(np.int32)
    if nmc >= 1_000_000 or (npar.max() if nmc else 0) > 1:
        raise RuntimeError(f"{fn}: {nmc} MCParticles / a particle with several parents: not supported")
    parent = np.full(nmc, -1, np.int32)
    has = npar > 0
    parent[has] = par_idx[mc["parents_begin"][has]]
    root = np.where(parent >= 0, parent, np.arange(nmc, dtype=np.int32))
    depth = (parent >= 0).astype(np.int32)
    for _ in range(64):                      # pointer jumping: doubles the step each pass
        nxt = root[root]
        if np.array_equal(nxt, root):
            break
        depth = depth + depth[root]
        root = nxt
    else:
        raise RuntimeError(f"{fn}: cyclic parent relation")

    gs = mc["generatorStatus"]
    q = mc["charge"].astype(np.float64)
    if not np.array_equal(q, np.rint(q)):
        raise RuntimeError(f"{fn}: fractional charge in MCParticles")
    px, py, pz = (mc[f"momentum.{k}"] * 1e3 for k in "xyz")
    vx, vy, vz = (mc[f"vertex.{k}"] for k in "xyz")
    isprim = gs == 1
    R, rmin, rmax, first, turn1, allt = helix_crossings(q, px, py, pz, vx, vy, vz)

    keep = np.zeros(nmc, np.int8)           # bit0 linked, bit1 ancestor, bit2 primary reach
    nhit_det = np.zeros(len(COLLECTIONS), np.int32)
    nhit_vb = np.zeros(len(VTX_LAYERS), np.int32)
    for det, c in enumerate(COLLECTIONS):
        h = {b: a[f"{c}/{c}.{b}"][0] for b in hb}
        link = a[f"_{c}_particle/_{c}_particle.index"][0].astype(np.int32)
        nh = len(h["cellID"])
        nhit_det[det] = nh
        if nh == 0:
            continue
        if len(link) != nh:
            raise RuntimeError(f"{fn}: {c} has {nh} hits but {len(link)} particle links")
        if link.min() < 0 or link.max() >= nmc:
            raise RuntimeError(f"{fn}: {c} particle link out of range")
        enc, cid = encodings[c], h["cellID"]
        if c == "DCHCollection":
            layer = decode(cid, enc["superlayer"]) * DCH_LAYERS_PER_SUPERLAYER + decode(cid, enc["layer"])
            side, module = decode(cid, enc["stereosign"]), decode(cid, enc["nphi"])
            sensor = ix = iy = np.zeros(nh, np.int64)
        else:
            layer, side = decode(cid, enc["layer"]), decode(cid, enc["side"])
            module, sensor = decode(cid, enc["module"]), decode(cid, enc["sensor"])
            ix, iy = decode(cid, enc["x"]), decode(cid, enc["y"])
        if det == 0:
            if layer.max() >= len(VTX_LAYERS):
                raise RuntimeError(f"{fn}: vertex-barrel layer {layer.max()} not in VTX_LAYERS")
            nhit_vb += np.bincount(layer, minlength=len(VTX_LAYERS)).astype(np.int32)
        keep[link] |= 1
        acc["hit_bx"].append(np.full(nh, bx, np.int32))
        acc["hit_det"].append(np.full(nh, det, np.int8))
        acc["hit_cellID"].append(cid.astype(np.uint64))
        acc["hit_layer"].append(layer.astype(np.int16))
        acc["hit_side"].append(side.astype(np.int8))
        acc["hit_module"].append(module.astype(np.int16))
        acc["hit_sensor"].append(sensor.astype(np.int16))
        acc["hit_ix"].append(ix.astype(np.int32))
        acc["hit_iy"].append(iy.astype(np.int32))
        for k in "xyz":
            acc[f"hit_{k}"].append(h[f"position.{k}"].astype(np.float64))
            acc[f"hit_p{k}"].append((h[f"momentum.{k}"] * 1e3).astype(np.float32))
        acc["hit_t"].append(h["time"].astype(np.float32))
        acc["hit_edep"].append((h["eDep"].astype(np.float64) * 1e6).astype(np.float32))
        acc["hit_pathlen"].append(h["pathLength"].astype(np.float32))
        acc["hit_quality"].append(h["quality"].astype(np.int32))
        acc["hit_index"].append(np.arange(nh, dtype=np.int32))
        acc["hit_mc_index"].append(link)

    # ancestors of every linked particle
    anc = parent[keep > 0]
    anc = anc[anc >= 0]
    while len(anc):
        new = anc[(keep[anc] & 3) == 0]
        keep[anc] |= 2
        anc = parent[np.unique(new)]
        anc = anc[anc >= 0]
    keep[isprim & (rmax >= args.reach_mm) & (q != 0)] |= 4

    s = np.flatnonzero(keep)
    acc["par_bx"].append(np.full(len(s), bx, np.int32))
    acc["par_mc_index"].append(s.astype(np.int32))
    acc["par_flags"].append(keep[s])
    acc["par_pdg"].append(mc["PDG"][s].astype(np.int32))
    acc["par_gen_status"].append(gs[s].astype(np.int8))
    acc["par_sim_status"].append(mc["simulatorStatus"][s].astype(np.int32))
    acc["par_charge"].append(q[s].astype(np.int8))
    acc["par_mass"].append((mc["mass"][s] * 1e3).astype(np.float32))
    acc["par_time"].append(mc["time"][s].astype(np.float32))
    for k in "xyz":
        acc[f"par_v{k}"].append(mc[f"vertex.{k}"][s].astype(np.float32))
        acc[f"par_end{k}"].append(mc[f"endpoint.{k}"][s].astype(np.float32))
        acc[f"par_p{k}"].append((mc[f"momentum.{k}"][s] * 1e3).astype(np.float32))
        acc[f"par_pend{k}"].append((mc[f"momentumAtEndpoint.{k}"][s] * 1e3).astype(np.float32))
    acc["par_parent_index"].append(parent[s])
    acc["par_prim_index"].append(root[s].astype(np.int32))
    acc["par_depth"].append(depth[s].astype(np.int16))
    acc["par_n_daughters"].append((mc["daughters_end"] - mc["daughters_begin"])[s].astype(np.int32))
    acc["par_helix_R"].append(R[s].astype(np.float32))
    acc["par_helix_rmin"].append(rmin[s].astype(np.float32))
    acc["par_helix_rmax"].append(rmax[s].astype(np.float32))
    acc["par_pred_first"].append(first[s])
    acc["par_pred_turn1"].append(turn1[s])
    acc["par_pred_all"].append(allt[s])

    pt = np.hypot(px, py)
    p = np.sqrt(pt**2 + pz**2)
    acc["bx_bx"].append(bx)
    acc["bx_n_mc"].append(nmc)
    acc["bx_n_prim"].append(int(isprim.sum()))
    acc["bx_sum_e_prim"].append(float(np.sqrt(p[isprim]**2 + (mc["mass"][isprim] * 1e3)**2).sum()))
    acc["bx_n_hits_det"].append(nhit_det)
    acc["bx_n_hits_vb"].append(nhit_vb)
    acc["bx_pred_first"].append(first[isprim].sum(axis=0).astype(np.int32))
    acc["bx_pred_turn1"].append(turn1[isprim].sum(axis=0).astype(np.int32))
    acc["bx_pred_all"].append(allt[isprim].sum(axis=0).astype(np.int32))

    with np.errstate(divide="ignore", invalid="ignore"):
        cost = np.where(p > 0, np.abs(pz) / p, 0.0)
        lpt = np.log10(np.where(pt > 0, pt, 1e-9))
    xe, ye = acc["hprim_xe"], acc["hprim_ye"]
    acc["hprim"] += np.histogram2d(np.clip(lpt[isprim], xe[0], np.nextafter(xe[-1], 0)),
                                   np.clip(cost[isprim], 0.0, np.nextafter(1.0, 0)), bins=[xe, ye])[0]

    d = np.flatnonzero(isprim & (pt > args.prim_ptmin))
    acc["prim_bx"].append(np.full(len(d), bx, np.int32))
    acc["prim_mc_index"].append(d.astype(np.int32))
    acc["prim_charge"].append(q[d].astype(np.int8))
    for k, arr in zip(("px", "py", "pz", "vx", "vy", "vz"), (px, py, pz, vx, vy, vz)):
        acc[f"prim_{k}"].append(arr[d].astype(np.float32))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--indir", required=True)
    ap.add_argument("--outdir", required=True)
    ap.add_argument("--slice", type=int, required=True)
    ap.add_argument("--nslices", type=int, required=True)
    ap.add_argument("--reach-mm", type=float, default=100.0,
                    help="store every primary whose ideal helix reaches this radius")
    ap.add_argument("--prim-ptmin", type=float, default=1.0,
                    help="pT threshold [MeV] of the slim all-primaries dump")
    args = ap.parse_args()

    import uproot
    from collections import defaultdict
    files = sorted(glob.glob(f"{args.indir}/output_*.root"))
    part = files[args.slice::args.nslices]
    if not part:
        sys.exit(f"no files for slice {args.slice}/{args.nslices}")
    print(f"[slice {args.slice}] {len(part)} files", file=sys.stderr)

    with uproot.open(part[0]) as f:
        encodings = read_encodings(f)
    acc = defaultdict(list)
    acc["hprim_xe"] = np.linspace(-4.0, 3.5, 151)      # log10(pT/MeV)
    acc["hprim_ye"] = np.linspace(0.0, 1.0, 21)        # |cos theta|
    acc["hprim"] = np.zeros((150, 20))
    for i, fn in enumerate(part):
        process_file(fn, uproot, acc, args, encodings)
        if i % 50 == 0:
            print(f"[slice {args.slice}] {i}/{len(part)}", file=sys.stderr)

    out = {}
    for k, v in acc.items():
        if k.startswith("hprim"):
            out[k] = v
        elif k.startswith("bx_"):
            out[k] = np.array(v)
        else:
            out[k] = np.concatenate(v)
    out["n_files"] = len(part)
    out["n_files_total"] = len(files)
    out["config"] = json.dumps({"vtx_layers_r_halfz_zoff_mm": VTX_LAYERS, "bfield_T": BFIELD_T,
                                "max_turns": MAX_TURNS, "reach_mm": args.reach_mm,
                                "prim_ptmin_MeV": args.prim_ptmin, "indir": args.indir})
    dst = Path(args.outdir) / f"bib_truth_part{args.slice}.npz"
    dst.parent.mkdir(parents=True, exist_ok=True)
    tmp = dst.with_name(f".{dst.name}.tmp.npz")
    np.savez_compressed(tmp, **out)
    tmp.rename(dst)
    print(f"[slice {args.slice}] {len(out['hit_bx'])} hits, {len(out['par_bx'])} particles, "
          f"{len(part)} BXs -> {dst}")


if __name__ == "__main__":
    main()

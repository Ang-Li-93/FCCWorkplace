#!/usr/bin/env python3
"""
check_sim_output.py
===================
Inspect an EDM4hep/podio simulation ROOT file: list all collections, flag the
SimTrackerHit collections, and print the first few hits of a chosen (or the
busiest wrapper) collection.

    python simulation/check_sim_output.py outputs/particle_gun_maps_wrapper.root
    python simulation/check_sim_output.py FILE.root --collection SiWrBCollection
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path


def die(msg, code=1):
    print(f"ERROR: {msg}", file=sys.stderr)
    sys.exit(code)


def get_reader(path):
    try:
        from podio.root_io import Reader
        return Reader(path)
    except Exception:
        try:
            from podio import root_io
            return root_io.Reader(path)
        except Exception as exc:  # noqa: BLE001
            die(f"podio reader unavailable ({exc}). Source setup/setup_key4hep.sh.")


def main(argv=None):
    ap = argparse.ArgumentParser(description="Inspect an EDM4hep sim ROOT file.")
    ap.add_argument("rootfile", help="EDM4hep/podio .root file")
    ap.add_argument("--collection", default=None,
                    help="collection to print hits from (default: auto)")
    ap.add_argument("--nhits", type=int, default=5,
                    help="number of hits to print")
    ap.add_argument("--nevents-scan", type=int, default=20,
                    help="events to scan for per-collection hit totals")
    args = ap.parse_args(argv)

    path = Path(args.rootfile)
    if not path.is_file():
        die(f"file not found: {path}")

    reader = get_reader(str(path))
    frames = reader.get("events")

    # First frame: list collections and their value types.
    it = iter(frames)
    try:
        first = next(it)
    except StopIteration:
        die("file has no events in category 'events'.")

    colls = list(first.getAvailableCollections())
    print("=" * 64)
    print(f"File: {path}")
    print(f"Collections ({len(colls)}):")
    simhit_colls = []
    for c in sorted(colls):
        try:
            obj = first.get(c)
            tname = type(obj).__name__
        except Exception:  # noqa: BLE001
            tname = "?"
        is_sth = "SimTrackerHit" in tname
        tag = "  <-- SimTrackerHit" if is_sth else ""
        if is_sth:
            simhit_colls.append(c)
        print(f"   {c:<34} {tname}{tag}")
    print("-" * 64)

    if not simhit_colls:
        print("No SimTrackerHit collections found. (Collections listed above.)")
        return

    print(f"SimTrackerHit collections: {simhit_colls}")

    # Count hits over a few events to find the busiest, unless user chose one.
    target = args.collection
    if target and target not in colls:
        die(f"requested collection '{target}' not present. "
            f"Available: {sorted(colls)}")

    if target is None:
        totals = {c: 0 for c in simhit_colls}
        # include the first frame, then scan a few more
        for c in simhit_colls:
            totals[c] += len(first.get(c))
        scanned = 1
        for fr in it:
            if scanned >= args.nevents_scan:
                break
            for c in simhit_colls:
                totals[c] += len(fr.get(c))
            scanned += 1
        print(f"hit totals over {scanned} event(s): "
              + ", ".join(f"{c}={n}" for c, n in totals.items()))
        # prefer a wrapper collection if it has hits
        ranked = sorted(totals.items(), key=lambda kv: kv[1], reverse=True)
        target = ranked[0][0] if ranked and ranked[0][1] > 0 else simhit_colls[0]

    print("-" * 64)
    print(f"First {args.nhits} hits of '{target}':")
    # re-open to read from event 0
    reader2 = get_reader(str(path))
    printed = 0
    for fr in reader2.get("events"):
        coll = fr.get(target)
        for h in coll:
            pos = h.getPosition()
            try:
                cid = h.getCellID()
            except Exception:  # noqa: BLE001
                cid = "n/a"
            print(f"   pos(mm)=({pos.x:9.2f},{pos.y:9.2f},{pos.z:9.2f})  "
                  f"t(ns)={h.getTime():8.3f}  EDep(GeV)={h.getEDep():.4e}  "
                  f"cellID={cid}")
            printed += 1
            if printed >= args.nhits:
                break
        if printed >= args.nhits:
            break
    if printed == 0:
        print(f"   (collection '{target}' had 0 hits in the scanned events)")
    print("=" * 64)


if __name__ == "__main__":
    main()

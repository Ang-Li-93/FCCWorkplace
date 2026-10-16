#!/usr/bin/env python3
"""Re-draw the W decay directions of H -> W+ W- -> 4 fermion events in a Les Houches event
file (LHEF), before the parton shower (PLAN.md Sec. 5.3, samples S2 'iso_decay' and S3
'diag_decay').  Only the two W decay products are changed: each W four-momentum (hence
both W masses, the H four-momentum, the Z decay and every other particle) is kept, the
pair's momentum in the W rest frame keeps its magnitude and only its direction is redrawn.

Modes
  iso   each W decays isotropically in its rest frame, independently of the other W:
        the decay-angle density is (1/4 pi)^2, i.e. rho = 1/9 exactly, and the joint
        distribution of the W four-momenta (the m_W* spectrum) is that of the input sample.
  diag  decohered SM state (CONVENTIONS.md Sec. 5): the diagonal of rho_SM(kappa) in the
        |m+ m-> basis, both spins quantised along k = W+ direction in the H frame
        (= W+ W- rest frame); kappa from this event's m(W+W-), m_W+, m_W-.  The helicity
        pair (+,-), (0,0), (-,+) is drawn with probabilities (1, kappa^2, 1)/(2 + kappa^2)
        and each analyser direction from |d^1_{m,+1}|^2 (W+) or |d^1_{m,-1}|^2 (W-).
        Frames as in qtomo.frames: lab -> H frame -> W frame by pure boosts.
  copy  pass-through (tests of the reader/writer).

The H decay products are the last four outgoing (status 1) fermions of each event (the
cards in config/generation/ list them last; override with --slots).  They are paired
into the W+ and W- systems as (fermion, antifermion) pairs of total charge +1 / -1 (and
matching lepton generation), which is unique for every W W -> 4f final state.
Analysers (CONVENTIONS.md Sec. 2): W+ -> l+ or the down-type antiquark, W- -> l- or the
down-type quark.

Usage (Key4hep python3 with numpy; no other dependencies):
    python3 randomise_w_decays.py --mode iso --seed 1234 in.lhe[.gz] out.lhe[.gz]
    # production chain (gen/run_hwwqe_job.sh), input from the factorised pass-1 cards:
    python3 randomise_w_decays.py --flatten-higgs --insert-resonances --beams-as-incoming \
        --mode iso --seed 1234 partonic.lhe events.lhe

The input must be a partonic (unshowered) LHEF.  The output is showered by Pythia8
(DelphesPythia8_EDM4HEP, config/generation/p8_lhe_hwwqe_ecm240.cmnd): WHIZARD 3.1.5 cannot
shower external events ('rescan' with ?update_event fails), see gen/README.md.
"""
import argparse
import gzip
import hashlib
import math
import re
import sys

import numpy as np

# ---------------------------------------------------------------------------
# Particle properties
# ---------------------------------------------------------------------------
CHARGE3 = {1: -1, 2: 2, 3: -1, 4: 2, 5: -1, 6: 2,          # 3 x electric charge
           11: -3, 12: 0, 13: -3, 14: 0, 15: -3, 16: 0}


def charge3(pdg):
    a = abs(pdg)
    return CHARGE3[a] * (1 if pdg > 0 else -1)


def is_fermion(pdg):
    return 1 <= abs(pdg) <= 16 and abs(pdg) not in (7, 8, 9, 10)


def is_analyser(pdg, w_charge):
    """W+ analyser: l+ (-11, -13, -15) or down-type antiquark (-1, -3, -5); W-: conjugates."""
    a = abs(pdg)
    down_type = a in (1, 3, 5, 11, 13, 15)
    return down_type and ((w_charge > 0 and pdg < 0) or (w_charge < 0 and pdg > 0))


def pair_ok(p1, p2):
    """(fermion, antifermion) of total charge +-1 with lepton-generation match."""
    if (p1 > 0) == (p2 > 0):
        return 0
    q = charge3(p1) + charge3(p2)
    if abs(q) != 3:
        return 0
    a1, a2 = abs(p1), abs(p2)
    if a1 > 10 or a2 > 10:                      # leptonic W: l and its own neutrino
        if not (a1 > 10 and a2 > 10) or (max(a1, a2) - min(a1, a2) != 1) or min(a1, a2) % 2 == 0:
            return 0
    return 1 if q > 0 else -1


def pair_quadruplet(pdgs):
    """Indices (into the 4-list) of the W+ pair and the W- pair, or None."""
    for (i, j), (k, l) in (((0, 1), (2, 3)), ((0, 2), (1, 3)), ((0, 3), (1, 2))):
        qa, qb = pair_ok(pdgs[i], pdgs[j]), pair_ok(pdgs[k], pdgs[l])
        if qa and qb and qa == -qb:
            return ((i, j), (k, l)) if qa > 0 else ((k, l), (i, j))
    return None


# ---------------------------------------------------------------------------
# Kinematics (E, px, py, pz); pure boosts as in qtomo.frames
# ---------------------------------------------------------------------------
def boost_to_rest(p, ref):
    e_r, p_r = ref[0], ref[1:]
    m = math.sqrt(max(e_r * e_r - p_r @ p_r, 0.0))
    dot = p_r @ p[1:]
    out = np.empty(4)
    out[0] = (e_r * p[0] - dot) / m
    out[1:] = p[1:] + ((dot / (e_r + m) - p[0]) / m) * p_r
    return out


def boost_from_rest(p, ref):
    r = ref.copy()
    r[1:] *= -1.0
    return boost_to_rest(p, r)


def mass(p):
    m2 = p[0] * p[0] - p[1:] @ p[1:]
    return math.sqrt(m2) if m2 > 0 else 0.0


def unit_vector(cos_t, phi, axis):
    """Unit vector with polar angle acos(cos_t) w.r.t. axis and azimuth phi around it."""
    axis = axis / np.linalg.norm(axis)
    e = np.eye(3)[np.argmin(np.abs(axis))]
    u = e - (e @ axis) * axis
    u /= np.linalg.norm(u)
    v = np.cross(axis, u)
    s = math.sqrt(max(0.0, 1.0 - cos_t * cos_t))
    return s * math.cos(phi) * u + s * math.sin(phi) * v + cos_t * axis


def redraw_pair(pa, pb, direction_in_rest, ref=None):
    """New (pa, pb) with the same sum P: pa along direction_in_rest in the rest frame of P,
    reached from the frame of the inputs (or from frame `ref` if given) by a pure boost."""
    P = pa + pb
    a_star = boost_to_rest(pa, P)
    pstar = math.sqrt(a_star[1:] @ a_star[1:])
    b_star = boost_to_rest(pb, P)
    na = np.concatenate(([a_star[0]], pstar * direction_in_rest))
    nb = np.concatenate(([b_star[0]], -pstar * direction_in_rest))
    return boost_from_rest(na, P), boost_from_rest(nb, P)


def sample_cos(m_proj, analyser_sign, rng):
    """cos(theta) w.r.t. k for an analyser projecting on |analyser_sign*1_n> (W+: +1, W-: -1)
    from a W in the state |m_proj> along k: density |d^1_{m, s}(theta)|^2."""
    s = m_proj * analyser_sign            # +1: (1+c)^2, -1: (1-c)^2, 0: 1-c^2
    u = rng.random()
    if s == 1:
        return 2.0 * u ** (1.0 / 3.0) - 1.0
    if s == -1:
        return 1.0 - 2.0 * u ** (1.0 / 3.0)
    while True:                           # 0: (3/4)(1 - c^2), accept-reject
        c = 2.0 * rng.random() - 1.0
        if rng.random() < 1.0 - c * c:
            return c


# ---------------------------------------------------------------------------
# LHEF streaming
# ---------------------------------------------------------------------------
def _open(path, mode):
    if path.endswith(".gz"):
        return gzip.open(path, mode + "t")
    return open(path, mode)


PARTICLE_FMT = ("{:>9d} {:>2d} {:>4d} {:>4d} {:>4d} {:>4d} {: .10E} {: .10E} {: .10E} "
                "{: .10E} {: .10E} {} {}\n")


def parse_particle(line):
    f = line.split()
    return {"pdg": int(f[0]), "status": int(f[1]), "moth": (int(f[2]), int(f[3])),
            "col": (int(f[4]), int(f[5])), "p": np.array([float(f[9]), float(f[6]), float(f[7]), float(f[8])]),
            "m": float(f[10]), "tail": (f[11], f[12]) if len(f) >= 13 else ("0.0000000000E+00", "9.0000000000E+00")}


def format_particle(d):
    p = d["p"]
    return PARTICLE_FMT.format(d["pdg"], d["status"], d["moth"][0], d["moth"][1], d["col"][0], d["col"][1],
                               p[1], p[2], p[3], p[0], d["m"], d["tail"][0], d["tail"][1])


def read_events(lines):
    """Yield ('text', line) for non-event lines and ('event', header, particles, extra)."""
    it = iter(lines)
    for line in it:
        if line.strip().startswith("<event"):
            block = [line]
            for l2 in it:
                block.append(l2)
                if l2.strip().startswith("</event>"):
                    break
            body = [b for b in block[1:-1]]
            head = body[0]
            n = int(head.split()[0])
            parts = [parse_particle(b) for b in body[1:1 + n]]
            extra = body[1 + n:]
            yield ("event", block[0], head, parts, extra, block[-1])
        else:
            yield ("text", line)


def h_decay_slots(parts, slots):
    fermions = [i for i, d in enumerate(parts) if d["status"] == 1 and is_fermion(d["pdg"])]
    if slots is None:
        return fermions[-4:] if len(fermions) >= 4 else None
    try:
        return [fermions[s] for s in slots]
    except IndexError:
        return None


def flatten_higgs(parts):
    """Factorised record (production e+e- -> f fbar H with H marked unstable, WHIZARD
    manual Sec. 5.8.2) -> the record of the equivalent 2 -> 6 hard process: the H line
    (status 2) is removed and its decay products become outgoing particles of the hard
    interaction (mothers = the H's mothers).  Indices of later particles shift by one.
    Returns the new list, or None if there is no single H with four fermion daughters."""
    hs = [i for i, d in enumerate(parts) if d["pdg"] == 25 and d["status"] == 2]
    if len(hs) != 1:
        return None
    ih = hs[0]
    h_lhef = ih + 1                                  # LHEF mother indices are 1-based
    dau = [i for i, d in enumerate(parts) if d["moth"][0] == h_lhef]
    if len(dau) != 4 or not all(is_fermion(parts[i]["pdg"]) for i in dau):
        return None

    def shift(m):
        return m - 1 if m > h_lhef else m

    out = []
    for i, d in enumerate(parts):
        if i == ih:
            continue
        e = dict(d)
        if i in dau:
            e["moth"] = parts[ih]["moth"]
        e["moth"] = (shift(e["moth"][0]), shift(e["moth"][1]))
        out.append(e)
    return out


def insert_resonances(parts, slots=None):
    """Insert the H -> W+ W- resonance chain (status 2, LHEF/LHA convention: a decay product
    has MOTHUP(1) = MOTHUP(2) = its resonance) in front of the four H decay products, so that
    a shower program treats each W pair as a resonance decay (FSR evolution from the W mass)
    and the MC record carries H -> W+ W- -> 4f as in the central samples.  Momenta: sums of
    the decay products (the W* virtualities are exact).  Returns the new list or None."""
    idx = h_decay_slots(parts, slots)
    pairing = pair_quadruplet([parts[i]["pdg"] for i in idx]) if idx else None
    if pairing is None:
        return None
    (a, b), (c, d) = pairing
    wp, wm = [idx[a], idx[b]], [idx[c], idx[d]]
    pos = min(idx)
    shift = lambda m: m + 3 if m > pos else m          # 1-based mother indices
    out = []
    for i, prt in enumerate(parts):
        e = dict(prt)
        e["moth"] = (shift(prt["moth"][0]), shift(prt["moth"][1]))
        out.append(e)
    h_moth = out[idx[0]]["moth"]
    zero_tail = ("0.0000000000E+00", "9.0000000000E+00")
    p_wp = parts[wp[0]]["p"] + parts[wp[1]]["p"]
    p_wm = parts[wm[0]]["p"] + parts[wm[1]]["p"]
    h_pos, wp_pos, wm_pos = pos + 1, pos + 2, pos + 3   # 1-based positions of the new lines
    new = [{"pdg": 25, "status": 2, "moth": h_moth, "col": (0, 0), "p": p_wp + p_wm, "m": mass(p_wp + p_wm),
            "tail": zero_tail},
           {"pdg": 24, "status": 2, "moth": (h_pos, h_pos), "col": (0, 0), "p": p_wp, "m": mass(p_wp), "tail": zero_tail},
           {"pdg": -24, "status": 2, "moth": (h_pos, h_pos), "col": (0, 0), "p": p_wm, "m": mass(p_wm), "tail": zero_tail}]
    for i in wp:
        out[i]["moth"] = (wp_pos, wp_pos)
    for i in wm:
        out[i]["moth"] = (wm_pos, wm_pos)
    return out[:pos] + new + out[pos:]


def beams_as_incoming(parts):
    """WHIZARD LHEF with ?keep_beams (beams with ISTUP = -9, the partons after beam spread
    and ISR with ISTUP = -1 and the ISR photons as outgoing particles) -> a plain LHA event
    in which the two beams are the incoming particles (ISTUP = -1, mothers 0 0) and the
    partons after ISR are dropped: everything they produced, and the ISR photons, become
    outgoing particles of the beam collision.  The event then conserves four-momentum up to
    the Gaussian beam-energy spread (~0.3 GeV), within Check:epTolErr of the official
    winter2023 LHE Pythia8 cards.  Returns the new list or None."""
    beams = [i for i, d in enumerate(parts) if d["status"] == -9]
    partons = [i for i, d in enumerate(parts) if d["status"] == -1]
    if len(beams) != 2 or len(partons) != 2:
        return None
    keep = [i for i in range(len(parts)) if i not in partons]
    newpos = {old + 1: new + 1 for new, old in enumerate(keep)}        # 1-based
    parton_to_beam = {partons[0] + 1: newpos[beams[0] + 1], partons[1] + 1: newpos[beams[1] + 1]}
    out = []
    for i in keep:
        e = dict(parts[i])
        if e["status"] == -9:
            e["status"], e["moth"] = -1, (0, 0)
        else:
            e["moth"] = tuple(parton_to_beam.get(m, newpos.get(m, 0)) if m else 0 for m in e["moth"])
        out.append(e)
    return out


def process_event(parts, mode, rng, slots):
    """Redraw the W decays in place; returns True if the event was modified."""
    idx = h_decay_slots(parts, slots)
    if idx is None:
        return False
    pdgs = [parts[i]["pdg"] for i in idx]
    pairing = pair_quadruplet(pdgs)
    if pairing is None:
        return False
    (a, b), (c, d) = pairing
    wp = [idx[a], idx[b]]                 # W+ pair, analyser first
    wm = [idx[c], idx[d]]
    if not is_analyser(parts[wp[0]]["pdg"], +1):
        wp.reverse()
    if not is_analyser(parts[wm[0]]["pdg"], -1):
        wm.reverse()
    pa_p, pb_p = parts[wp[0]]["p"], parts[wp[1]]["p"]
    pa_m, pb_m = parts[wm[0]]["p"], parts[wm[1]]["p"]
    if mode == "copy":
        return True
    if mode == "iso":
        for pair in (wp, wm):
            c_t, phi = 2.0 * rng.random() - 1.0, 2.0 * math.pi * rng.random()
            n = unit_vector(c_t, phi, np.array([0.0, 0.0, 1.0]))
            na, nb = redraw_pair(parts[pair[0]]["p"], parts[pair[1]]["p"], n)
            parts[pair[0]]["p"], parts[pair[1]]["p"] = na, nb
        return True
    # diag: work in the H frame (W+ W- rest frame), W frames by pure boosts from it
    W_p, W_m = pa_p + pb_p, pa_m + pb_m
    H = W_p + W_m
    m_h, m_p, m_m = mass(H), mass(W_p), mass(W_m)
    if m_p <= 0 or m_m <= 0:
        return False
    kappa = (m_h * m_h - m_p * m_p - m_m * m_m) / (2.0 * m_p * m_m)
    r = rng.random() * (2.0 + kappa * kappa)
    m_plus = 1 if r < 1.0 else (0 if r < 1.0 + kappa * kappa else -1)
    m_minus = -m_plus
    hf = {key: boost_to_rest(v, H) for key, v in (("ap", pa_p), ("bp", pb_p), ("am", pa_m), ("bm", pb_m))}
    k_hat = (hf["ap"] + hf["bp"])[1:]
    k_hat = k_hat / np.linalg.norm(k_hat)
    for (ka, kb, m_proj, sign, pair) in (("ap", "bp", m_plus, +1, wp), ("am", "bm", m_minus, -1, wm)):
        c_t = sample_cos(m_proj, sign, rng)
        n = unit_vector(c_t, 2.0 * math.pi * rng.random(), k_hat)   # direction in the W frame (from H frame)
        na, nb = redraw_pair(hf[ka], hf[kb], n)
        parts[pair[0]]["p"] = boost_from_rest(na, H)
        parts[pair[1]]["p"] = boost_from_rest(nb, H)
    return True


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("input")
    ap.add_argument("output")
    ap.add_argument("--mode", choices=("iso", "diag", "copy"), default="iso")
    ap.add_argument("--seed", type=int, default=None,
                    help="random seed (default: derived from the SHA-256 of the input file)")
    ap.add_argument("--slots", type=int, nargs=4, default=None,
                    help="positions (0-based, among the outgoing fermions) of the four H decay products")
    ap.add_argument("--flatten-higgs", action="store_true",
                    help="input from a factorised production x 'unstable H' run: remove the H line, its decay "
                         "products become outgoing particles of the hard process (the record of the equivalent "
                         "2 -> 6 process); use with --insert-resonances (gen/README.md)")
    ap.add_argument("--insert-resonances", action="store_true",
                    help="after redrawing, add the H -> W+ W- resonance lines (status 2) for a standalone "
                         "shower program reading the LHEF, e.g. Pythia8 (gen/README.md)")
    ap.add_argument("--beams-as-incoming", action="store_true",
                    help="write the beams (WHIZARD ISTUP = -9) as the incoming particles and drop the partons "
                         "after ISR, for LHA readers such as Pythia8 (gen/README.md)")
    args = ap.parse_args(argv)
    seed = args.seed
    if seed is None:
        h = hashlib.sha256()
        with open(args.input, "rb") as f:
            h.update(f.read(1 << 22))
        seed = int.from_bytes(h.digest()[:8], "little")
    rng = np.random.default_rng(seed)
    n_ev = n_mod = 0
    with _open(args.input, "r") as fin, _open(args.output, "w") as fout:
        for item in read_events(fin):
            if item[0] == "text":
                line = item[1]
                if line.strip().startswith("</header>"):
                    fout.write(f"<!-- HWWQE gen/randomise_w_decays.py: mode={args.mode} seed={seed} -->\n")
                fout.write(line)
                continue
            _, open_tag, head, parts, extra, close_tag = item
            n_ev += 1
            if args.flatten_higgs:
                flat = flatten_higgs(parts)
                if flat is None:
                    print(f"randomise_w_decays: event {n_ev}: no H -> 4f line to flatten", file=sys.stderr)
                    return 4
                parts = flat
                f = head.split()
                head = " " + " ".join([str(len(parts))] + f[1:]) + "\n"
            if process_event(parts, args.mode, rng, args.slots):
                n_mod += 1
            if args.insert_resonances:
                res = insert_resonances(parts, args.slots)
                if res is None:
                    print(f"randomise_w_decays: event {n_ev}: cannot insert resonances", file=sys.stderr)
                    return 5
                parts = res
                f = head.split()
                head = " " + " ".join([str(len(parts))] + f[1:]) + "\n"
            if args.beams_as_incoming:
                res = beams_as_incoming(parts)
                if res is None:
                    print(f"randomise_w_decays: event {n_ev}: no ISTUP = -9 beams / -1 partons", file=sys.stderr)
                    return 6
                parts = res
                f = head.split()
                head = " " + " ".join([str(len(parts))] + f[1:]) + "\n"
            fout.write(open_tag)
            fout.write(head)
            for d in parts:
                fout.write(format_particle(d))
            for e in extra:
                fout.write(e)
            fout.write(close_tag)
    print(f"randomise_w_decays: mode={args.mode} seed={seed} events={n_ev} modified={n_mod}", file=sys.stderr)
    return 0 if n_ev == n_mod or args.mode == "copy" else 3


if __name__ == "__main__":
    sys.exit(main())

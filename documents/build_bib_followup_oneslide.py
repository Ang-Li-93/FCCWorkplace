#!/usr/bin/env python3
"""One-slide version for 6 Oct 2026: rebuild slide 2 of 2026_10_06_MAPS_short.pptx (Ang's cut-down deck) as a self-contained answer. Same venv as build_bib_followup_deck.py plus matplotlib (formulas via bib_formula_png.py); writes 2026_10_06_MAPS_short_v2.pptx."""
import sys, re
from pathlib import Path
src = open(Path(__file__).with_name("build_bib_followup_deck.py"), encoding="utf8").read()
exec(src[: src.index("# ----------------------------------------------------------------------------- deck")])  # helpers + paths
from pptx import Presentation


def set_bullet(p, level=0):  # three levels: diamond, arrow, dash (overrides the two-level helper)
    pPr = p._p.get_or_add_pPr()
    marL, indent = [(342900, 342900), (742950, 285750), (1085850, 228600)][min(level, 2)]
    pPr.set("marL", str(marL)); pPr.set("indent", str(-indent))
    if level:
        pPr.set("lvl", str(level))
    font, char = [("Wingdings", "v"), ("Wingdings", "\u00d8"), ("Arial", "\u2013")][min(level, 2)]
    pPr.append(parse_xml(f'<a:buFont {A_NS} typeface="{font}"/>'))
    pPr.append(parse_xml(f'<a:buChar {A_NS} char="{char}"/>'))
from pptx.util import Inches, Pt
from pptx.enum.text import PP_ALIGN

IN = WS / "2026_10_06_MAPS_short.pptx"
OUT = Path(sys.argv[1]) if len(sys.argv) > 1 else WS / "2026_10_06_MAPS_short_v2.pptx"
prs = Presentation(str(IN))
s = prs.slides[1]

# drop Ang's bullet box and the rotated EMF; keep the table, title, footer, slide number
for shp in list(s.shapes):
    if shp.name in ("Body Bullets", "Picture 2", "Sample footer"):
        shp._element.getparent().remove(shp._element)

t = s.shapes.title
t.text_frame.text = ""
add_runs(t.text_frame.paragraphs[0], "Why layer 4 is above layer 3, and what a pT cut does", 28, bold=True)

tbl = [x for x in s.shapes if x.name == "pT cut table"][0]
tbl.left, tbl.top, tbl.width = Inches(7.15), Inches(3.4), Inches(5.7)
for col, w in zip(tbl.table.columns, (2.64, 1.02, 1.02, 1.02)):
    col.width = Inches(w)
for c, txt in ((0, "cut on the track pT at the hit"), (1, "layer 3 [hits/BX]"), (2, "layer 4 [hits/BX]")):
    tbl.table.cell(0, c).text_frame.paragraphs[0].runs[0].text = txt
for r in range(1, len(tbl.table.rows)):                      # L4/L3 without the uncertainty
    run = tbl.table.cell(r, 3).text_frame.paragraphs[0].runs[0]
    run.text = run.text.split("\u00b1")[0].strip()
for row in tbl.table.rows:
    row.height = Inches(0.27)
    for cell in row.cells:
        cell.margin_top = cell.margin_bottom = Inches(0.03)
        for para in cell.text_frame.paragraphs:
            for r in para.runs:
                r.font.size = Pt(12)

import tempfile, importlib.util
_spec = importlib.util.spec_from_file_location("formula_png", Path(__file__).with_name("formula_png.py") if Path(__file__).with_name("formula_png.py").exists() else Path(__file__).with_name("bib_formula_png.py"))
_fp = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(_fp)
_png = Path(tempfile.mkdtemp()) / "formula.png"
_fp.make(str(_png), width_in=6.1, height_in=1.2)
picture(s, _png, 0.62, 0.98, w=5.9, name="Formulas (matplotlib mathtext)")

# LEFT: the physics, read top to bottom
bullets(s, 0.62, 2.25, 5.9, 4.4, [
    [("Observed: L4 > L3, 0.565 vs 0.306 hits per BX", {"b": True}), " \u2014 mean over the 19,673 simulated crossings"],
    [("Can primaries from the beam line explain it? No", {"b": True})],
    (1, ["primary = an e\u207a or e\u207b of the pairs GuineaPig creates in one crossing (~1,120 per BX, median pT ~1 MeV), the input to Geant4"]),
    (1, ["helix of every primary (formulas above): 0.024 (L3) / 0.0036 (L4) reach the layer per BX, 91% / 86% confirmed in Geant4"]),
    (1, ["\u2192 field + geometry alone put L4 about 7\u00d7 below L3"]),
    (1, ["loopers (tracks crossing a layer again): 23% of L3 hits, 3.6% of L4"]),
    [("What makes the hits: sub-MeV electrons", {"b": True}), " \u2014 94% of L4 hits, 65% of L3"],
    (1, ["Geant4 secondaries born < 1 MeV: their hits are recorded (position, time, energy, momentum, flagged \u201csecondary\u201d)"]),
    (2, ["but not the particles: ddsim keeps > 1 MeV only, so birth point and parent photon are unknown"]),
    (2, ["to study them: re-simulate with cut = 0 and no 1 keV step cut"]),
    (1, ["origin: GuineaPig pair (forward, ~130 MeV) showers in the beam pipe / MDI"]),
    (1, ["\u2192 soft photons (keV\u2013MeV) \u2192 absorbed in the 50 \u00b5m Si of L3 / L4"]),
    (1, ["\u2192 photo-electron + 1.6 keV Auger electron: a hit each"]),
    (1, ["why L4: per-cm\u00b2 density drops only \u00d70.61 from L3 to L4 (charged tracks \u00d70.07), and L4 has 4.4\u00d7 the silicon"]),
], size=13, space=4)

# RIGHT: the plot, the pT-cut table, what a cut can and cannot do
picture(s, P_BIBS / "h_avg_hits_x_layer.png", 8.4, 1.04, w=3.2, name="4 Aug slide-5 plot, relabelled")
bullets(s, 7.15, 5.3, 5.7, 2.1, [
    [("A pT cut on the track at the hit restores the order", {"b": True}), ": it removes the sub-MeV electrons"],
    (1, ["truth-level only: the track momentum is known only in simulation"]),
    (1, ["a readout charge threshold does not: L4/L3 = 1.61 above 1000 e\u207b"]),
    (2, ["1000 e\u207b = 3.6 keV (3.6 eV per e\u2013h pair); these electrons deposit 10\u201350 keV, like a track through 50 \u00b5m Si"]),
    [("Readout load: ", {"b": True}), "0.26 / 0.44 fired 20 \u00b5m pixels per BX (L3 / L4), isolated"],
], size=12, space=3)

s.notes_slide.notes_text_frame.text = (
    "Right: the plot of the 4 Aug slide 5 (left), redrawn with its real axis title: SimTrackerHits per bunch crossing, "
    "whole layer (a layer total, not a density). Left: the helix calculation per layer and the pT-cut table.\n"
    "Calculation: R[mm] = pT[MeV]/(0.3 B[T]) = pT/0.6 at 2 T; a particle from the beam line reaches radius r if pT > 0.15 B r, "
    "i.e. 39 MeV for L3 (131 mm) and 95 MeV for L4 (316 mm); below ~600 MeV it cannot leave the tracker radially. Counting also "
    "the return arc and later turns of loopers in vacuum, the calculation still puts L4 three to seven times below L3. Most "
    "high-pT primaries are very forward and leave along z: 41 per crossing have enough pT for L3, but only 0.06% cross it inside "
    "its length. The helix code was checked against a brute-force stepper and re-implemented independently (identical counts in "
    "all 19,673 BX). The field in the barrel is 2 T to within 1%.\n"
    "What makes the hits: 'sub-MeV secondary' = a track created in the simulation below 1 MeV (not stored in the truth record; the "
    "hit is flagged and its momentum known from the hit itself). To record them: SIM.part.userParticleHandler = \"\" or "
    "SIM.part.minimalKineticEnergy = 0, plus SIM.filter.tracker = \"edep0\" for the 1 keV step cut; --part.keepAllParticles alone "
    "is a no-op with the default particle handler. About half of them are tagged directly as photon absorptions "
    "(photo-electron plus a 1.6 keV Si Auger electron at the same point); the photons come from showers of forward low-pT pairs "
    "in the beam pipe / MDI. Per cm2 the sub-MeV density falls only to 0.61 from L3 to L4 (charged-track hits: 0.07) and L4 has "
    "4.43x the silicon. L4 - L3 = 0.259 +- 0.012 hits per crossing (21 sigma), not carried by a few crossings.\n"
    "pT cut: the stored hit momentum is the mean of entry and exit momentum, so for an electron that stops in the sensor it is "
    "half the entry value; this only matters for cuts below 1 MeV. Generator-level cut on the primary behind the hit: 1.76 "
    "(> 1 MeV), 1.64 (> 5 MeV), 0.87 (> 10 MeV), 0.31 (> 20 MeV): the L4 hits descend from low-pT pairs (median 5 MeV) that never "
    "reach L4; they act through the radiation they produce where they hit material. For a common cut above 95 MeV L4 is higher "
    "again (1.5 +- 0.1): the few loopers that reach it cross the twice longer layer more often (0.018 vs 0.012 per crossing).\n"
    "Readout: 0.26 (L3) and 0.44 (L4) fired 20 um pixels per crossing, mostly isolated hits of several thousand electrons; a charge "
    "threshold does not remove them, pattern recognition should (not tested). Files, script and plots: "
    "https://angli-share.web.cern.ch/FCC/MAPS/BIB_IPC_LCC/truth_ntuple/")
# every "pT" in a text run of this slide -> "p" + subscript "T" (table headers, bullets)
import copy as _copy
from pptx.oxml.ns import qn as _qn
for r in list(s._element.iter(_qn("a:r"))):
    t = r.find(_qn("a:t"))
    if t is None or t.text is None or "pT" not in t.text:
        continue
    parts = t.text.split("pT")
    parent = r.getparent(); idx = list(parent).index(r)
    new_runs = []
    for i, seg in enumerate(parts):
        if i > 0:
            sub = _copy.deepcopy(r); sub.find(_qn("a:t")).text = "T"
            sub.find(_qn("a:rPr")).set("baseline", "-25000")
            new_runs.append(sub)
        if i < len(parts) - 1:
            seg = seg + "p"
        if seg:
            nr = _copy.deepcopy(r); nr.find(_qn("a:t")).text = seg
            new_runs.append(nr)
    parent.remove(r)
    for k, nr in enumerate(new_runs):
        parent.insert(idx + k, nr)
prs.save(str(OUT))
print("wrote", OUT)

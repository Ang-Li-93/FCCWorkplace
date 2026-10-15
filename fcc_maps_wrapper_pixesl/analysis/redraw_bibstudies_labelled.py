#!/usr/bin/env python3
"""
redraw_bibstudies_labelled.py - redraw the bib-studies drawhits histograms of the
vertex barrel with axis titles that say what is plotted.

drawhits.py stores most histograms without (or with misleading) axis titles and
sets the readable ones only in its own draw step. This script takes the merged
histogram file and draws every usable histogram in the same ROOT style with the
audited axis titles; histograms that are empty or broken by construction are not
drawn and are listed with the reason in SKIPPED.md.

  python3 redraw_bibstudies_labelled.py MERGED.root --outdir outputs/BIB/bibstudies_LCC_labelled
"""
import argparse, re
from pathlib import Path

SAMPLE = "IPC @ Z, LCC V106.2, central mdi_v2 sim, 19,673 BX; SimTrackerHits (1 keV simulation cut)"
HITS = "SimTrackerHits per BX"
LAYER = "vertex-barrel layer (0-2 inner barrel, 3-4 MAPS)"
NOT_OCC = "100 #times fired pixels / sensors (not an occupancy)"

# stem (without _VertexBarrelCollection; N = layer digit) -> title, x, y, z, options
LABELS = {
    "h_avg_hits_x_layer": ("Hits per bunch crossing, whole layer", LAYER, HITS + " (whole layer)", "", ""),
    "h_avg_firing_cells_x_layer": ("Fired pixels per bunch crossing (25 #mum pixels in L0-2, 50#times150 #mum in L3-4)", LAYER,
                                   "distinct fired pixels per BX (whole layer)", "", ""),
    "h_avg_occ_x_layer": ("Fired pixels per sensor - NOT a pixel occupancy", LAYER, NOT_OCC, "", "logy"),
    "h_occ_x_layerN": ("Fired pixels per BX in layer N, in units of its sensor count", NOT_OCC,
                       "fraction of bunch crossings per bin", "", "logx logy"),
    "h_occ_tot": ("Fired pixels per BX in the vertex barrel, in units of its 4,870 sensors", NOT_OCC,
                  "fraction of bunch crossings per bin", "", "logx logy"),
    "h_avg_hits_x_layer0_x_module": ("Hits per bunch crossing per module, layer 0",
                                     "module index in layer 0 (= stave #times 6 + z index)", HITS + " per module", "", ""),
    "hit_xy": ("End-on projection of the hit positions (all layers, summed along z)", "x [mm]", "y [mm]",
               HITS + " per 11.28#times11.28 mm^{2} map cell", "logz"),
    "hit_zr": ("Side projection of the hit positions (each band = half a layer)", "z [mm]", "r #times sign(x) [mm]",
               HITS + " per 8.64#times11.28 mm^{2} map cell", "logz"),
    "hit_zphi": ("Unrolled view, all five layers on top of each other", "z [mm]", "#phi [rad]",
                 HITS + " per (8.64 mm #times 0.0707 rad) cell", ""),
    "hist_xy_vs_layerN": ("End-on projection of the hit positions, layer N (summed along z)", "x [mm]", "y [mm]",
                          HITS + " per 11.28#times11.28 mm^{2} map cell", ""),
    "hist_zphi_vs_layerN": ("Unrolled view of layer N", "z [mm]", "#phi [rad]",
                            HITS + " per (8.64 mm #times 0.0707 rad) cell", ""),
    "h_hit_E_keV_map": ("Deposited energy per hit, by layer", "deposited energy per SimTrackerHit [keV]",
                        "vertex-barrel layer", HITS + " per keV", "logz"),
    "h_hit_particle_ID_map": ("Species of the stored MC particle linked to the hit, by layer",
                              "species of the linked MC particle (nearest stored ancestor)", "vertex-barrel layer", HITS, "logz"),
    "hist_hit_t_corr_map": ("Hit time minus light time from the origin, by layer (half of the prompt peak is below 0)",
                            "t_{hit} - |r_{hit}|/c [ns]", "vertex-barrel layer", HITS + " per 0.1 ns", "logz"),
    "h_hit_E_keV": ("Deposited energy per hit, all five layers", "deposited energy per SimTrackerHit [keV]",
                    HITS + " per keV", "", "logy"),
    "h_hit_particle_ID": ("Species of the stored MC particle linked to the hit, all five layers",
                          "species of the linked MC particle (nearest stored ancestor)", HITS, "", "logy"),
    "h_hit_particle_ID_E_MeV": ("Total energy of the linked MC particle at production",
                                "species of the linked MC particle", "total energy at production [GeV]",
                                HITS + " per 0.1 GeV", "logz"),
    "h_hit_particle_pt": ("p_{T} at production of the MC particle linked to the hit",
                          "p_{T} at production of the linked MC particle [GeV]", HITS + " per 0.1 GeV", "", "logy"),
    "h_hit_particle_E": ("Total energy at production of the MC particle linked to the hit",
                         "total energy at production of the linked MC particle [GeV]", HITS + " per 0.1 GeV", "", "logy"),
    "h_hit_particle_eta": ("Direction at production of the MC particle linked to the hit",
                           "#eta of the linked MC particle at production", HITS + " per 0.1", "", ""),
    "hist_hit_t": ("Hit time, all five layers (16% of L3 and 23% of L4 hits are beyond 20 ns)",
                   "hit time after the simulated bunch crossing [ns]", HITS + " per 0.1 ns", "", "logy"),
    "hist_hit_t_corr": ("Hit time minus light time from the origin, all five layers",
                        "t_{hit} - |r_{hit}|/c [ns]", HITS + " per 0.1 ns", "", "logy"),
    "h_hit_x_mm": ("Hit x, all five layers", "hit x [mm]", HITS + " per 0.1128 mm", "", "logy"),
    "h_hit_y_mm": ("Hit y, all five layers", "hit y [mm]", HITS + " per 0.1128 mm", "", "logy"),
    "h_hit_z_mm": ("Hit z, all five layers", "hit z [mm]", HITS + " per 0.0864 mm", "", ""),
    "h_hit_r_mm": ("Signed hit radius, all five layers", "hit radius #times sign(x) [mm]", HITS + " per 0.1128 mm", "", "logy"),
    "h_hit_eta": ("Pseudorapidity of the hit position, all five layers", "#eta of the hit position", HITS + " per 0.05", "", ""),
    "h_hit_rateDensity_layerN_VS_eta": ("bib-studies design rate of layer N on an ideal cylinder (21#times the simulated hit rate)",
                                        "|#eta| of the hit position",
                                        "hits/BX/cm^{2} #times 52 MHz #times 3 #times 5 [MHz/cm^{2}]", "", ""),
    "hist_z_density_vs_layerN_mm": ("Hits along z, layer N (all #phi)", "hit z [mm]", HITS + " per 8.64 mm", "", ""),
    "hist_phi_density_vs_layerN": ("Hits around #phi, layer N (all z)", "hit #phi [rad]", HITS + " per 0.0707 rad", "", ""),
}
SKIP = {
    "h_avg_hits_x_layer[1-4]_x_module": "module axis booked with a cumulative offset: 38% (L1), 61% (L2), 100% (L3, L4) of the hits are in the underflow",
    "h_hit_E_MeV(_map)?": "100 keV bins: 90% of the hits in the first bin; use the keV version",
    "h_hit_E_eV(_map)?": "covers 0-1 keV, below the 1 keV cut of the simulation: empty by construction",
    "h_tot_pu|h_avg_pu_x_layer|h_pu_x_layer[0-4]": "pile-up was not computed (integration time = 1 BX): empty",
}


def lookup(stem):
    for pat, why in SKIP.items():
        if re.fullmatch(pat, stem):
            return None, why
    if stem in LABELS:
        return LABELS[stem], None
    m = re.search(r"layer(\d)", stem)
    if m:
        key = stem.replace(f"layer{m.group(1)}", "layerN")
        if key in LABELS:
            return tuple(s.replace("layer N", f"layer {m.group(1)}") for s in LABELS[key]), None
    return None, "no audited label"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("merged", help="merged drawhits histogram file")
    ap.add_argument("--outdir", default="outputs/BIB/bibstudies_LCC_labelled", help="directory for <histogram>.png/.pdf and SKIPPED.md")
    ap.add_argument("--suffix", default="_VertexBarrelCollection", help="collection suffix stripped from the histogram names")
    args = ap.parse_args()

    import ROOT
    ROOT.gROOT.SetBatch(True)
    gs = ROOT.gStyle
    gs.SetOptStat(0)
    gs.SetPadTickX(1); gs.SetPadTickY(1)
    gs.SetPadTopMargin(0.14); gs.SetPadRightMargin(0.17); gs.SetPadBottomMargin(0.14); gs.SetPadLeftMargin(0.15)
    gs.SetTitleOffset(1.25, "x"); gs.SetTitleOffset(1.45, "y"); gs.SetTitleOffset(1.45, "z")
    gs.SetHistLineWidth(2)
    gs.SetPalette(ROOT.kBird)
    out = Path(args.outdir)
    out.mkdir(parents=True, exist_ok=True)
    f = ROOT.TFile.Open(args.merged)
    todo = []
    for key in f.GetListOfKeys():
        obj = key.ReadObj()
        if obj.InheritsFrom("TDirectory"):
            todo += [(obj.GetName(), k.ReadObj()) for k in obj.GetListOfKeys()]
        else:
            todo.append(("", obj))
    skipped, drawn = [], 0
    for folder, h in todo:
        stem = h.GetName().replace(args.suffix, "")
        lab, why = lookup(stem)
        if lab is None:
            skipped.append(f"- `{stem}`: {why}")
            continue
        title, tx, ty, tz, opt = lab
        c = ROOT.TCanvas("c", "c", 900, 650)
        h.SetTitle("")
        h.GetXaxis().SetTitle(tx)
        h.GetYaxis().SetTitle(ty)
        for ax in (h.GetXaxis(), h.GetYaxis()):
            ax.SetTitleSize(0.040); ax.SetLabelSize(0.038)
        if h.InheritsFrom("TH2"):
            h.GetZaxis().SetTitle(tz); h.GetZaxis().SetTitleSize(0.036); h.GetZaxis().SetLabelSize(0.034)
            if stem.startswith(("hit_zphi", "hist_zphi")):
                h.GetYaxis().SetRangeUser(-3.1416, 3.1416)
            h.Draw("COLZ")
        else:
            h.SetLineColor(ROOT.kAzure + 2)
            if h.GetXaxis().GetLabels() and h.GetXaxis().GetLabels().GetSize():
                h.GetXaxis().LabelsOption("h")
            if stem.startswith(("h_avg_hits_x_layer", "h_avg_firing", "h_avg_occ")) and "module" not in stem:
                h.GetXaxis().SetRangeUser(-0.5, 4.5)          # the sixth bin is not a layer
                h.GetXaxis().SetNdivisions(5)
            h.Draw("HIST")
        c.SetLogx("logx" in opt); c.SetLogy("logy" in opt); c.SetLogz("logz" in opt)
        t = ROOT.TLatex(); t.SetNDC()
        nchar = len(re.sub(r"#[a-z]+|[{}^_]", "", title))      # shrink long titles to the pad width
        t.SetTextSize(0.038 * min(1.0, 58 / nchar)); t.DrawLatex(0.15, 0.945, title)
        t.SetTextSize(0.026); t.SetTextColor(ROOT.kGray + 2); t.DrawLatex(0.15, 0.895, SAMPLE)
        for ext in ("png", "pdf"):
            c.Print(str(out / f"{stem}.{ext}"))
        c.Close()
        drawn += 1
    (out / "SKIPPED.md").write_text("# bib-studies histograms not redrawn\n\n" + "\n".join(sorted(skipped)) + "\n")
    print(f"drawn {drawn}, skipped {len(skipped)} -> {out}")


if __name__ == "__main__":
    main()

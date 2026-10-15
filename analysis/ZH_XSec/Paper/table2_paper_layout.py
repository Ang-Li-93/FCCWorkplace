#!/usr/bin/env python3
"""
Table 2 of arXiv:2512.21290 (JHEP version, Sec. 6) in the PAPER'S OWN LAYOUT, published value and
reproduction side by side: rows Z(ee)H, Z(mumu)H, Z(ll)H, Z(qq)H, Combination; columns Cut-based /
MVA-based at 240 GeV and at 365 GeV; every cell 'total (stat-only)' in % of sigma_ZH.

Three tables: (1) paper vs reproduction in the paper's layout (two decimals, the paper's
resolution); (2) the differences reproduction - paper, total and stat-only, in percentage points;
(3) every reproduction scan at three decimals, including the columns that have no counterpart in
the paper (the regular shape systematics profiled; JES / JER profiled in the hadronic fit), so
that nothing is lost. Markdown to stdout / --out, the first table as a LaTeX table in the paper's
booktabs style to --tex (tables 2 and 3 follow it as comment lines).

Mapping between the paper's two numbers per cell and the three scans that the fit drivers
(run_fit_leptonic.sh / run_fit_qq.sh / run_fit_combination.sh) leave in every run dir:
  paper total      <->  xsecSTATshapes  the card's shape nuisances frozen, the 1% lnN background
                                        normalizations norm_* floating  =  stat + 1% bkg norm
  paper stat-only  <->  xsecSTAT        --freezeParameters=allConstrainedNuisances: the norm_* AND
                                        the shape nuisances frozen  =  stat only
  no counterpart        xsec            nothing frozen: BES, the lepton / jet momentum scale (MUSCALE /
                                        ELSCALE / JETSCALE) and SQRTS profiled in addition - BEYOND
                                        the paper's quoted precision
  no counterpart        xsec of <dir><suffix><jesjer-suffix>/   JES and JER profiled as well (hadronic
                                        card only: the Z(qq)H and Combination rows, MVA-based dirs)
The mapping follows the paper's text. Its fit carries the 1% background normalizations as its only
nuisance parameters: "Background processes (WW, ZZ, Z/gamma* and rare processes) are modeled as
separate components, each with a normalization uncertainty of 1% included as a nuisance parameter
in the fit" and "Shape uncertainties are not included as nuisance parameters in this study"
(Sec. 5.3). Its stat-only number: "The statistical-only uncertainties, reported in parentheses in
Table 2, are obtained by fixing the background normalization parameters in the likelihood fit"
(Sec. 6; Table 2 caption: "obtained with the background normalization parameters fixed"). BES,
momentum scale and sqrt(s) were evaluated separately by repeating the fit with shifted inputs
("The combined uncertainty from these effects is approximately 0.095%, dominated by the BES
contribution") and JES / JER "are not included in the final quoted precision" (Sec. 5.3).

Configurations (paper Sec. 6): MVA-based = the BDT categorization and, for Z(qq)H, the 2D
m_recoil x m_jj fit (run dirs <dir><suffix>); Cut-based = "each final state is fitted in a single
region, and the hadronic final state is fitted using only the recoil mass distribution" (run dirs
<dir><cut-suffix>, built by makeWS_recoil_2cat.py --single-region and makeWS_2D_qq.py --recoil-only,
the same cards with one bin). Run dirs per energy (<base>/, base = S{ecm}/combine or --base):
  Z(ee)H       run_recoil_2cat_ee<sfx>          Z(mumu)H  run_recoil_2cat_mumu<sfx>
  Z(ll)H       run_recoil_2cat_combined<sfx>    Z(qq)H    run_2D_mrecoil_mjj_qq<sfx>
  Combination  run_{ecm}_all<sfx>               JES/JER   run_2D_mrecoil_mjj_qq<sfx><jesjer-suffix>,
                                                          run_{ecm}_all<sfx><jesjer-suffix>
Everything is read with table2.py's helpers (scan reading through fit_precision.py's crossings,
the fit_summary.txt cross-check, card parsing, the freeze-list footnote and the Sources block);
a missing run dir / scan / crossing gives 'n/a', never an abort (exit code 0 in every data
situation, like table2.py).

python3 + ROOT + stdlib (key4hep env or the combine container), from anywhere:
  python3 table2_paper_layout.py --suffix _oldbdt --cut-suffix _oldbdt_cutbased --label 'original models' \\
      --out documents/zh_xsec_table2_paper_layout_2026-09_oldbdt.md \\
      --tex documents/zh_xsec_table2_paper_layout_2026-09_oldbdt.tex
  --cut-suffix defaults to <suffix>_cutbased; --jesjer-suffix (default _jesjer) is appended to --suffix
"""
import argparse
import datetime
import os
import sys

PAPER = os.path.dirname(os.path.abspath(__file__))
sys.dont_write_bytecode = True
sys.path.insert(0, PAPER)
import table2 as T  # noqa: E402  (table2.py: ROOT setup, fit_precision import, readers, formatting)

# arXiv:2512.21290, JHEP version, Table 2 (Sec. 6 "Results"): relative uncertainty on sigma_ZH in %,
# (total, stat-only), all four columns. Source: the text extracted from the JHEP PDF (Table 2 block,
# "delta sigma_ZH / sigma_ZH (%)", read off line by line):
#   Final state   240 Cut-based  240 MVA-based  365 Cut-based  365 MVA-based
#   Z(e+e-)H      1.01 (0.97)    0.81 (0.78)    2.27 (2.16)    1.91 (1.90)
#   Z(mu+mu-)H    0.84 (0.80)    0.68 (0.66)    2.11 (2.03)    1.79 (1.79)
#   Z(l+l-)H      0.64 (0.62)    0.52 (0.50)    1.56 (1.48)    1.32 (1.30)
#   Z(qq)H        1.20 (0.63)    0.38 (0.30)    1.42 (0.63)    0.56 (0.47)
#   ZH            0.56 (0.44)    0.31 (0.26)    1.06 (0.58)    0.52 (0.44)
# The MVA-based columns are table2.py's PAPER_TABLE2 (checked identical at import).
PAPER_TABLE2 = {
    "cut": {
        240: {"ee": (1.01, 0.97), "mumu": (0.84, 0.80), "ll": (0.64, 0.62), "qq": (1.20, 0.63), "all": (0.56, 0.44)},
        365: {"ee": (2.27, 2.16), "mumu": (2.11, 2.03), "ll": (1.56, 1.48), "qq": (1.42, 0.63), "all": (1.06, 0.58)},
    },
    "mva": {
        240: {"ee": (0.81, 0.78), "mumu": (0.68, 0.66), "ll": (0.52, 0.50), "qq": (0.38, 0.30), "all": (0.31, 0.26)},
        365: {"ee": (1.91, 1.90), "mumu": (1.79, 1.79), "ll": (1.32, 1.30), "qq": (0.56, 0.47), "all": (0.52, 0.44)},
    },
}
for _ecm in (240, 365):
    if PAPER_TABLE2["mva"][_ecm] != T.PAPER_TABLE2[_ecm]:
        print(f"WARNING: MVA-based paper values at {_ecm} GeV differ between table2_paper_layout.py and table2.py",
              file=sys.stderr)

CONFIGS = [("cut", "Cut-based"), ("mva", "MVA-based")]   # the paper's column order per energy
HADRONIC = ("qq", "all")                                 # rows whose fit has jets (JES/JER run dirs)
TEX_ECM = {240: r"\sqrtsZH", 365: r"\sqrtsTop"}          # the paper's energy macros (fallbacks provided)
LAYOUT_LABEL = {"all": "ZH"}                                # the paper's row label under the "Combination" group
TITLE = ("Table 2 of arXiv:2512.21290 (JHEP) in the paper's layout: paper vs reproduction, cut-based / "
         "MVA-based at 240 and 365 GeV, total (stat-only) in % of sigma_ZH")
DEFINITIONS = [
    "- **paper total <-> `xsecSTATshapes`** (stat + 1% bkg norm): `--freezeParameters=<the card's shape "
    "nuisances>` - BES, MUSCALE / ELSCALE / JETSCALE and SQRTS fixed, the 1% lnN background normalizations "
    "`norm_*` floating. This is the paper's fit: \"Background processes (WW, ZZ, Z/gamma* and rare processes) "
    "are modeled as separate components, each with a normalization uncertainty of 1% included as a nuisance "
    "parameter in the fit\"; \"Shape uncertainties are not included as nuisance parameters in this study\" "
    "(Sec. 5.3).",
    "- **paper stat-only <-> `xsecSTAT`** (stat only): `--freezeParameters=allConstrainedNuisances` - every "
    "nuisance fixed (the paper-spec cards have no rateParam). The paper: \"The statistical-only uncertainties, "
    "reported in parentheses in Table 2, are obtained by fixing the background normalization parameters in the "
    "likelihood fit\" (Sec. 6; Table 2 caption: \"obtained with the background normalization parameters fixed\").",
    "- **`xsec` (nothing frozen)**: BES, the lepton / jet momentum scale and sqrt(s) profiled in addition - "
    "beyond the paper's quoted precision. The paper evaluated these effects separately by repeating the fit with "
    "shifted inputs (\"The combined uncertainty from these effects is approximately 0.095%, dominated by the BES "
    "contribution\", Sec. 5.3); the reproduction's shape templates come from the dedicated +-1% BES samples, "
    "the 1e-5 momentum-scale and the 2 MeV sqrt(s) variations (run book, Systematics).",
    "- **+ JES/JER**: `xsec` of the hadronic JES/JER run dirs (a 1% jet energy scale and an additional 1% jet "
    "energy smearing profiled as shape nuisances on every process of the hadronic card; Z(qq)H and the "
    "combination only). The paper evaluated them unprofiled (+3.9% / +3.2% relative degradation of the "
    "hadronic precision at 240 GeV) and they \"are not included in the final quoted precision\" (Sec. 5.3).",
    "- Configurations (Sec. 6): MVA-based = BDT categorization and, for Z(qq)H, the 2D m_recoil x m_jj fit; "
    "cut-based = \"each final state is fitted in a single region, and the hadronic final state is fitted using "
    "only the recoil mass distribution\" (the same cards with one bin: `makeWS_recoil_2cat.py --single-region`, "
    "`makeWS_2D_qq.py --recoil-only`; the leptonic single region = loBDT + hiBDT = the paper's Sec. 4.2 selection, "
    "the hadronic one = stage2 sel_Baseline_nomva, m_recoil projection).",
]


# ----------------------------------------------------------------------------- inputs
def suffix_of(args, cfg):
    return args.cut_suffix if cfg == "cut" else args.suffix


def collect(ecm, args):
    """{config: [rows in the paper's order]}; every row is table2.py's collect_row() dict plus key /
    label / group / paper / config, and 'jesjer' = the JES/JER dir's row for the hadronic rows (else None)."""
    base = T.run_base(args, ecm)
    out = {}
    for cfg, _ in CONFIGS:
        sfx = suffix_of(args, cfg)
        rows = []
        for key, label, template, group in T.ROWS:
            row = T.collect_row(os.path.join(base, template.format(ecm=ecm) + sfx))
            row.update(key=key, label=label, group=group, paper=PAPER_TABLE2[cfg][ecm][key], config=cfg, jesjer=None)
            if key in HADRONIC:
                v = T.collect_row(os.path.join(base, template.format(ecm=ecm) + sfx + args.jesjer_suffix))
                v.update(key=key, label=f"{label} + JES/JER", group=None, paper=row["paper"], config=cfg, jesjer=None)
                row["jesjer"] = v
            rows.append(row)
        out[cfg] = rows
    return out


def row_of(per, cfg, key):
    return next(r for r in per[cfg] if r["key"] == key)


def repro_pair(row):
    """(total, stat-only) of the reproduction in the paper's definition: (xsecSTATshapes, xsecSTAT)."""
    return T.sigma_of(row, "bkg"), T.sigma_of(row, "stat")


def jesjer_of(row):
    v = row.get("jesjer")
    return T.sigma_of(v, "total") if v and v["exists"] else None


def listed_rows(rows):
    """The nominal rows followed by the JES/JER rows that exist (footnote / sources / cross-check)."""
    return list(rows) + [r["jesjer"] for r in rows if r["jesjer"] and r["jesjer"]["exists"]]


# ----------------------------------------------------------------------------- formatting
def fmt2(x):
    return "n/a" if x is None else f"{100 * x:.2f}"


def pair2(tot, stat):
    return "n/a" if tot is None and stat is None else f"{fmt2(tot)} ({fmt2(stat)})"


def diff3(x, paper):
    return "n/a" if x is None else f"{100 * x - paper:+.3f}"


def diff_pair(row):
    tot, stat = repro_pair(row)
    ptot, pstat = row["paper"]
    return "n/a" if tot is None and stat is None else f"{diff3(tot, ptot)} ({diff3(stat, pstat)})"


def group_rows():
    """[(key, label, group-or-None)] in the paper's order, group given where a group header starts."""
    out, last = [], None
    for key, label, _, group in T.ROWS:
        start = group if group is not None and group != last else None
        if group is not None:
            last = group
        out.append((key, label, start))
    return out


# ----------------------------------------------------------------------------- markdown
def layout_table(results):
    ecms = [e for e, _ in results]
    ncell = 2 * len(ecms)
    out = ["| Final state | | " + " | ".join(f"{ecm} {cl}" for ecm in ecms for _, cl in CONFIGS) + " |",
           "|---|---|" + "---|" * ncell]
    for key, label, start in group_rows():
        if start:
            out.append(f"| **{start}** | |" + " |" * ncell)
        cells_p, cells_r = [], []
        for _, per in results:
            for cfg, _ in CONFIGS:
                row = row_of(per, cfg, key)
                ptot, pstat = row["paper"]
                cells_p.append(f"{ptot:.2f} ({pstat:.2f})")
                cells_r.append(pair2(*repro_pair(row)))
        out.append(f"| {LAYOUT_LABEL.get(key, label)} | paper | " + " | ".join(cells_p) + " |")
        out.append("| | reproduction | " + " | ".join(cells_r) + " |")
    return out


def diff_table(results):
    ecms = [e for e, _ in results]
    out = ["| Final state | " + " | ".join(f"{ecm} {cl}" for ecm in ecms for _, cl in CONFIGS) + " |",
           "|---|" + "---|" * (2 * len(ecms))]
    for key, label, _ in group_rows():
        cells = [diff_pair(row_of(per, cfg, key)) for _, per in results for cfg, _ in CONFIGS]
        out.append(f"| {label} | " + " | ".join(cells) + " |")
    return out


def full_table(ecm, per, args):
    """Every scan at three decimals for one energy; the JES/JER column only for a configuration that has
    at least one JES/JER run dir."""
    has_jj = {cfg: any(jesjer_of(r) is not None for r in per[cfg]) for cfg, _ in CONFIGS}
    head, ncol = ["Final state"], 0
    for cfg, cl in CONFIGS:
        head += [f"{cl}: stat only (xsecSTAT)", "stat + 1% bkg norm (xsecSTATshapes)", "+ regular syst (xsec)"]
        ncol += 3
        if has_jj[cfg]:
            head.append("+ JES/JER (hadronic)")
            ncol += 1
    out = ["| " + " | ".join(head) + " |", "|---|" + "---|" * ncol]
    for key, label, _ in group_rows():
        cells = []
        for cfg, _ in CONFIGS:
            row = row_of(per, cfg, key)
            cells += [T.pct(T.sigma_of(row, k)) for k in ("stat", "bkg", "total")]
            if has_jj[cfg]:
                cells.append(T.pct(jesjer_of(row)) if key in HADRONIC else "-")
        out.append(f"| {label} | " + " | ".join(cells) + " |")
    out.append("")
    notes = []
    for cfg, cl in CONFIGS:
        sfx = suffix_of(args, cfg)
        if not has_jj[cfg]:
            notes.append(f"{cl}: no JES/JER run dir (<dir>{sfx}{args.jesjer_suffix}), the column is omitted.")
    notes.append("'-' = leptonic final state, no jets. Quadrature components in %: regular syst sqrt(xsec^2 - "
                 "xsecSTATshapes^2), JES/JER sqrt(jesjer^2 - xsec^2), 1% bkg norm sqrt(xsecSTATshapes^2 - "
                 "xsecSTAT^2) ('~0' when the argument is negative):")
    # a quoted value is the half-width of the 2dNLL = 1 interval; flag profiles whose up and down
    # half-widths differ by more than 10% of it (e.g. the same-sided 1D BES templates of the 365 GeV
    # cut-based hadronic fit), which must not be read as symmetric precisions
    scan_name = {"stat": "xsecSTAT", "bkg": "xsecSTATshapes", "total": "xsec"}
    for cfg, cl in CONFIGS:
        for key, label, _ in group_rows():
            row = row_of(per, cfg, key)
            for k in ("stat", "bkg", "total"):
                scan = (row or {}).get("scans", {}).get(k) if row else None
                if not scan or scan.get("sigma") is None or "best" not in scan:
                    continue
                down, up = scan["best"] - scan["lo"], scan["hi"] - scan["best"]
                if abs(up - down) > 0.1 * scan["sigma"]:
                    notes.append(f"ASYMMETRIC PROFILE {cl} {label} {scan_name[k]}: 2dNLL = 1 at -{100 * down:.3f} / "
                                 f"+{100 * up:.3f} around r = {scan['best']:.4f}; the quoted {100 * scan['sigma']:.3f} "
                                 "is the half-width of the interval, not a symmetric precision.")
    out += notes
    out.append("")
    for cfg, cl in CONFIGS:
        parts = []
        for key, label, _ in group_rows():
            row = row_of(per, cfg, key)
            c1, c2, c3 = (T.sigma_of(row, k) for k in ("stat", "bkg", "total"))
            s = f"{label} bkg-norm {T.quad(c1, c2)}, regular syst {T.quad(c2, c3)}"
            if key in HADRONIC and has_jj[cfg]:
                s += f", JES/JER {T.quad(c3, jesjer_of(row))}"
            parts.append(s)
        out.append(f"- {cl}: " + "; ".join(parts) + ".")
    out.append("")
    return out


def per_run_dir(results, args):
    """table2.py's per-run-dir freeze-list footnote and Sources blocks, per energy and configuration."""
    out = []
    for ecm, per in results:
        base = T.run_base(args, ecm)
        for cfg, cl in CONFIGS:
            rows = listed_rows(per[cfg])
            sfx = suffix_of(args, cfg)
            out.append(f"#### {ecm} GeV, {cl} ({base}/<dir>{sfx}/)")
            out.append("")
            fn = T.footnote(rows, base, sfx)
            start = next((i for i, l in enumerate(fn) if l.startswith("Per run dir")), None)
            if start is not None:
                out += fn[start:]
            out += T.sources(rows, base, sfx, ecm)
    return out


# ----------------------------------------------------------------------------- LaTeX
def tex_table(results, args, title):
    ecms = [e for e, _ in results]
    ncol = 2 + 2 * len(ecms)
    out = [f"% {T.oneline(title)}",
           f"% generated {datetime.date.today()} by table2_paper_layout.py from {PAPER} (MVA-based run dirs "
           f"'{T.oneline(args.suffix)}', cut-based run dirs '{T.oneline(args.cut_suffix)}'"
           + (f", base {T.oneline(args.base)}" if args.base else "") + ")",
           "% cell = total (stat-only) in %. paper = Table 2 of arXiv:2512.21290 (JHEP). reproduction: total =",
           "% xsecSTATshapes (shape nuisances frozen, the 1% lnN background normalizations float = stat + 1% bkg norm),",
           "% stat-only = xsecSTAT (all constrained nuisances frozen) - the paper's definitions (its fit has only the 1%",
           "% normalizations as nuisances; stat-only = background normalizations fixed). The xsec scans (BES, momentum",
           "% scale, sqrt(s) profiled) and the JES/JER dirs have no counterpart in the paper: comment lines below.",
           "% Precision = half the 2*deltaNLL = 1 interval of the Asimov grid scan. Requires booktabs; the",
           "% \\providecommand lines are fallbacks for a standalone build, the paper's own macros win."]
    out += T.TEX_MACROS
    out += [r"\providecommand{\sqrtsZH}{$\sqrt{s} = 240$~GeV}", r"\providecommand{\sqrtsTop}{$\sqrt{s} = 365$~GeV}"]
    out += [r"\begin{table}[ht!]", r"\renewcommand{\arraystretch}{1.1}", r"\centering",
            (r"\caption{Relative uncertainties at the 68\% confidence level on the \ZH cross section (in \%) "
             r"for the individual final states and their combination: the published values (paper, Table~2 of "
             r"arXiv:2512.21290) and the reproduction"
             + (f" ({T.tex_escape(args.label)})" if args.label else "")
             + r". The cut-based configuration fits the recoil mass in a single region per final state; the "
             r"MVA-based configuration adds the BDT categorization and, for \ZqqH, a second fit dimension. The "
             r"values in parentheses are the statistical-only uncertainties, obtained with the background "
             r"normalization parameters fixed; like the paper's, the reproduction's totals include the 1\% "
             r"background-normalization uncertainties and no other nuisance parameter.}"),
            r"\vspace{0.5em}", r"\label{tab:results_xsec_paper_vs_repro}", "{\\small",
            r"\setlength{\tabcolsep}{5pt}",
            r"\begin{tabular}{ll" + "cc" * len(ecms) + "}", r"\toprule",
            f" & & \\multicolumn{{{ncol - 2}}}{{c}}{{$\\delta\\sigma_{{\\mathrm{{ZH}}}}/\\sigma_{{\\mathrm{{ZH}}}}$ (\\%)}} \\\\"]
    head, rules = " &", []
    for i, ecm in enumerate(ecms):
        macro = TEX_ECM.get(ecm) or ("$\\sqrt{s} = %d$~GeV" % ecm)
        head += " & \\multicolumn{2}{c}{%s}" % macro
        rules.append("\\cmidrule(lr){%d-%d}" % (3 + 2 * i, 4 + 2 * i))
    out.append(head + r" \\")
    out.append(" ".join(rules))
    out.append(r"\textbf{Final state} &" + "".join(f" & {cl}" for _ in ecms for _, cl in CONFIGS) + r" \\")
    out.append(r"\midrule")
    for i, (key, _, start) in enumerate(group_rows()):
        group = next(g for k, _, _, g in T.ROWS if k == key)
        if start:
            if i > 0:
                out.append(r"\midrule")
            out.append(f"\\multicolumn{{{ncol}}}{{l}}{{\\textbf{{{start}}}}} \\\\")
        elif group is None:
            out.append(r"\midrule")
        cells_p, cells_r = [], []
        for _, per in results:
            for cfg, _ in CONFIGS:
                row = row_of(per, cfg, key)
                ptot, pstat = row["paper"]
                cells_p.append(f"{ptot:.2f} ({pstat:.2f})")
                cells_r.append(pair2(*repro_pair(row)))
        out.append(f"{T.TEX_ROW[key]} & paper & " + " & ".join(cells_p) + r" \\")
        out.append(" & reproduction & " + " & ".join(cells_r) + r" \\")
    out += [r"\bottomrule", r"\end{tabular}", "}", r"\end{table}"]
    out.append("% differences reproduction - paper, total (stat-only), in percentage points (the paper is rounded to 0.01):")
    for key, label, _ in group_rows():
        cells = [f"{ecm} {cl} {diff_pair(row_of(per, cfg, key)):>17}" for ecm, per in results for cfg, cl in CONFIGS]
        out.append(f"%   {label:<12} " + "   ".join(cells))
    out.append("% every reproduction scan at three decimals: stat only (xsecSTAT) / stat + 1% bkg norm (xsecSTATshapes) /")
    out.append("% + regular syst profiled (xsec, beyond the paper) [/ + JES/JER (hadronic rows, MVA-based dirs)]")
    for ecm, per in results:
        for cfg, cl in CONFIGS:
            for key, label, _ in group_rows():
                row = row_of(per, cfg, key)
                vals = " / ".join(T.pct(T.sigma_of(row, k)) for k in ("stat", "bkg", "total"))
                jj = jesjer_of(row)
                if jj is not None:
                    vals += f" / {T.pct(jj)}"
                out.append(f"%   {ecm} GeV {cl:<9} {label:<12} {vals}")
    return out


# ----------------------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--suffix", default="", help="run-dir suffix of the MVA-based (paper-spec) fits, e.g. _oldbdt")
    ap.add_argument("--cut-suffix", default=None,
                    help="run-dir suffix of the cut-based (single-region) fits; default <suffix>_cutbased")
    ap.add_argument("--jesjer-suffix", default="_jesjer",
                    help="appended to the configuration's suffix for the hadronic JES/JER run dirs (default _jesjer)")
    ap.add_argument("--ecm", type=int, nargs="+", choices=(240, 365), default=[240, 365])
    ap.add_argument("--out", metavar="FILE.md", help="also write the markdown to FILE.md")
    ap.add_argument("--tex", metavar="FILE.tex", help="write the paper-layout table as a booktabs LaTeX table to FILE.tex")
    ap.add_argument("--label", default="", help="text prefixed to the title, e.g. 'original models'")
    ap.add_argument("--base", metavar="DIR", help="parent of the run dirs, '{ecm}' substituted (default <Paper>/S{ecm}/combine)")
    args = ap.parse_args()
    if args.cut_suffix is None:
        args.cut_suffix = args.suffix + "_cutbased"
    for name, val in (("--suffix", args.suffix), ("--cut-suffix", args.cut_suffix), ("--jesjer-suffix", args.jesjer_suffix)):
        if any(ch.isspace() or ch == os.sep for ch in val):
            print(f"WARNING: {name} {val!r} contains whitespace or '/', no run dir can match", file=sys.stderr)

    ecms = sorted(set(args.ecm))
    title = f"{args.label}: {TITLE}" if args.label else TITLE
    results = [(ecm, collect(ecm, args)) for ecm in ecms]

    out = [f"# {title}", ""]
    out.append(f"Generated {datetime.date.today()} by table2_paper_layout.py from {PAPER} (MVA-based run dirs "
               f"'<dir>{args.suffix}', cut-based run dirs '<dir>{args.cut_suffix}', JES/JER run dirs "
               f"'<dir>{args.suffix}{args.jesjer_suffix}'" + (f", base {args.base}" if args.base else "")
               + "). Relative uncertainty on sigma_ZH in %, Asimov data, r = sigma_ZH / SM; precision = half the "
               "distance between the 2*deltaNLL = 1 crossings around the best fit (fit_precision.py logic). "
               "Every cell of the first table is 'total (stat-only)' as in the paper; paper values from Table 2 of "
               "the JHEP version (Sec. 6). A missing run dir / scan / crossing gives n/a.")
    out.append("")
    out.append("Definitions and mapping (reproduction column <-> paper number):")
    out.append("")
    out += DEFINITIONS
    out.append("")
    out.append("## Table 2 in the paper's layout: paper vs reproduction (total (stat-only), %)")
    out.append("")
    out += layout_table(results)
    out.append("")
    out.append("Reproduction cells: xsecSTATshapes (xsecSTAT) rounded to the paper's two decimals; the three-decimal "
               "values are in the third table.")
    out.append("")
    out.append("## Differences reproduction - paper, total (stat-only), in percentage points")
    out.append("")
    out += diff_table(results)
    out.append("")
    out.append("The paper's values are rounded to 0.01, so |difference| <= 0.005 is exact agreement; the reproduction "
               "values enter at full precision.")
    out.append("")
    out.append("## Every reproduction scan (three decimals), including the columns beyond the paper")
    out.append("")
    for ecm, per in results:
        out.append(f"### sqrt(s) = {ecm} GeV")
        out.append("")
        out += full_table(ecm, per, args)
    out.append("## Per run dir: freeze lists and sources")
    out.append("")
    out += per_run_dir(results, args)
    n_cmp = n_bad = 0
    for _, per in results:
        for row in (r for cfg, _ in CONFIGS for r in listed_rows(per[cfg])):
            if row["exists"] and row["summary"] is not None:
                n_cmp += sum(1 for k, name, _, _ in T.COLS
                             if T.sigma_of(row, k) is not None and name in row["summary"]["values"])
                n_bad += len(row["check"])
    out.append(f"Cross-check against fit_summary.txt: {n_cmp} values compared (3 decimals), "
               + ("all match." if n_bad == 0 else f"{n_bad} MISMATCH(ES) - see the Sources blocks."))
    out.append("")
    text = "\n".join(out)
    print(text)
    if args.out:
        T.write(args.out, text)
    if args.tex:
        T.write(args.tex, "\n".join(tex_table(results, args, title)))


if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        raise
    except Exception:  # pylint: disable=broad-except  (never abort a chain: report, exit 0)
        import traceback
        traceback.print_exc()
        print("ERROR: table2_paper_layout.py failed (see the traceback above); exit code 0 by design", file=sys.stderr)
    sys.exit(0)

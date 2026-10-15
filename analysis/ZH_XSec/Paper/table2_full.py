#!/usr/bin/env python3
"""
Table 2 of arXiv:2512.21290 (JHEP version, MVA-based configuration) from the reproduction's
combine scans, with a FIFTH uncertainty column: the hadronic jet energy scale / resolution
nuisances (JES, JER) that the paper's Sec. 5.3 evaluated (1% jet energy scale shift, 1%
additional jet energy smearing: -3.9% / -3.2% relative degradation of the hadronic precision
at 240 GeV) but did not include in the quoted precision.

Built on table2.py (imported unchanged: scan reading, fit_summary.txt cross-check, card
parsing, footnote and sources blocks); the three first uncertainty columns are table2.py's,
read from the nominal run dirs <base>/<dir><suffix>/:
  c1 stat only                     = xsecSTAT        every constrained nuisance frozen = the paper's stat-only
  c2 stat + 1% bkg norm            = xsecSTATshapes  the card's shape nuisances frozen, norm_* lnN float
                                                     = the paper's quoted TOTAL (the 1% normalizations are
                                                     the only nuisance parameters of the paper's fit)
  c3 + regular syst profiled       = xsec            nothing frozen: BES, MUSCALE / ELSCALE / JETSCALE,
                                                     SQRTS profiled in addition - BEYOND the paper's quoted
                                                     precision (evaluated separately there, 0.095% combined)
  c4 c3 + JES/JER (hadronic)       = xsec of the run dirs <dir><suffix><jesjer-suffix>/ written by
                                     'makeWS_2D_qq.py --jesjer --tag <suffix><jesjer-suffix>' +
                                     'QQ_RUNDIR_SUFFIX=... run_fit_qq.sh 2d' (Z(qq)H) and
                                     'RUNDIR_SUFFIX=<suffix> QQ_RUNDIR_SUFFIX=<suffix><jesjer-suffix>
                                     ALL_RUNDIR_SUFFIX=<suffix><jesjer-suffix> run_fit_combination.sh all'
                                     (Combination): JES and JER profiled in addition to the regular
                                     shape nuisances. The leptonic final states have no jets: their
                                     c4 equals c3 by construction and is marked with an asterisk.
     In the JES/JER run dirs xsecSTAT / xsecSTATshapes freeze JES and JER as well, so they must
     reproduce c1 / c2 of the nominal dir: printed and checked (3 decimals) as a consistency test.
Below each table: the quadrature decomposition (1% bkg norm sqrt(c2^2 - c1^2), regular syst
sqrt(c3^2 - c2^2), JES/JER sqrt(c4^2 - c3^2), full syst sqrt(c4^2 - c1^2)), the hadronic
degradation of the total precision with JES only / JER only / both (run dirs
<dir><suffix>_jes / _jer / _jesjer; xsec(variant) / xsec(nominal) - 1, the quantity the paper's
Sec. 5.3 quotes: +3.9% JES, +3.2% JER for Z(qq)H at 240 GeV), the freeze lists of every run
dir as parsed from its fit_summary.txt header (footnote), and the Sources block with every
value cross-checked against the fit_precision.py printout tee'd to fit_summary.txt.

A missing run dir / scan / crossing gives 'n/a', never an abort (exit code 0 in every data
situation, like table2.py).

python3 + ROOT + stdlib (key4hep env or the combine container), from anywhere:
  python3 table2_full.py --suffix _oldbdt --label 'original models' \
      --out documents/zh_xsec_table2_2026-09_oldbdt.md --tex documents/zh_xsec_table2_2026-09_oldbdt.tex
  --jesjer-suffix SFX   appended to --suffix for the JES/JER run dirs (default _jesjer);
                        the JES-only / JER-only dirs take _jes / _jer in the same way
"""
import argparse
import datetime
import os
import sys

PAPER = os.path.dirname(os.path.abspath(__file__))
sys.dont_write_bytecode = True
sys.path.insert(0, PAPER)
import table2 as T  # noqa: E402  (table2.py: ROOT setup, fit_precision import, readers, formatting)

HADRONIC = ("qq", "all")          # rows whose fit has jets: Z(qq)H and the combination
VARIANTS = [("jes", "JES only", "_jes"), ("jer", "JER only", "_jer"), ("jesjer", "JES + JER", "_jesjer")]
PAPER_SEC53 = {240: {"jes": 3.9, "jer": 3.2}}   # relative degradation of the Z(qq)H total, paper Sec. 5.3 (%)
COLS = [("stat", "stat only (= paper stat)", r"stat"),
        ("bkg", "stat + 1% bkg norm (= paper total)", r"stat+bkg"),
        ("total", "+ regular syst profiled (beyond the paper)", r"+syst"),
        ("jesjer", "+ JES/JER (hadronic, beyond the paper)", r"+JES/JER")]
TITLE = ("Table 2 (arXiv:2512.21290, MVA-based) with the hadronic JES/JER nuisances: stat only (= paper stat) / "
         "stat + 1% bkg norm (= paper total) / + regular syst profiled (BES, lepton/jet scale, sqrt(s); beyond "
         "the paper) / + JES/JER (hadronic; beyond the paper), relative uncertainty on sigma_ZH in %")
TOL = 0.0015   # % : 3-decimal agreement


# ----------------------------------------------------------------------------- inputs
def collect(ecm, args):
    """table2.py's nominal rows, each with the JES/JER variant rows attached (hadronic rows only)."""
    rows = T.collect(ecm, args)
    base = T.run_base(args, ecm)
    for row in rows:
        row["variants"] = {}
        if row["key"] not in HADRONIC:
            continue
        template = next(t for k, _, t, _ in T.ROWS if k == row["key"])
        for vkey, vlabel, vsfx in VARIANTS:
            if vkey == "jesjer":
                vsfx = args.jesjer_suffix
            vrow = T.collect_row(os.path.join(base, template.format(ecm=ecm) + args.suffix + vsfx))
            vrow.update(key=row["key"], label=f"{row['label']} + {vlabel}", group=None, paper=row["paper"])
            row["variants"][vkey] = vrow
    return rows


def c4_of(row):
    """(fifth column value, asterisk?): xsec of the JES/JER dir for the hadronic rows, c3 otherwise."""
    if row["key"] in HADRONIC:
        v = row["variants"].get("jesjer")
        return (T.sigma_of(v, "total") if v and v["exists"] else None), False
    return T.sigma_of(row, "total"), True


def values(row):
    """(c1, c2, c3, c4) as fractions (None when n/a)."""
    return tuple(T.sigma_of(row, k) for k in ("stat", "bkg", "total")) + (c4_of(row)[0],)


def consistency(row):
    """Check that the JES/JER dirs' frozen scans reproduce the nominal c1 / c2: list of notes."""
    notes = []
    c1, c2 = T.sigma_of(row, "stat"), T.sigma_of(row, "bkg")
    for vkey, vlabel, _ in VARIANTS:
        v = row["variants"].get(vkey)
        if not v or not v["exists"]:
            continue
        for key, ref, name in (("stat", c1, "xsecSTAT"), ("bkg", c2, "xsecSTATshapes")):
            mine = T.sigma_of(v, key)
            if mine is None or ref is None:
                continue
            d = 100 * abs(mine - ref)
            notes.append(f"{row['label']} {vlabel}: {name} {100 * mine:.3f}% vs nominal {100 * ref:.3f}% "
                         + ("OK" if d <= TOL else f"MISMATCH ({d:+.3f}%)"))
    return notes


# ----------------------------------------------------------------------------- output
def pct_star(x, star):
    return T.pct(x) + ("*" if star and x is not None else "")


def rel(v, nom):
    """xsec(variant) / xsec(nominal) - 1 in %."""
    if v is None or not nom:
        return "n/a"
    return f"{100 * (v / nom - 1):+.2f}%"


def all_rows(rows):
    """Nominal rows followed by the variant rows (for the footnote / sources blocks)."""
    out = list(rows)
    for row in rows:
        out += [row["variants"][k] for k, _, _ in VARIANTS if k in row["variants"]]
    return out


def energy_section(ecm, rows, base, args):
    js = args.suffix + args.jesjer_suffix
    out = [f"## sqrt(s) = {ecm} GeV", ""]
    out.append("| Channel | Paper total (stat) | " + " | ".join(c[1] for c in COLS) + " |")
    out.append("|---|---|" + "---|" * len(COLS))
    for row in rows:
        ptot, pstat = row["paper"]
        c1, c2, c3, c4 = values(row)
        star = c4_of(row)[1]
        out.append(f"| {row['label']} | {ptot:.2f} ({pstat:.2f}) | {T.pct(c1)} | {T.pct(c2)} | {T.pct(c3)} | "
                   f"{pct_star(c4, star)} |")
    out.append("")
    out.append(f"(*) leptonic final states: no jets, the JES/JER column equals the previous one by construction "
               f"(no {js} run dir). Z(qq)H and the combination: xsec of run_2D_mrecoil_mjj_qq{js} / run_{ecm}_all{js} "
               "(JES and JER profiled on the signal and every background component of the hadronic card, in addition "
               "to the regular shape nuisances; the leptonic cards of the combination are the nominal ones).")
    out.append("")
    out.append("Quadrature decomposition (in %; c1 = stat only, c2 = stat + 1% bkg norm = the paper's total, "
               "c3 = + regular syst profiled (xsec), c4 = c3 + JES/JER; a negative argument prints '~0'):")
    out.append("")
    out.append("| Channel | 1% bkg-norm sqrt(c2^2 - c1^2) | regular syst sqrt(c3^2 - c2^2) | JES/JER sqrt(c4^2 - c3^2) "
               "| full syst sqrt(c4^2 - c1^2) |")
    out.append("|---|---|---|---|---|")
    for row in rows:
        c1, c2, c3, c4 = values(row)
        jj = T.quad(c3, c4) if row["key"] in HADRONIC else "0 (*)"
        out.append(f"| {row['label']} | {T.quad(c1, c2)} | {T.quad(c2, c3)} | {jj} | {T.quad(c1, c4)} |")
    out.append("")
    out.append("Hadronic degradation of the c3 precision (xsec, every regular nuisance profiled) by the jet nuisances, "
               "xsec(variant) / xsec(nominal) - 1 "
               "(run dirs <dir>" + args.suffix + "_jes / _jer / " + args.jesjer_suffix + "; the paper's Sec. 5.3 quotes "
               "+3.9% (JES) and +3.2% (JER) for Z(qq)H at 240 GeV, not included in its Table 2):")
    out.append("")
    out.append("| Channel | nominal c3 (xsec) | JES only: xsec (rel.) | JER only: xsec (rel.) | JES + JER: xsec (rel.) "
               "| paper Sec. 5.3 JES / JER |")
    out.append("|---|---|---|---|---|---|")
    for row in rows:
        if row["key"] not in HADRONIC:
            continue
        c3 = T.sigma_of(row, "total")
        cells = []
        for vkey, _, _ in VARIANTS:
            v = row["variants"][vkey]
            t = T.sigma_of(v, "total") if v["exists"] else None
            cells.append(f"{T.pct(t)} ({rel(t, c3)})")
        paper = PAPER_SEC53.get(ecm, {}) if row["key"] == "qq" else {}
        pcell = f"+{paper['jes']:.1f}% / +{paper['jer']:.1f}%" if paper else "not quoted"
        out.append(f"| {row['label']} | {T.pct(c3)} | " + " | ".join(cells) + f" | {pcell} |")
    out.append("")
    notes = [n for row in rows for n in consistency(row)]
    if notes:
        out.append("Consistency of the frozen scans of the JES/JER run dirs with the nominal columns (JES and JER are "
                   "frozen there too, so xsecSTAT / xsecSTATshapes must reproduce c1 / c2 to 3 decimals):")
        out.append("")
        out += [f"- {n}" for n in notes]
        out.append("")
    out += footnote(rows, base, args)
    out += T.sources(all_rows(rows), base, args.suffix, ecm)
    return out


def footnote(rows, base, args):
    out = [f"Definitions ({base}/<dir>{args.suffix}/ and <dir>{args.suffix}_jes / _jer / {args.jesjer_suffix}/; freeze "
           "lists parsed from the fit_summary.txt header fragments '(paper stat-only: ...)' = xsecSTAT and "
           "'(July run-book stat-only: ...)' = xsecSTATshapes, which the drivers run_fit_leptonic.sh / run_fit_qq.sh / "
           "run_fit_combination.sh build from the card and tee there; checked against the lnN / shape / rateParam lines "
           "of the datacard in the run dir):", ""]
    out.append("- stat only = `xsecSTAT`: `--freezeParameters=allConstrainedNuisances` - every constrained nuisance "
               "fixed, i.e. the 1% lnN background normalizations norm_* AND all shape nuisances (BES, MUSCALE / ELSCALE / "
               "JETSCALE, SQRTS; JES, JER where present); the paper-spec cards have no rateParam, so nothing but r "
               "floats = statistical only = the paper's stat-only ('obtained with the background normalization "
               "parameters fixed').")
    out.append("- stat + 1% bkg norm = `xsecSTATshapes`: `--freezeParameters=<the card's shape nuisances>` - only the "
               "shape nuisances fixed, the norm_* lnN (1%) float = the paper's quoted total (the 1% normalizations are "
               "the only nuisance parameters of the paper's fit; 'Shape uncertainties are not included as nuisance "
               "parameters in this study', Sec. 5.3).")
    out.append("- + regular syst profiled = `xsec` of the nominal run dir: nothing frozen; the card carries BES, "
               "the lepton (MUSCALE / ELSCALE) or jet (JETSCALE) momentum scale and SQRTS as shape nuisances, profiled "
               "in addition - beyond the paper's quoted precision (the paper evaluated these effects separately by "
               "repeating the fit with shifted inputs, 0.095% combined).")
    out.append("- + JES/JER = `xsec` of the JES/JER run dir: as before plus the JES "
               "(both jets scaled by 1 +- 1%, m_recoil recomputed) and JER (each jet momentum smeared by an additional "
               "1%, deterministic per-event draws; Down = bin-wise mirror of Up around the nominal) shape nuisances on "
               "the signal and every background component of the hadronic card (datacard_2d_qq_jesjer.txt); the BDT "
               "score is not recomputed under JES/JER (the JETSCALE convention); beyond the paper's quoted precision "
               "(unprofiled there, 'not included in the final quoted precision'). Leptonic rows: no jets, = the "
               "previous column (*).")
    out.append("")
    # the per-run-dir part of table2.py's footnote (nominal + variant dirs)
    fn = T.footnote(all_rows(rows), base, args.suffix)
    start = next((i for i, l in enumerate(fn) if l.startswith("Per run dir")), None)
    if start is not None:
        out += fn[start:]
    return out


def tex_table(results, args, title):
    ecms = [e for e, _ in results]
    ncol = 1 + (1 + len(COLS)) * len(ecms)
    out = [f"% {T.oneline(title)}",
           f"% generated {datetime.date.today()} by table2_full.py from {PAPER} (run-dir suffix "
           f"'{T.oneline(args.suffix)}', JES/JER dirs '{T.oneline(args.suffix + args.jesjer_suffix)}'"
           + (f", base {T.oneline(args.base)}" if args.base else "") + ")",
           "% per energy: paper = Table 2 total (stat-only); stat = xsecSTAT (all constrained nuisances frozen) =",
           "% the paper's stat-only; stat+bkg = xsecSTATshapes (shape nuisances frozen, 1% lnN normalizations float)",
           "% = the paper's quoted total; +syst = xsec of the nominal dir (BES, lepton/jet scale, sqrt(s) profiled",
           "% in addition - beyond the paper's quoted precision); +JES/JER = xsec of the JES/JER dir (jet energy",
           "% scale and resolution profiled in addition; hadronic card only, leptonic rows = +syst, marked *; not",
           "% in the paper's quoted precision either). Precision = half the 2*deltaNLL = 1 interval.",
           "% the \\providecommand lines are fallbacks for a standalone build; the paper's own macros win."]
    out += T.TEX_MACROS
    out += [r"\begin{table}[ht!]", r"\renewcommand{\arraystretch}{1.1}", r"\centering",
            (r"\caption{Relative uncertainties at the 68\% confidence level on the \ZH cross section "
             r"(in \%) from the reproduction, MVA-based configuration"
             + (f" ({T.tex_escape(args.label)})" if args.label else "")
             + r". For each center-of-mass energy: paper = published value (statistical only in parentheses); "
             r"stat = statistical only (the paper's stat-only definition); stat+bkg = statistical plus the 1\% "
             r"background-normalization uncertainties (the paper's quoted total); +syst = with, in addition, the "
             r"regular systematic uncertainties (beam energy spread, lepton or jet momentum scale, $\sqrt{s}$) "
             r"profiled; +JES/JER = with, in addition, a 1\% jet energy scale and a 1\% additional jet energy "
             r"resolution uncertainty profiled in the hadronic fit ($^*$: no jets, equal to the previous column). "
             r"The last two columns go beyond the paper's quoted precision.}"),
            r"\vspace{0.5em}", r"\label{tab:results_xsec_repro_jesjer}", "{\\footnotesize",
            r"\setlength{\tabcolsep}{3pt}",
            r"\begin{tabular}{l" + "|ccccc" * len(ecms) + "}", r"\hline",
            f" & \\multicolumn{{{ncol - 1}}}{{c}}{{$\\delta\\sigma_{{\\mathrm{{ZH}}}}/\\sigma_{{\\mathrm{{ZH}}}}$ [\\%]}} \\\\",
            r"\hline"]
    head = " "
    for i, ecm in enumerate(ecms):
        align = "c|" if i < len(ecms) - 1 else "c"
        head += f" & \\multicolumn{{{1 + len(COLS)}}}{{{align}}}{{$\\sqrt{{s}} = {ecm}$~GeV}}"
    out.append(head + r" \\")
    sub = r"\textbf{Final state}"
    for _ in ecms:
        sub += " & paper (stat) & " + " & ".join(c[2] for c in COLS)
    out += [sub + r" \\", r"\hline"]
    last_group = None
    for i, (key, _, _, group) in enumerate(T.ROWS):
        if group is not None and group != last_group:
            if i > 0:
                out.append(r"\hline")
            out.append(f"\\multicolumn{{{ncol}}}{{l}}{{\\textbf{{{group}}}}} \\\\")
            last_group = group
        elif group is None:
            out.append(r"\hline")
        line = T.TEX_ROW[key]
        for _, rows in results:
            row = next(r for r in rows if r["key"] == key)
            ptot, pstat = row["paper"]
            c1, c2, c3, c4 = values(row)
            star = c4_of(row)[1]
            line += f" & {ptot:.2f} ({pstat:.2f}) & {T.pct(c1)} & {T.pct(c2)} & {T.pct(c3)} & {T.pct(c4)}"
            if star and c4 is not None:
                line += "$^*$"
        out.append(line + r" \\")
    out += [r"\hline", r"\end{tabular}", "}", r"\end{table}"]
    out.append("% quadrature decomposition per energy (in %): 1% bkg-norm sqrt(c2^2 - c1^2), regular syst "
               "sqrt(c3^2 - c2^2), JES/JER sqrt(c4^2 - c3^2), full syst sqrt(c4^2 - c1^2)")
    for ecm, rows in results:
        for row in rows:
            c1, c2, c3, c4 = values(row)
            jj = T.quad(c3, c4) if row["key"] in HADRONIC else "0 (*)"
            out.append(f"%   {ecm} GeV {row['label']:<12} bkg-norm {T.quad(c1, c2):>6}  regular syst {T.quad(c2, c3):>6}  "
                       f"JES/JER {jj:>6}  full syst {T.quad(c1, c4):>6}")
    out.append("% hadronic degradation of the total, xsec(variant)/xsec(nominal) - 1 (paper Sec. 5.3 at 240 GeV, "
               "Z(qq)H: +3.9% JES, +3.2% JER)")
    for ecm, rows in results:
        for row in rows:
            if row["key"] not in HADRONIC:
                continue
            c3 = T.sigma_of(row, "total")
            parts = []
            for vkey, vlabel, _ in VARIANTS:
                v = row["variants"][vkey]
                t = T.sigma_of(v, "total") if v["exists"] else None
                parts.append(f"{vlabel} {T.pct(t):>6} ({rel(t, c3)})")
            out.append(f"%   {ecm} GeV {row['label']:<12} nominal {T.pct(c3):>6}  " + "  ".join(parts))
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--suffix", default="", help="run-dir suffix of the nominal fits, e.g. _oldbdt (original models)")
    ap.add_argument("--jesjer-suffix", default="_jesjer",
                    help="appended to --suffix for the JES/JER run dirs (default _jesjer -> e.g. _oldbdt_jesjer)")
    ap.add_argument("--ecm", type=int, nargs="+", choices=(240, 365), default=[240, 365])
    ap.add_argument("--out", metavar="FILE.md", help="also write the markdown to FILE.md")
    ap.add_argument("--tex", metavar="FILE.tex", help="write the table as a plain LaTeX tabular to FILE.tex")
    ap.add_argument("--label", default="", help="text prefixed to the title, e.g. 'original models'")
    ap.add_argument("--base", metavar="DIR", help="parent of the run dirs, '{ecm}' substituted (default <Paper>/S{ecm}/combine)")
    args = ap.parse_args()
    for name, val in (("--suffix", args.suffix), ("--jesjer-suffix", args.jesjer_suffix)):
        if any(ch.isspace() or ch == os.sep for ch in val):
            print(f"WARNING: {name} {val!r} contains whitespace or '/', no run dir can match", file=sys.stderr)

    ecms = sorted(set(args.ecm))
    title = f"{args.label}: {TITLE}" if args.label else TITLE
    out = [f"# {title}", ""]
    out.append(f"Generated {datetime.date.today()} by table2_full.py from {PAPER} (run-dir suffix '{args.suffix}', "
               f"JES/JER run dirs '{args.suffix + args.jesjer_suffix}'" + (f", base {args.base}" if args.base else "")
               + "). Precision = half the distance between the 2*deltaNLL = 1 crossings around the best fit "
               "(fit_precision.py logic), Asimov data, r = sigma_ZH / SM. 'Paper total (stat)' = Table 2 total "
               "(stat-only): the paper's total corresponds to the 'stat + 1% bkg norm' column (xsecSTATshapes, the "
               "1% background normalizations being the only nuisance parameters of its fit) and its stat-only to "
               "the 'stat only' column (xsecSTAT); the '+ regular syst profiled' and '+ JES/JER' columns go beyond "
               "the paper's quoted precision. A missing run dir / scan / crossing gives n/a.")
    out.append("")
    results = []
    n_cmp = n_bad = 0
    for ecm in ecms:
        rows = collect(ecm, args)
        results.append((ecm, rows))
        out += energy_section(ecm, rows, T.run_base(args, ecm), args)
        for row in all_rows(rows):
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
        print("ERROR: table2_full.py failed (see the traceback above); exit code 0 by design", file=sys.stderr)
    sys.exit(0)

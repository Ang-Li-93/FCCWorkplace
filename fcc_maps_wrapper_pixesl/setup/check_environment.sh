#!/usr/bin/env bash
#
# check_environment.sh
# --------------------
# Quick sanity check that the Key4hep environment is usable for this workflow.
# Run AFTER `source setup/setup_key4hep.sh`.
#
#   bash setup/check_environment.sh
#
# Exits non-zero (with a clear message) if a required tool is missing.

set -u

fail=0
note() { printf "  %-14s %s\n" "$1" "$2"; }

echo "=== Environment check ==="

# --- core executables -------------------------------------------------------
for tool in ddsim k4run python; do
    if command -v "$tool" >/dev/null 2>&1; then
        note "$tool" "OK  ($(command -v "$tool"))"
    else
        note "$tool" "MISSING"
        fail=1
    fi
done

# --- K4GEO ------------------------------------------------------------------
if [ -n "${K4GEO:-}" ] && [ -d "${K4GEO}/FCCee" ]; then
    note "K4GEO" "OK  (${K4GEO})"
    if [ -d "${K4GEO}/FCCee/ALLEGRO" ]; then
        note "ALLEGRO" "found"
    else
        note "ALLEGRO" "NOT found under K4GEO/FCCee"
        fail=1
    fi
else
    note "K4GEO" "MISSING or invalid (did you source setup_key4hep.sh?)"
    fail=1
fi

# --- python packages used by conversion/analysis ----------------------------
echo "--- python packages ---"
python - <<'PY'
import importlib, sys
pkgs = ["podio", "edm4hep", "ROOT", "yaml", "numpy", "pandas", "matplotlib"]
missing = []
for p in pkgs:
    try:
        importlib.import_module(p)
        print(f"  {p:<12} OK")
    except Exception as e:
        print(f"  {p:<12} MISSING ({type(e).__name__})")
        missing.append(p)
if missing:
    print()
    print("  NOTE: missing packages above. Inside the Key4hep stack these are")
    print("  normally all present. If you are in a custom venv, install with:")
    print("     pip install " + " ".join(m for m in missing if m not in ('ROOT','podio','edm4hep')))
    print("  (ROOT/podio/edm4hep come from the Key4hep stack, not pip.)")
    sys.exit(3)
PY
pyrc=$?

if [ "$fail" -ne 0 ] || [ "$pyrc" -ne 0 ]; then
    echo
    echo "RESULT: environment is NOT fully ready (see MISSING items above)." >&2
    exit 1
fi

echo
echo "RESULT: environment looks good."

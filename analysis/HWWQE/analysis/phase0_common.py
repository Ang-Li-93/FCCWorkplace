"""Shared pieces of the Phase 0 toy studies (PLAN.md Sec. 4): states, their exact
reference observables, and the per-pseudo-experiment evaluation."""
import sys
from pathlib import Path

import numpy as np

ANALYSIS_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ANALYSIS_ROOT))

from qtomo import basis, bell, config, sm, tomography  # noqa: E402

H44 = basis.COEFF_LABELS.index("h44")
H55 = basis.COEFF_LABELS.index("h55")

# Per-pseudo-experiment quantities stored by the drivers (all floats).
FIELDS = ("i3", "i3_physical", "i3_unrotated", "c2", "c2_physical", "c2_unbiased",
          "c2_unbiased_arg", "h44", "min_eigenvalue", "chi2", "ndf")


def cfg():
    return config.load("phase0")


def spectrum():
    return sm.OffShellSpectrum.from_config(config.constants())


def state(entry, const=None, spec=None):
    """Density matrix of a Phase 0 state entry (config/phase0.yaml)."""
    const = config.constants() if const is None else const
    kind = entry["kind"]
    if kind in ("sm_fixed", "decohered"):
        rho = sm.density_matrix(sm.kappa(const["m_H"], const["m_W"], entry["mstar"]))
        return rho if kind == "sm_fixed" else sm.decohered(rho)
    if kind == "sm_spectrum":
        spec = spectrum() if spec is None else spec
        return spec.average_density_matrix(entry.get("mstar_range", (0.0, np.inf)))[0]
    if kind == "isotropic":
        return basis.ID9 / 9
    raise ValueError(f"unknown state kind {kind!r}")


def reference(rho, n_starts):
    """Exact observables of a state: coefficients, I3 (with its optimal settings), C2, h44."""
    i3 = bell.i3_optimise(rho, n_starts=n_starts, full_output=True)
    return {"c": basis.coefficient_vector(rho), "i3": i3.value, "i3_result": i3,
            "c2": float(bell.c2(rho)), "h44": float(basis.coefficient_vector(rho)[H44])}


def evaluate(res, ref, n_starts, rng, with_i3=True):
    """Observables of one pseudo-experiment (a tomography.Result): I3 and C2 raw and after
    projection on the nearest physical state, unbiased C2, h44 and the chi^2 of the 80
    coefficients against the truth with the estimated covariance."""
    from qtomo import stats
    out = dict.fromkeys(FIELDS, np.nan)
    if with_i3:
        obs = bell.observables(res.rho, n_starts=n_starts, rng=rng, x0=ref["i3_result"])
        out.update(i3=obs["i3"], i3_physical=obs["i3_physical"], c2=obs["c2"],
                   c2_physical=obs["c2_physical"])
    arg = max(res.invariants.c2_arg_wplus, res.invariants.c2_arg_wminus)
    out.update(i3_unrotated=float(np.real(np.trace(res.rho @ bell.B_CGLMP))),
               c2_unbiased=2.0 * max(0.0, arg), c2_unbiased_arg=2.0 * arg,
               h44=float(res.c[H44]), min_eigenvalue=float(res.min_eigenvalue))
    chi2, ndf, _ = stats.chi_square(res.c - ref["c"], res.cov)
    out.update(chi2=chi2, ndf=float(ndf))
    return out


def seed_sequence(*keys):
    return np.random.SeedSequence([int(cfg()["seed"])] + [int(k) for k in keys])

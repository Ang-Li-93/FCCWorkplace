"""Analytic tree-level SM spin state of H -> W+ W-* (PLAN.md Sec. 3.4) and the
off-shell W mass spectrum used to average it.

    |Psi_H> = (|+-> - kappa |00> + |-+>) / sqrt(2 + kappa^2),
    kappa   = (m_H^2 - M1^2 - M2^2) / (2 M1 M2)          (2302.00683 Eqs. 3.12-3.13)

in the common-axis basis of ``basis`` (both spins quantised along k = W+ direction
in the H rest frame).  kappa >= 1, with kappa = 1 at threshold (M1 + M2 = m_H,
maximally entangled) and kappa -> infinity for M* -> 0 (state -> |00>).
"""
import numpy as np

from . import basis

I_PM, I_00, I_MP = 2, 4, 6      # flat indices of |+1,-1>, |0,0>, |-1,+1>
SQRT3 = basis.SQRT3


def kappa(m_H, M1, M2):
    """kappa = (m_H^2 - M1^2 - M2^2) / (2 M1 M2); symmetric in M1, M2."""
    M1 = np.asarray(M1, dtype=float)
    M2 = np.asarray(M2, dtype=float)
    return (m_H ** 2 - M1 ** 2 - M2 ** 2) / (2 * M1 * M2)


def state(kappa):
    """|Psi_H> as a flat 9-vector (or stack of them)."""
    k = np.asarray(kappa, dtype=float)
    norm = np.sqrt(2 + k ** 2)
    psi = np.zeros(k.shape + (9,), dtype=complex)
    psi[..., I_PM] = 1 / norm
    psi[..., I_00] = -k / norm
    psi[..., I_MP] = 1 / norm
    return psi


def density_matrix(kappa):
    psi = state(kappa)
    return np.einsum("...i,...j->...ij", psi, psi.conj())


def coefficients(kappa):
    """(f, g, h) of |Psi_H><Psi_H| in closed form.  Non-zero entries:
    f3 = g3 = (1 - k^2)/(6 d), f8 = g8 = -f3/sqrt3, h16 = h61 = h27 = h72 = -k/(2 d),
    h33 = k^2/(4 d), h38 = h83 = -1/(4 sqrt3), h44 = h55 = 1/(2 d),
    h88 = (k^2 - 4)/(12 d), with d = 2 + k^2."""
    k = np.asarray(kappa, dtype=float)
    d = 2 + k ** 2
    f = np.zeros(k.shape + (8,))
    h = np.zeros(k.shape + (8, 8))
    f[..., 2] = (1 - k ** 2) / (6 * d)
    f[..., 7] = -f[..., 2] / SQRT3
    for a, b in ((0, 5), (5, 0), (1, 6), (6, 1)):
        h[..., a, b] = -k / (2 * d)
    h[..., 2, 2] = k ** 2 / (4 * d)
    h[..., 2, 7] = h[..., 7, 2] = -1 / (4 * SQRT3)
    h[..., 3, 3] = h[..., 4, 4] = 1 / (2 * d)
    h[..., 7, 7] = (k ** 2 - 4) / (12 * d)
    return f, f.copy(), h


def coefficients_paper(m_H, M_V, f):
    """Eqs. (3.5)-(3.6) of 2302.00683, transcribed verbatim: M_V is the on-shell
    mass and f = M_V*/M_V the ratio of the off-shell to the on-shell mass."""
    m_H, M_V, f = (np.asarray(x, dtype=float) for x in (m_H, M_V, f))
    m2, M2, f2 = m_H ** 2, M_V ** 2, f ** 2
    den = m2 ** 2 - 2 * (1 + f2) * m2 * M2 + (1 + 10 * f2 + f2 ** 2) * M2 ** 2
    shape = np.broadcast(m_H, M_V, f).shape
    fa = np.zeros(shape + (8,))
    h = np.zeros(shape + (8, 8))
    fa[..., 2] = (-m2 ** 2 + 2 * (1 + f2) * m2 * M2 - (1 - f2) ** 2 * M2 ** 2) / (6 * den)
    fa[..., 7] = -fa[..., 2] / SQRT3
    h16 = f * M2 * (-m2 + (1 + f2) * M2) / den
    for a, b in ((0, 5), (5, 0), (1, 6), (6, 1)):
        h[..., a, b] = h16
    h[..., 2, 2] = 0.25 * (m2 - (1 + f2) * M2) ** 2 / den
    h[..., 2, 7] = h[..., 7, 2] = -1 / (4 * SQRT3)
    h[..., 3, 3] = h[..., 4, 4] = 2 * f2 * M2 ** 2 / den
    h[..., 7, 7] = (m2 ** 2 - 2 * (1 + f2) * m2 * M2 + (1 - 14 * f2 + f2 ** 2) * M2 ** 2) / (12 * den)
    return fa, fa.copy(), h


def decohered(rho):
    """rho with all coherences removed in the |m+ m-> basis (diagonal part).
    A diagonal state is a mixture of product states, hence separable."""
    rho = np.asarray(rho)
    return np.einsum("...ii,ij->...ij", rho, np.eye(rho.shape[-1]))


# --------------------------------------------------------------------------
# Off-shell W mass spectrum
# --------------------------------------------------------------------------
def kallen(a, b, c):
    return a * a + b * b + c * c - 2 * (a * b + a * c + b * c)


def offshell_density(M1, M2, m_H, m_W, Gamma_W):
    """Unnormalised d^2Gamma/(dM1 dM2) for H -> W(M1) W(M2) -> 4 massless fermions,
    tree level, constant-width Breit-Wigner propagators:

        4 M1 M2 lambda^{1/2} [lambda + 12 M1^2 M2^2] / (BW(M1^2) BW(M2^2)),
        lambda = lambda(m_H^2, M1^2, M2^2), BW(q^2) = (q^2 - m_W^2)^2 + m_W^2 Gamma_W^2,

    for M1 + M2 < m_H and zero otherwise.  lambda + 12 M1^2 M2^2 = 4 M1^2 M2^2 (2 + kappa^2)
    is the helicity sum of the amplitude that gives |Psi_H> (CONVENTIONS.md;
    cf. A. Djouadi, Phys. Rept. 457 (2008) 1, H -> V* V*).
    """
    M1 = np.asarray(M1, dtype=float)
    M2 = np.asarray(M2, dtype=float)
    x1, x2 = M1 ** 2, M2 ** 2
    lam = kallen(m_H ** 2, x1, x2)
    ok = (M1 > 0) & (M2 > 0) & (M1 + M2 < m_H) & (lam > 0)
    lam = np.where(ok, lam, 0.0)
    bw = ((x1 - m_W ** 2) ** 2 + (m_W * Gamma_W) ** 2) * ((x2 - m_W ** 2) ** 2 + (m_W * Gamma_W) ** 2)
    return np.where(ok, 4 * M1 * M2 * np.sqrt(lam) * (lam + 12 * x1 * x2) / bw, 0.0)


class OffShellSpectrum:
    """(M1, M2) spectrum of H -> W W*, see ``offshell_density``.

    Internally the heavier W mass is mapped to u = arctan((M^2 - m_W^2)/(m_W Gamma_W)),
    which flattens its Breit-Wigner, and the lighter one to y = M^2; in (u, y) the density
    lambda^{1/2} [lambda + 12 x1 x2] / BW(y) is smooth and bounded by m_H^6 / BW_min(y).
    """

    def __init__(self, m_H, m_W, Gamma_W, mstar_min):
        self.m_H, self.m_W, self.Gamma_W, self.mstar_min = m_H, m_W, Gamma_W, mstar_min
        self._a = m_W * Gamma_W
        self.u_lo = np.arctan((mstar_min ** 2 - m_W ** 2) / self._a)
        self.u_hi = np.arctan(((m_H - mstar_min) ** 2 - m_W ** 2) / self._a)
        self.y_lo, self.y_hi = mstar_min ** 2, (m_H / 2) ** 2
        y_peak = min(self.y_hi, m_W ** 2)
        self._bound = m_H ** 6 / ((y_peak - m_W ** 2) ** 2 + self._a ** 2)

    @classmethod
    def from_config(cls, const):
        return cls(const["m_H"], const["m_W"], const["Gamma_W"], const["mstar_min"])

    def _heavy_mass(self, u):
        return np.sqrt(self.m_W ** 2 + self._a * np.tan(u))

    def _weight(self, u, y):
        """Density in (u, y) up to a constant; zero outside M_light < M_heavy, sum < m_H."""
        mh = self._heavy_mass(u)
        ml = np.sqrt(y)
        lam = kallen(self.m_H ** 2, mh ** 2, y)
        ok = (ml < mh) & (ml + mh < self.m_H) & (lam > 0)
        lam = np.where(ok, lam, 0.0)
        val = np.sqrt(lam) * (lam + 12 * mh ** 2 * y) / ((y - self.m_W ** 2) ** 2 + self._a ** 2)
        return np.where(ok, val, 0.0)

    def sample(self, n, rng, chunk=200000):
        """Exact accept-reject sample of n (M_W+, M_W-) pairs."""
        out_h, out_l = [], []
        have = 0
        while have < n:
            u = rng.uniform(self.u_lo, self.u_hi, chunk)
            y = rng.uniform(self.y_lo, self.y_hi, chunk)
            w = self._weight(u, y)
            if np.any(w > self._bound):
                raise RuntimeError("OffShellSpectrum: accept-reject bound violated")
            keep = rng.uniform(0.0, self._bound, chunk) < w
            out_h.append(self._heavy_mass(u[keep]))
            out_l.append(np.sqrt(y[keep]))
            have += int(keep.sum())
        mh = np.concatenate(out_h)[:n]
        ml = np.concatenate(out_l)[:n]
        wplus_heavy = rng.uniform(size=n) < 0.5
        return np.where(wplus_heavy, mh, ml), np.where(wplus_heavy, ml, mh)

    def grid(self, n_u=2000, n_y=400):
        """Midpoint grid: heavy masses, light masses and normalised weights (flat arrays)."""
        u = self.u_lo + (np.arange(n_u) + 0.5) * (self.u_hi - self.u_lo) / n_u
        y = self.y_lo + (np.arange(n_y) + 0.5) * (self.y_hi - self.y_lo) / n_y
        uu, yy = np.meshgrid(u, y, indexing="ij")
        w = self._weight(uu, yy).ravel()
        return self._heavy_mass(uu).ravel(), np.sqrt(yy).ravel(), w / w.sum()

    def average_density_matrix(self, mstar_range=(0.0, np.inf), n_u=2000, n_y=400):
        """SM spin state averaged over the spectrum, optionally for M* = min(M1, M2)
        inside ``mstar_range``.  Returns (rho_bar, accepted fraction)."""
        mh, ml, w = self.grid(n_u, n_y)
        sel = (ml >= mstar_range[0]) & (ml < mstar_range[1])
        frac = w[sel].sum()
        k = kappa(self.m_H, mh[sel], ml[sel])
        d = 2 + k ** 2
        a = np.sum(w[sel] / d) / frac          # <1/(2+k^2)>
        b = np.sum(w[sel] * k / d) / frac      # <k/(2+k^2)>
        c = np.sum(w[sel] * k ** 2 / d) / frac  # <k^2/(2+k^2)>
        rho = np.zeros((9, 9))
        for i in (I_PM, I_MP):
            for j in (I_PM, I_MP):
                rho[i, j] = a
            rho[i, I_00] = rho[I_00, i] = -b
        rho[I_00, I_00] = c
        return rho.astype(complex), frac

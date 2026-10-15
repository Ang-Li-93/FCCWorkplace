"""Common plot style (PLAN.md rule 8): matplotlib, PDF + PNG, axis labels with
units, and the study label from config/plotting.yaml."""
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

from . import config  # noqa: E402

_CFG = None


def _cfg():
    global _CFG
    if _CFG is None:
        _CFG = config.load("plotting")
    return _CFG


def label(kind="toy"):
    """'toy' for detector-free toy studies, 'mc' for Delphes IDEA samples."""
    return _cfg()["label_toy" if kind == "toy" else "label_mc"]


def add_label(ax, kind="toy", x=0.02, y=0.98, title=False, **kwargs):
    """Study label inside the axes at (x, y), or as a left-aligned title (``title=True``)."""
    if title:
        ax.set_title(label(kind), fontsize=8, loc="left")
        return
    ax.text(x, y, label(kind), transform=ax.transAxes, ha="left", va="top",
            fontsize=8, **kwargs)


def save(fig, stem):
    """Write ``<stem>.pdf`` and ``<stem>.png``; ``stem`` is relative to the analysis root."""
    stem = config.resolve(stem)
    stem.parent.mkdir(parents=True, exist_ok=True)
    for ext in _cfg()["formats"]:
        fig.savefig(Path(f"{stem}.{ext}"), dpi=_cfg()["dpi"], bbox_inches="tight")
    plt.close(fig)

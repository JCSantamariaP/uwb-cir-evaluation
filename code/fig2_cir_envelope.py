"""
fig2_cir_envelope.py — Overlaid average CIR envelopes (Fig. 2)
=================================================================
Reads cir_dataset.csv and plots, in a single figure, the average CIR
envelope (aligned to the first path) for the 4 groups:
  {DW1000, DW3000} x {Lab, Corridor}

This reproduces Fig. 2 in the paper (Section III-B).

Notes on methodology, to keep this reproduction exact:
  1. The integrity filter (is_valid, is_full_length, non-null metrics)
     used throughout the paper's text is applied here too, so that the
     legend's n values match the reported "valid measurements":
     3,680 / 1,403 / 3,506 / 3,192.
  2. Alignment uses int() (truncation), not round(), to be exactly
     consistent with the fp_bins convention used in
     build_cir_dataset.py when computing mean_excess_delay_ns and
     rms_delay_spread_ns.
"""

import json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

sns.set_theme(style="whitegrid", context="paper")
plt.rcParams.update({
    "font.family": "serif",
    "font.size": 9,
    "axes.labelsize": 9,
    "axes.labelweight": "bold",
    "xtick.labelsize": 8,
    "ytick.labelsize": 8,
    "legend.fontsize": 7.5,
    "legend.frameon": True,
    "legend.edgecolor": "0.3",
    "figure.dpi": 300,
    "axes.edgecolor": "0.3",
    "grid.linewidth": 0.5,
    "grid.alpha": 0.4,
})

FS = 499.2e6
TS_NS = (1.0 / FS) * 1e9
WINDOW_PRE = 10
WINDOW_POST = 100
OUT = Path(".")

PALETTE = sns.color_palette("deep", 2)
COLORS = {"dw1000": PALETTE[0], "dw3000": PALETTE[1]}
LABELS = {"dw1000": "DW1000", "dw3000": "DW3000"}
LSTYLES = {"lab": "-", "corridor": "--"}


def align_envelope(amplitude, fp_ind):
    """Crops and aligns an already-computed envelope to a fixed window
    centered on the first path.

    Uses int() (truncation), matching build_cir_dataset.py:
        fp_bins = fp_ind / 64.0
        start = max(0, int(fp_bins) - WINDOW_PRE_BINS)
    so that the alignment point is identical to the one used when
    computing the paper's official metrics.
    """
    fp_bins = int(fp_ind / 64.0)   # truncation, not round()
    start = fp_bins - WINDOW_PRE
    end = fp_bins + WINDOW_POST
    total_len = WINDOW_PRE + WINDOW_POST
    window = np.full(total_len, np.nan)
    src_start = max(0, start)
    src_end = min(len(amplitude), end)
    dst_start = src_start - start
    dst_end = dst_start + (src_end - src_start)
    if src_end > src_start:
        window[dst_start:dst_end] = amplitude[src_start:src_end]
    return window


def compute_average_envelope(sub_df):
    """Returns (normalized_average, n) from a sub-dataframe."""
    envelopes = []
    for _, row in sub_df.iterrows():
        try:
            amplitude = json.loads(row["cir_amplitude"])
        except (json.JSONDecodeError, TypeError):
            continue
        env = align_envelope(amplitude, row["fp_ind"])
        envelopes.append(env)

    n = len(envelopes)
    if n == 0:
        return None, 0
    average = np.nanmean(np.vstack(envelopes), axis=0)
    average_norm = average / np.nanmax(average)
    return average_norm, n


print("Loading cir_dataset.csv (selected columns only)...")
df = pd.read_csv(
    "cir_dataset.csv",
    usecols=["chipset", "carpeta", "fp_ind", "cir_amplitude", "anc_medicion",
             "is_valid", "is_full_length",
             "mean_excess_delay_ns", "rms_delay_spread_ns"],
)

# ── Integrity filter (identical to the one used for the paper's text) ──
val = df[
    df["carpeta"].isin(["lab", "corridor"]) &
    df["cir_amplitude"].notna() &
    (df["is_valid"] == True) &
    (df["is_full_length"] == True) &
    df["mean_excess_delay_ns"].notna() &
    df["rms_delay_spread_ns"].notna()
].copy()

t_axis_ns = np.arange(-WINDOW_PRE, WINDOW_POST) * TS_NS

fig, ax = plt.subplots(figsize=(5.0, 3.6))

stats_lines = []
def log(msg):
    print(msg)
    stats_lines.append(msg)

groups = [("dw1000","lab"), ("dw1000","corridor"),
          ("dw3000","lab"), ("dw3000","corridor")]

for chip, scen in groups:
    sub = val[(val["chipset"] == chip) & (val["carpeta"] == scen)]
    average_norm, n = compute_average_envelope(sub)

    if average_norm is None:
        log(f"  {LABELS[chip]} - {scen}: no data")
        continue

    ax.plot(t_axis_ns, average_norm,
            color=COLORS[chip], linestyle=LSTYLES[scen],
            linewidth=2.0, zorder=3,
            label=f"{LABELS[chip]} - {scen.capitalize()} (n={n})")

    log(f"  {LABELS[chip]:8s} - {scen:10s} | n={n:5d} | "
        f"peak_bin={np.nanargmax(average_norm)}  "
        f"energy_after_50ns={np.nansum(average_norm[t_axis_ns>50]):.2f}")

ax.axvline(0, color="0.4", linewidth=0.8, linestyle=":", zorder=1)
ax.set_xlabel("Time relative to First Path (ns)")
ax.set_ylabel("Normalized CIR Amplitude")
ax.legend(loc="upper right")
ax.set_xlim(-10, 100)
sns.despine(ax=ax, left=False, bottom=False)

fig.tight_layout()
fig.savefig(OUT / "fig_envolventes_superpuestas.pdf", bbox_inches="tight")
fig.savefig(OUT / "fig_envolventes_superpuestas.png", bbox_inches="tight")
plt.close(fig)
print("\n[OK] fig_envolventes_superpuestas.pdf generated")
print("Verify that n matches:")
print("  DW1000-Lab=3680, DW1000-Corridor=1403, DW3000-Lab~3506, DW3000-Corridor~3192")

with open(OUT / "stats_envolventes.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(stats_lines))
print("[OK] stats_envolventes.txt saved")

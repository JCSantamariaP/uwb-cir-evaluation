"""fig2_cir_envelope.py — Fig. 2 of the paper (Section III-B)"""

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
OUT = Path("fig")
OUT.mkdir(exist_ok=True)

PALETTE = sns.color_palette("deep", 2)
COLORS = {"dw1000": PALETTE[0], "dw3000": PALETTE[1]}
LABELS = {"dw1000": "DW1000", "dw3000": "DW3000"}
LSTYLES = {"lab": "-", "corridor": "--"}


def align_envelope(amplitude, fp_ind):
    # truncation (int()), matching build_cir_dataset.py's fp_bins convention
    fp_bins = int(fp_ind / 64.0)
    start = fp_bins - WINDOW_PRE
    end = fp_bins + WINDOW_POST
    window = np.full(WINDOW_PRE + WINDOW_POST, np.nan)
    src_start = max(0, start)
    src_end = min(len(amplitude), end)
    dst_start = src_start - start
    dst_end = dst_start + (src_end - src_start)
    if src_end > src_start:
        window[dst_start:dst_end] = amplitude[src_start:src_end]
    return window


def compute_average_envelope(sub_df):
    envelopes = []
    for _, row in sub_df.iterrows():
        try:
            amplitude = json.loads(row["cir_amplitude"])
        except (json.JSONDecodeError, TypeError):
            continue
        envelopes.append(align_envelope(amplitude, row["fp_ind"]))

    if not envelopes:
        return None, 0
    average = np.nanmean(np.vstack(envelopes), axis=0)
    return average / np.nanmax(average), len(envelopes)


df = pd.read_csv("cir_dataset.csv", usecols=[
    "chipset", "carpeta", "fp_ind", "cir_amplitude",
    "is_valid", "is_full_length",
    "mean_excess_delay_ns", "rms_delay_spread_ns",
])

val = df[
    df["carpeta"].isin(["lab", "corridor"]) &
    df["cir_amplitude"].notna() &
    (df["is_valid"] == True) &
    (df["is_full_length"] == True) &
    df["mean_excess_delay_ns"].notna() &
    df["rms_delay_spread_ns"].notna()
]

t_axis_ns = np.arange(-WINDOW_PRE, WINDOW_POST) * TS_NS
fig, ax = plt.subplots(figsize=(5.0, 3.6))

groups = [("dw1000", "lab"), ("dw1000", "corridor"),
          ("dw3000", "lab"), ("dw3000", "corridor")]

for chip, scen in groups:
    sub = val[(val["chipset"] == chip) & (val["carpeta"] == scen)]
    average_norm, n = compute_average_envelope(sub)
    if average_norm is None:
        continue
    ax.plot(t_axis_ns, average_norm,
            color=COLORS[chip], linestyle=LSTYLES[scen],
            linewidth=2.0, zorder=3,
            label=f"{LABELS[chip]} - {scen.capitalize()} (n={n})")

ax.axvline(0, color="0.4", linewidth=0.8, linestyle=":", zorder=1)
ax.set_xlabel("Time relative to First Path (ns)")
ax.set_ylabel("Normalized CIR Amplitude")
ax.legend(loc="upper right")
ax.set_xlim(-10, 100)
sns.despine(ax=ax)
fig.tight_layout()
fig.savefig(OUT / "fig2_cir_envelope.pdf", bbox_inches="tight")
plt.close(fig)
print("fig/fig2_cir_envelope.pdf")
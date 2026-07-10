"""fig1_power_energy_vs_distance.py — Fig. 1 of the paper (Section III-A)"""

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

sns.set_theme(style="whitegrid", context="paper")
plt.rcParams.update({
    "font.family": "serif",
    "font.size": 9,
    "axes.titlesize": 9,
    "axes.titleweight": "bold",
    "axes.labelsize": 9,
    "axes.labelweight": "bold",
    "xtick.labelsize": 8,
    "ytick.labelsize": 8,
    "legend.fontsize": 8,
    "legend.frameon": True,
    "legend.edgecolor": "0.3",
    "figure.dpi": 300,
    "axes.edgecolor": "0.3",
    "grid.linewidth": 0.5,
    "grid.alpha": 0.4,
})

PALETTE = sns.color_palette("deep", 2)
COLORS = {"dw1000": PALETTE[0], "dw3000": PALETTE[1]}
LABELS = {"dw1000": "DW1000", "dw3000": "DW3000"}
OUT = Path("fig")
OUT.mkdir(exist_ok=True)

df = pd.read_csv("cir_dataset.csv", usecols=[
    "chipset", "carpeta", "dist_real_m", "fp_pwr_dBm",
    "energy_ratio_fp", "is_valid", "is_full_length",
])

val = df[
    (df["carpeta"] == "calibration_anc0") &  # single-anchor calibration at 0.5-5 m
    (df["is_valid"] == True) &
    (df["is_full_length"] == True)
]
distances = sorted(val["dist_real_m"].dropna().unique())

metrics = [
    ("fp_pwr_dBm", "First-Path Power (dBm)", "fig1a_fppwr_vs_dist"),
    ("energy_ratio_fp", "Energy Ratio (FP/Total)", "fig1b_energyratio_vs_dist"),
]

for col, label, fname in metrics:
    fig, ax = plt.subplots(figsize=(5.0, 3.6))

    for chip in ["dw1000", "dw3000"]:
        sub_chip = val[val["chipset"] == chip]
        medians, p10s, p90s = [], [], []
        for d in distances:
            sub = sub_chip[sub_chip["dist_real_m"] == d][col].dropna()
            medians.append(sub.median() if len(sub) else np.nan)
            p10s.append(sub.quantile(0.10) if len(sub) else np.nan)
            p90s.append(sub.quantile(0.90) if len(sub) else np.nan)

        ax.plot(distances, medians, marker="o", color=COLORS[chip],
                label=LABELS[chip], linewidth=2.0, markersize=6,
                markeredgecolor="white", markeredgewidth=0.6, zorder=3)
        ax.fill_between(distances, p10s, p90s, color=COLORS[chip],
                         alpha=0.18, zorder=1, linewidth=0)  # 10th-90th percentile band

    ax.set_xlabel("True Distance (m)")
    ax.set_ylabel(label)
    ax.legend(loc="best")
    sns.despine(ax=ax)
    fig.tight_layout()
    fig.savefig(OUT / f"{fname}.pdf", bbox_inches="tight")
    plt.close(fig)
    print(f"fig/{fname}.pdf")
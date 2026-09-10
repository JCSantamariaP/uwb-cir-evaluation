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
    "font.size": 14,
    "axes.titlesize": 16,
    "axes.titleweight": "bold",
    "axes.labelsize": 14,
    "axes.labelweight": "bold",
    "xtick.labelsize": 12,
    "ytick.labelsize": 12,
    "legend.fontsize": 12,
    "legend.frameon": True,
    "legend.edgecolor": "0.3",
    "figure.dpi": 300,
    "axes.edgecolor": "0.3",
    "grid.linewidth": 0.5,
    "grid.alpha": 0.4,
    "pdf.fonttype": 42,
    "ps.fonttype": 42
})

PALETTE = sns.color_palette("deep", 2)
COLORS = {"dw1000": PALETTE[0], "dw3000": PALETTE[1]}
LABELS = {"dw1000": "DW1000", "dw3000": "DW3000"}
OUT = Path("fig")
OUT.mkdir(exist_ok=True)

df = pd.read_csv("cir_dataset.csv", usecols=[
    "chipset", "carpeta", "dist_real_m", "fp_pwr_dBm",
    "energy_ratio_fp", "temp", "is_valid", "is_full_length",
])

val = df[
    (df["carpeta"] == "calibration_anc0") &
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

        if col == "energy_ratio_fp":
            print(f"\n  {LABELS[chip]} Energy Ratio medians:")
            for d, m in zip(distances, medians):
                print(f"    {d} m: median={m:.3f}")

        ax.plot(distances, medians, marker="o", color=COLORS[chip],
                label=LABELS[chip], linewidth=2.0, markersize=6,
                markeredgecolor="white", markeredgewidth=0.6, zorder=3)
        ax.fill_between(distances, p10s, p90s, color=COLORS[chip],
                         alpha=0.18, zorder=1, linewidth=0)

    ax.set_xlabel("True Distance (m)")
    ax.set_ylabel(label)
    ax.legend(loc="best")
    sns.despine(ax=ax)
    fig.tight_layout()
    fig.savefig(OUT / f"{fname}.pdf", bbox_inches="tight")
    plt.close(fig)
    print(f"fig/{fname}.pdf")

# --- Diagnostic: temperature by distance (rules out thermal drift as cause of the DW3000 pattern) ---
print("\nTemperature (°C) by distance and chipset — calibration_anc0")
print(f"{'Dist (m)':>10} | {'DW1000':>10} | {'DW3000':>10}")
for d in distances:
    row = f"{d:>10.1f} |"
    for chip in ["dw1000", "dw3000"]:
        sub = val[(val["chipset"] == chip) & (val["dist_real_m"] == d)]["temp"].dropna()
        med = sub.median() if len(sub) else float("nan")
        row += f" {med:>10.2f} |"
    print(row)
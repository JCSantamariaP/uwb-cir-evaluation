"""
fig1_power_energy_vs_distance.py — First-path power & Energy Ratio vs. distance
=================================================================================
Reads cir_dataset.csv and generates the two panels of Fig. 1 in the paper
(Section III-A): First-Path Power and Energy Ratio (FP/Total) as a function
of true (ground-truth) distance, for DW1000 vs. DW3000.

Uses only true distance (ground truth), never measured/ranging distance.
Does not depend on ranging or ToF.
"""

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

# ── Seaborn style + IEEE column formatting ─────────────────────────
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

# Seaborn "deep" palette, trimmed to 2 colors with good IEEE contrast
PALETTE = sns.color_palette("deep", 2)
COLORS = {"dw1000": PALETTE[0], "dw3000": PALETTE[1]}
LABELS = {"dw1000": "DW1000", "dw3000": "DW3000"}
OUT = Path(".")

print("Loading cir_dataset.csv...")
df = pd.read_csv(
    "cir_dataset.csv",
    usecols=["chipset", "carpeta", "dist_real_m",
             "fp_pwr_dBm", "energy_ratio_fp",
             "is_valid", "is_full_length"],
)

val = df[
    (df["carpeta"] == "calibration_anc0") &
    (df["is_valid"] == True) &
    (df["is_full_length"] == True)
].copy()
distances = sorted(val["dist_real_m"].dropna().unique())
print(f"Distances evaluated: {distances}")

metrics = [
    ("fp_pwr_dBm",      "First-Path Power (dBm)",  "fig_fppwr_vs_dist"),
    ("energy_ratio_fp", "Energy Ratio (FP/Total)", "fig_energyratio_vs_dist"),
]

stats_lines = []
def log(msg):
    print(msg)
    stats_lines.append(msg)

for col, label, fname in metrics:
    log(f"\n[{label}]")
    fig, ax = plt.subplots(figsize=(5.0, 3.6))

    for chip in ["dw1000", "dw3000"]:
        sub_chip = val[val["chipset"] == chip]
        medians, p10s, p90s = [], [], []
        for d in distances:
            sub = sub_chip[sub_chip["dist_real_m"] == d][col].dropna()
            if len(sub) > 0:
                medians.append(sub.median())
                p10s.append(sub.quantile(0.10))
                p90s.append(sub.quantile(0.90))
                log(f"  {LABELS[chip]:8s} | d={d:.1f}m | "
                    f"median={sub.median():.3f}  n={len(sub)}")
            else:
                medians.append(np.nan)
                p10s.append(np.nan)
                p90s.append(np.nan)

        ax.plot(distances, medians, marker="o", color=COLORS[chip],
                label=LABELS[chip], linewidth=2.0, markersize=6,
                markeredgecolor="white", markeredgewidth=0.6,
                zorder=3)
        ax.fill_between(distances, p10s, p90s, color=COLORS[chip],
                         alpha=0.18, zorder=1, linewidth=0)

    ax.set_xlabel("True Distance (m)")
    ax.set_ylabel(label)
    ax.legend(loc="best")
    sns.despine(ax=ax, left=False, bottom=False)
    fig.tight_layout()
    fig.savefig(OUT / f"{fname}.pdf", bbox_inches="tight")
    fig.savefig(OUT / f"{fname}.png", bbox_inches="tight")
    plt.close(fig)
    print(f"  [OK] {fname}.pdf")

with open(OUT / "stats_vs_dist.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(stats_lines))
print("\n[OK] stats_vs_dist.txt saved")
print("[OK] 2 figures generated")

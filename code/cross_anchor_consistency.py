"""cross_anchor_consistency.py — Cross-anchor consistency (Section III-A)"""

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
    "chipset", "carpeta", "ancla_id", "dist_real_m", "fp_pwr_dBm",
    "energy_ratio_fp", "mean_excess_delay_ns", "rms_delay_spread_ns",
    "temp", "is_valid", "is_full_length",
])
df = df[(df["is_valid"] == True) & (df["is_full_length"] == True)]
df = df[~df["carpeta"].str.contains("antiguas", case=False, na=False)]

# anchor 0 measured separately (calibration_anc0) at several distances; keep only 2 m
anc0_2m = df[(df["carpeta"] == "calibration_anc0") & (df["dist_real_m"] == 2.0)]
anchors_df = pd.concat([anc0_2m, df[df["carpeta"] == "calibration_anchors"]])

metrics = [
    ("fp_pwr_dBm", "First-Path Power (dBm)"),
    ("energy_ratio_fp", "Energy Ratio (FP/Total)"),
    ("mean_excess_delay_ns", "Mean Excess Delay (ns)"),
    ("rms_delay_spread_ns", "RMS Delay Spread (ns)"),
]

fig, axes = plt.subplots(2, 2, figsize=(8, 6))
for ax, (col, label) in zip(axes.flatten(), metrics):
    data, tick_labels, colors = [], [], []
    medians_by_chip = {"dw1000": [], "dw3000": []}
    for chip in ["dw1000", "dw3000"]:
        for anc in sorted(anchors_df["ancla_id"].dropna().unique()):
            sub = anchors_df[(anchors_df["chipset"] == chip) & (anchors_df["ancla_id"] == anc)][col].dropna()
            if len(sub) == 0:
                continue
            data.append(sub)
            tick_labels.append(f"{LABELS[chip]}\nA{int(anc)}")
            colors.append(COLORS[chip])
            medians_by_chip[chip].append(sub.median())

    for chip in ["dw1000", "dw3000"]:
        vals = medians_by_chip[chip]
        if len(vals) >= 2:
            print(f"[{label}] cross-anchor range ({LABELS[chip]}): {max(vals)-min(vals):.3f}")

    bp = ax.boxplot(data, tick_labels=tick_labels, patch_artist=True, showfliers=False,
                     medianprops=dict(color="black", linewidth=1.5))
    for patch, color in zip(bp["boxes"], colors):
        patch.set_facecolor(color)
        patch.set_alpha(0.7)
    ax.set_title(label, fontweight="bold", fontsize=8.5)
    ax.tick_params(axis="x", labelsize=6.5)
    sns.despine(ax=ax)

fig.suptitle("Cross-Anchor Consistency at Fixed 2 m Distance", fontweight="bold")
fig.tight_layout()
fig.savefig(OUT / "fig_cross_anchor_consistency.pdf", bbox_inches="tight")
plt.close(fig)
print("fig/fig_cross_anchor_consistency.pdf")

print("\nChip temperature by anchor:")
for chip in ["dw1000", "dw3000"]:
    anc0_chip = anc0_2m[anc0_2m["chipset"] == chip]
    print(f"  {LABELS[chip]} Anchor 0: temp median={anc0_chip['temp'].median():.2f}")
    others_chip = df[(df["carpeta"] == "calibration_anchors") & (df["chipset"] == chip)]
    for anc in sorted(others_chip["ancla_id"].dropna().unique()):
        sub = others_chip[others_chip["ancla_id"] == anc]
        print(f"  {LABELS[chip]} Anchor {int(anc)}: temp median={sub['temp'].median():.2f}")
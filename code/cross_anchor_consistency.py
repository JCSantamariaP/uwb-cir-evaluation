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
    "font.size": 14,
    "axes.titlesize": 14,
    "axes.titleweight": "bold",
    "axes.labelsize": 14,
    "axes.labelweight": "bold",
    "xtick.labelsize": 10,
    "ytick.labelsize": 12,
    "legend.fontsize": 12,
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

# === LOAD DATA ===

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

# === PLOT ===

# anchor_id as an int column, needed for seaborn's x-axis grouping
anchors_df = anchors_df.copy()
anchors_df["anchor_label"] = "A" + anchors_df["ancla_id"].astype(int).astype(str)

fig, axes = plt.subplots(2, 2, figsize=(9, 7))
for ax, (col, label) in zip(axes.flatten(), metrics):
    plot_df = anchors_df.dropna(subset=[col])

    medians_by_chip = {
        chip: plot_df[plot_df["chipset"] == chip].groupby("ancla_id")[col].median()
        for chip in ["dw1000", "dw3000"]
    }
    for chip, meds in medians_by_chip.items():
        if len(meds) >= 2:
            print(f"[{label}] cross-anchor range ({LABELS[chip]}): {meds.max()-meds.min():.3f}")

    sns.boxplot(
        data=plot_df, x="anchor_label", y=col, hue="chipset",
        hue_order=["dw1000", "dw3000"], palette=COLORS,
        showfliers=False, linewidth=1, ax=ax,
    )
    ax.set_title(label, fontweight="bold")
    ax.set_xlabel("")
    ax.set_ylabel("")
    ax.get_legend().remove()  # one shared legend for the whole figure instead
    sns.despine(ax=ax)

handles, _ = axes[0, 0].get_legend_handles_labels()
fig.suptitle("Cross-Anchor Consistency at Fixed 2 m Distance", fontweight="bold", y=1.02)
fig.legend(handles, ["DW1000", "DW3000"], loc="upper center", ncol=2, bbox_to_anchor=(0.5, 0.97))
fig.tight_layout(rect=[0, 0, 1, 0.93])
fig.savefig(OUT / "fig_cross_anchor_consistency.pdf", bbox_inches="tight")
plt.close(fig)
print("fig/fig_cross_anchor_consistency.pdf")

# === DIAGNOSTIC: TEMPERATURE BY ANCHOR ===

print("\nChip temperature by anchor:")
for chip in ["dw1000", "dw3000"]:
    anc0_chip = anc0_2m[anc0_2m["chipset"] == chip]
    print(f"  {LABELS[chip]} Anchor 0: temp median={anc0_chip['temp'].median():.2f}")
    others_chip = df[(df["carpeta"] == "calibration_anchors") & (df["chipset"] == chip)]
    for anc in sorted(others_chip["ancla_id"].dropna().unique()):
        sub = others_chip[others_chip["ancla_id"] == anc]
        print(f"  {LABELS[chip]} Anchor {int(anc)}: temp median={sub['temp'].median():.2f}")
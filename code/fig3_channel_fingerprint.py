"""
fig3_channel_fingerprint.py — Channel morphology fingerprint scatter (Fig. 3)
================================================================================
Reads cir_dataset.csv and generates a 2D scatter plot: Mean Excess Delay
vs. RMS Delay Spread, colored by the 4 groups
{DW1000, DW3000} x {Lab, Corridor}.

This reproduces Fig. 3 in the paper (Section III-B).

Applies the same integrity filter (is_valid, is_full_length) used
throughout the pipeline and in the paper's text, so that the medians
and n match exactly what is reported in Section III-B
(MED: 45.2/44.1 ns lab, 34.3/32.1 ns corridor;
 RMS: 40.0/40.0 ns lab, 35.7/33.8 ns corridor).
"""

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

OUT = Path(".")

# Seaborn "deep" palette: two base tones, lighter variant for corridor
PALETTE = sns.color_palette("deep", 2)
COLORS = {
    ("dw1000", "lab"):      PALETTE[0],
    ("dw1000", "corridor"): sns.light_palette(PALETTE[0], n_colors=3)[1],
    ("dw3000", "lab"):      PALETTE[1],
    ("dw3000", "corridor"): sns.light_palette(PALETTE[1], n_colors=3)[1],
}
MARKERS = {
    ("dw1000", "lab"):      "o",
    ("dw1000", "corridor"): "^",
    ("dw3000", "lab"):      "o",
    ("dw3000", "corridor"): "^",
}
GROUP_LABELS = {
    ("dw1000", "lab"):      "DW1000 - Lab",
    ("dw1000", "corridor"): "DW1000 - Corridor",
    ("dw3000", "lab"):      "DW3000 - Lab",
    ("dw3000", "corridor"): "DW3000 - Corridor",
}

print("Loading cir_dataset.csv...")
df = pd.read_csv(
    "cir_dataset.csv",
    usecols=["chipset", "carpeta", "mean_excess_delay_ns", "rms_delay_spread_ns",
             "is_valid", "is_full_length"],
)

# ── Integrity filter (identical to the one used for the paper's text) ──
val = df[
    df["carpeta"].isin(["lab", "corridor"]) &
    (df["is_valid"] == True) &
    (df["is_full_length"] == True)
].dropna(subset=["mean_excess_delay_ns", "rms_delay_spread_ns"])

fig, ax = plt.subplots(figsize=(5.0, 4.2))

groups = [("dw1000","lab"), ("dw1000","corridor"),
          ("dw3000","lab"), ("dw3000","corridor")]

stats_lines = []
def log(msg):
    print(msg)
    stats_lines.append(msg)

for chip, scen in groups:
    sub = val[(val["chipset"]==chip) & (val["carpeta"]==scen)]
    x = sub["mean_excess_delay_ns"]
    y = sub["rms_delay_spread_ns"]

    ax.scatter(x, y, s=8, alpha=0.18, color=COLORS[(chip,scen)],
               marker=MARKERS[(chip,scen)], rasterized=True, zorder=2)

    ax.scatter(x.median(), y.median(), s=160, color=COLORS[(chip,scen)],
               marker=MARKERS[(chip,scen)], edgecolor="black", linewidth=1.2,
               label=GROUP_LABELS[(chip,scen)], zorder=5)

    line = (f"  {GROUP_LABELS[(chip,scen)]:20s} | n={len(sub):5d} | "
            f"MED_median={x.median():6.2f} ns | "
            f"RMS_median={y.median():6.2f} ns")
    print(line)
    stats_lines.append(line)

ax.set_xlabel("Mean Excess Delay (ns)")
ax.set_ylabel("RMS Delay Spread (ns)")
ax.legend(loc="upper left", framealpha=0.9, fontsize=7,
          markerscale=0.5, labelspacing=0.8, handletextpad=0.6,
          borderpad=0.6)
sns.despine(ax=ax, left=False, bottom=False)

fig.tight_layout()
fig.savefig(OUT / "fig_fingerprint_canal.pdf", bbox_inches="tight")
fig.savefig(OUT / "fig_fingerprint_canal.png", bbox_inches="tight")
plt.close(fig)
print("\n[OK] fig_fingerprint_canal.pdf generated")

with open(OUT / "stats_fingerprint.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(stats_lines))
print("[OK] stats_fingerprint.txt saved")

print("\n" + "=" * 65)
print("Compare the medians above with the paper's text (Section III-B):")
print("  MED -- Lab: DW1000=45.2ns, DW3000=44.1ns")
print("  MED -- Corridor: DW1000=34.3ns, DW3000=32.1ns")
print("  RMS -- Lab: DW1000=40.0ns, DW3000=40.0ns")
print("  RMS -- Corridor: DW1000=35.7ns, DW3000=33.8ns")
print("=" * 65)

"""fig3_channel_fingerprint.py — Fig. 3 of the paper (Section III-B)"""

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

OUT = Path("fig")
OUT.mkdir(exist_ok=True)

# two base tones, lighter variant for corridor
PALETTE = sns.color_palette("deep", 2)
COLORS = {
    ("dw1000", "lab"):      PALETTE[0],
    ("dw1000", "corridor"): sns.light_palette(PALETTE[0], n_colors=3)[1],
    ("dw3000", "lab"):      PALETTE[1],
    ("dw3000", "corridor"): sns.light_palette(PALETTE[1], n_colors=3)[1],
}
MARKERS = {
    ("dw1000", "lab"): "o", ("dw1000", "corridor"): "^",
    ("dw3000", "lab"): "o", ("dw3000", "corridor"): "^",
}
GROUP_LABELS = {
    ("dw1000", "lab"): "DW1000 - Lab", ("dw1000", "corridor"): "DW1000 - Corridor",
    ("dw3000", "lab"): "DW3000 - Lab", ("dw3000", "corridor"): "DW3000 - Corridor",
}

df = pd.read_csv("cir_dataset.csv", usecols=[
    "chipset", "carpeta", "mean_excess_delay_ns", "rms_delay_spread_ns",
    "is_valid", "is_full_length",
])

val = df[
    df["carpeta"].isin(["lab", "corridor"]) &
    (df["is_valid"] == True) &
    (df["is_full_length"] == True)
].dropna(subset=["mean_excess_delay_ns", "rms_delay_spread_ns"])

fig, ax = plt.subplots(figsize=(5.0, 4.2))
groups = [("dw1000", "lab"), ("dw1000", "corridor"),
          ("dw3000", "lab"), ("dw3000", "corridor")]

for chip, scen in groups:
    sub = val[(val["chipset"] == chip) & (val["carpeta"] == scen)]
    x, y = sub["mean_excess_delay_ns"], sub["rms_delay_spread_ns"]

    ax.scatter(x, y, s=8, alpha=0.18, color=COLORS[(chip, scen)],
               marker=MARKERS[(chip, scen)], rasterized=True, zorder=2)
    ax.scatter(x.median(), y.median(), s=160, color=COLORS[(chip, scen)],
               marker=MARKERS[(chip, scen)], edgecolor="black", linewidth=1.2,
               label=GROUP_LABELS[(chip, scen)], zorder=5)  # group median marker

ax.set_xlabel("Mean Excess Delay (ns)")
ax.set_ylabel("RMS Delay Spread (ns)")
ax.legend(loc="upper left", framealpha=0.9, fontsize=7,
          markerscale=0.5, labelspacing=0.8, handletextpad=0.6, borderpad=0.6)
sns.despine(ax=ax)
fig.tight_layout()
fig.savefig(OUT / "fig3_channel_fingerprint.pdf", bbox_inches="tight")
plt.close(fig)
print("fig/fig3_channel_fingerprint.pdf")
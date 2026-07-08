"""
cross_anchor_consistency.py — Cross-anchor consistency at fixed 2 m distance
==============================================================================
Uses calibration_anchors (4 anchors at 2 m) to check whether fp_pwr and
Energy Ratio are consistent across anchors, or whether one anchor shows
anomalous behaviour.

Explicitly computes the anchor-to-anchor RANGE (max median - min median)
per chipset, which is the figure cited in the paper (Section III-A):
"varied by up to 11.7 dB in FP power and 4.9 ns in Mean Excess Delay,
versus 2.0 dB and 0.4 ns for the DW3000, with comparable RMS Delay
Spread variation (~2 ns) for both."

Also reports the per-anchor chip temperature (calibration_anc0 @2m vs.
calibration_anchors), which supports the paper's explanation for the
outlier: "This large DW1000 range is driven by a single anchor with a
higher device temperature, likely from prior use; the remaining three
anchors are mutually consistent (<=4.4 dB)."
"""

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from pathlib import Path

plt.rcParams.update({
    "font.family": "serif",
    "font.size": 9,
    "axes.titlesize": 9,
    "axes.labelsize": 9,
    "xtick.labelsize": 8,
    "ytick.labelsize": 8,
    "figure.dpi": 300,
})

COLORS = {"dw1000": "#1f77b4", "dw3000": "#d62728"}
LABELS = {"dw1000": "DW1000", "dw3000": "DW3000"}
OUT = Path(".")

print("Loading cir_dataset.csv...")
df = pd.read_csv(
    "cir_dataset.csv",
    usecols=["chipset", "carpeta", "ancla_id", "anc_medicion",
             "dist_real_m", "fp_pwr_dBm", "energy_ratio_fp",
             "mean_excess_delay_ns", "rms_delay_spread_ns",
             "temp", "is_valid", "is_full_length"],
)

# ── Integrity filter (consistent with the rest of the pipeline) ──
df = df[(df["is_valid"] == True) & (df["is_full_length"] == True)].copy()

# ── Safety net: exclude any "antiguas" (superseded) folder that slipped in ──
df = df[~df["carpeta"].str.contains("antiguas", case=False, na=False)].copy()

# ── Sanity check: is calibration_anchors really at 2.0 m? ──
print("\nChecking dist_real_m within calibration_anchors:")
calib_anchors_raw = df[df["carpeta"] == "calibration_anchors"]
print(calib_anchors_raw.groupby(["chipset", "ancla_id"])["dist_real_m"]
      .agg(["unique", "count"]))

# calibration_anc0 contains anchor 0 at several distances.
# Keep only the 2 m rows to compare against calibration_anchors.
anc0_2m = df[(df["carpeta"] == "calibration_anc0") &
             (df["dist_real_m"] == 2.0)].copy()

print(f"calibration_anc0 @2m: {len(anc0_2m)} rows, "
      f"anchors present: {sorted(anc0_2m['ancla_id'].dropna().unique())}")

# ── Duplicate check: calibration_anchors should NOT contain anchor 0 ──
dup_check = df[(df["carpeta"] == "calibration_anchors") & (df["ancla_id"] == 0)]
if len(dup_check) > 0:
    print(f"  [!] WARNING: calibration_anchors contains {len(dup_check)} rows "
          f"for anchor 0 -- possible duplicate with calibration_anc0 @2m")
else:
    print("  [OK] calibration_anchors does not contain anchor 0 (no duplicate)")

# calibration_anchors contains anchors 1, 2, 3 at 2 m.
anchors_df = pd.concat([
    anc0_2m,
    df[df["carpeta"] == "calibration_anchors"].copy(),
], ignore_index=True)

# ── Extra check: no (chipset, anchor) combination should draw rows
#    from both sources at once ──
combo_counts = anchors_df.groupby(["chipset", "ancla_id"]).size()
print(f"\nRows per (chipset, anchor) after combining sources:")
print(combo_counts.to_string())

print(f"\ncalibration_anchors + anc0 @2m: {len(anchors_df)} rows, "
      f"anchors present: {sorted(anchors_df['ancla_id'].dropna().unique())}")

metrics = [
    ("fp_pwr_dBm", "First-Path Power (dBm)"),
    ("energy_ratio_fp", "Energy Ratio (FP/Total)"),
    ("mean_excess_delay_ns", "Mean Excess Delay (ns)"),
    ("rms_delay_spread_ns", "RMS Delay Spread (ns)"),
]

stats_lines = []
def log(msg):
    print(msg)
    stats_lines.append(msg)

fig, axes = plt.subplots(2, 2, figsize=(8, 6))
axes = axes.flatten()

for ax, (col, label) in zip(axes, metrics):
    log(f"\n[{label}] -- by anchor (fixed 2 m, calibration_anchors)")
    data, tick_labels, colors = [], [], []
    medians_by_chip = {"dw1000": [], "dw3000": []}

    for chip in ["dw1000", "dw3000"]:
        for anc in sorted(anchors_df["ancla_id"].dropna().unique()):
            sub = anchors_df[(anchors_df["chipset"] == chip) &
                              (anchors_df["ancla_id"] == anc)][col].dropna()
            if len(sub) == 0:
                continue
            data.append(sub)
            tick_labels.append(f"{LABELS[chip]}\nA{int(anc)}")
            colors.append(COLORS[chip])
            medians_by_chip[chip].append(sub.median())
            log(f"  {LABELS[chip]:8s} anchor {int(anc)} | median={sub.median():.3f}  "
                f"std={sub.std():.3f}  n={len(sub)}")

    # ── Cross-anchor range (the figure cited in the paper) ──
    for chip in ["dw1000", "dw3000"]:
        vals = medians_by_chip[chip]
        if len(vals) >= 2:
            rng = max(vals) - min(vals)
            log(f"  >>> Cross-anchor range ({LABELS[chip]}): {rng:.3f} "
                f"(max={max(vals):.3f}, min={min(vals):.3f})")
        else:
            log(f"  [!] {LABELS[chip]}: fewer than 2 anchors with data, "
                f"cannot compute range")

    bp = ax.boxplot(data, labels=tick_labels, patch_artist=True,
                     showfliers=False,
                     medianprops=dict(color="black", linewidth=1.5))
    for patch, color in zip(bp["boxes"], colors):
        patch.set_facecolor(color)
        patch.set_alpha(0.7)
    ax.set_title(label, fontweight="bold", fontsize=8.5)
    ax.tick_params(axis="x", labelsize=6.5)
    ax.grid(True, axis="y", linestyle=":", alpha=0.4)

fig.suptitle("Cross-Anchor Consistency at Fixed 2 m Distance",
             fontweight="bold")
fig.tight_layout()
fig.savefig(OUT / "fig_anclas_consistencia.pdf", bbox_inches="tight")
fig.savefig(OUT / "fig_anclas_consistencia.png", bbox_inches="tight")
plt.close(fig)
print("\n[OK] fig_anclas_consistencia.pdf generated")

# ════════════════════════════════════════════════════════════════
# Chip temperature by anchor (supports the "prior use" explanation
# for the DW1000 outlier anchor cited in the paper, Section III-A)
# ════════════════════════════════════════════════════════════════
log("\n" + "=" * 65)
log("  CHIP TEMPERATURE BY ANCHOR (supporting evidence for the outlier)")
log("=" * 65)

for chip in ["dw1000", "dw3000"]:
    anc0_chip = anc0_2m[anc0_2m["chipset"] == chip]
    others_chip = df[(df["carpeta"] == "calibration_anchors") & (df["chipset"] == chip)]

    log(f"\n[{LABELS[chip]}]")
    log(f"  Anchor 0 (calibration_anc0 @2m): temp median={anc0_chip['temp'].median():.2f}, "
        f"min={anc0_chip['temp'].min():.2f}, max={anc0_chip['temp'].max():.2f}")

    for anc in sorted(others_chip["ancla_id"].dropna().unique()):
        sub = others_chip[others_chip["ancla_id"] == anc]
        log(f"  Anchor {int(anc)} (calibration_anchors): temp median={sub['temp'].median():.2f}, "
            f"min={sub['temp'].min():.2f}, max={sub['temp'].max():.2f}")

with open(OUT / "stats_anclas.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(stats_lines))
print("[OK] stats_anclas.txt saved")

print("\n" + "=" * 65)
print("Compare the 'Cross-anchor range' figures above with the paper text:")
print("  DW1000: ~11.7 dB (FP power), ~4.9 ns (Mean Excess Delay)")
print("  DW3000: ~2.0 dB (FP power), ~0.4 ns (Mean Excess Delay)")
print("  Both:   ~2 ns (RMS Delay Spread)")
print("  Excluding the outlier anchor, DW1000 anchors are mutually")
print("  consistent within <=4.4 dB (see temperature check above).")
print("=" * 65)

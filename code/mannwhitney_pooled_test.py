"""
mannwhitney_pooled_test.py — Pooled Mann-Whitney U test: Lab vs. Corridor
===========================================================================
Reads cir_dataset.csv and applies the Mann-Whitney U test (non-parametric,
distribution-free) to check whether the observed differences between Lab
and Corridor are statistically significant, per chipset, for the CIR
morphology metrics.

Also applies the same test between DW1000 and DW3000 within each
environment, to formally verify that the chipset effect is much smaller
(or non-significant) compared to the environmental effect.

This script produces the POOLED TEST values quoted at the start of
Section III-B of the paper:
  "A pooled Mann-Whitney test confirms a large environmental effect
   (|r|>0.60, p<0.001) and negligible hardware effect in the laboratory
   (|r|<0.21); the corridor comparison aggregates unequal sample sizes
   (1,403 DW1000 vs. 3,192 DW3000)..."

Applies the same integrity filter (is_valid, is_full_length) used
throughout the pipeline, so that n1/n2 match the "valid measurements"
reported in the text (3,680 / 1,403 / 3,506 / 3,192).
"""

import pandas as pd
from scipy import stats
from pathlib import Path

OUT = Path(".")

print("Loading cir_dataset.csv...")
df = pd.read_csv(
    "cir_dataset.csv",
    usecols=["chipset", "carpeta", "energy_ratio_fp",
             "mean_excess_delay_ns", "rms_delay_spread_ns",
             "is_valid", "is_full_length"],
)

# ── Integrity filter (identical to the one used for the paper's text) ──
val = df[
    df["carpeta"].isin(["lab", "corridor"]) &
    (df["is_valid"] == True) &
    (df["is_full_length"] == True)
].copy()

metrics = [
    ("energy_ratio_fp",      "Energy Ratio (FP/Total)"),
    ("mean_excess_delay_ns", "Mean Excess Delay (ns)"),
    ("rms_delay_spread_ns",  "RMS Delay Spread (ns)"),
]

stats_lines = []
def log(msg):
    print(msg)
    stats_lines.append(msg)

# ── Per-group n, to compare directly against the paper's text ──
log("=" * 70)
log("  n per group (after integrity filter) -- compare with the text:")
log("  DW1000-Lab=3680, DW1000-Corridor=1403, DW3000-Lab~3506, DW3000-Corridor~3192")
log("=" * 70)
log(val.groupby(["carpeta", "chipset"]).size().to_string())

log("\n" + "=" * 70)
log("  TEST 1: Lab vs. Corridor (same chipset) -- does the environment dominate?")
log("=" * 70)

for col, label in metrics:
    log(f"\n[{label}]")
    for chip in ["dw1000", "dw3000"]:
        lab = val[(val["chipset"]==chip) & (val["carpeta"]=="lab")][col].dropna()
        corr = val[(val["chipset"]==chip) & (val["carpeta"]=="corridor")][col].dropna()

        u_stat, p_value = stats.mannwhitneyu(lab, corr, alternative="two-sided")

        # Effect size: rank-biserial correlation (simple approximation)
        n1, n2 = len(lab), len(corr)
        effect_size = 1 - (2 * u_stat) / (n1 * n2)

        sig = "***" if p_value < 0.001 else ("**" if p_value < 0.01 else
              ("*" if p_value < 0.05 else "ns"))

        log(f"  {chip.upper():8s} | Lab median={lab.median():.3f} vs "
            f"Corridor median={corr.median():.3f} | n_lab={n1} n_corr={n2} | "
            f"U={u_stat:.0f}  p={p_value:.2e}  effect_r={effect_size:.3f}  [{sig}]")

log("\n" + "=" * 70)
log("  TEST 2: DW1000 vs. DW3000 (same environment) -- does the chipset dominate?")
log("=" * 70)

for col, label in metrics:
    log(f"\n[{label}]")
    for scen in ["lab", "corridor"]:
        dw1 = val[(val["carpeta"]==scen) & (val["chipset"]=="dw1000")][col].dropna()
        dw3 = val[(val["carpeta"]==scen) & (val["chipset"]=="dw3000")][col].dropna()

        u_stat, p_value = stats.mannwhitneyu(dw1, dw3, alternative="two-sided")
        n1, n2 = len(dw1), len(dw3)
        effect_size = 1 - (2 * u_stat) / (n1 * n2)

        sig = "***" if p_value < 0.001 else ("**" if p_value < 0.01 else
              ("*" if p_value < 0.05 else "ns"))

        log(f"  {scen:10s} | DW1000 median={dw1.median():.3f} vs "
            f"DW3000 median={dw3.median():.3f} | n_dw1={n1} n_dw3={n2} | "
            f"U={u_stat:.0f}  p={p_value:.2e}  effect_r={effect_size:.3f}  [{sig}]")

log("\n" + "=" * 70)
log("  INTERPRETATION")
log("=" * 70)
log("  effect_r near 0 = no practical difference (even if p is significant)")
log("  effect_r > 0.3 = moderate difference;  > 0.5 = large difference")
log("  With large n, even trivial differences yield p<0.001 -- that is why")
log("  the effect size is more informative than the p-value here.")
log("")
log("  Compare TEST 2 with the paper's text (Section III-B):")
log("  Lab:      |r|<0.21 expected (negligible hardware effect)")
log("  Corridor: aggregated effect, but attributed to coverage disparity,")
log("            NOT to an independent chipset effect (see Section III-C)")

with open(OUT / "stats_test_estadistico.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(stats_lines))
print("\n[OK] stats_test_estadistico.txt saved")

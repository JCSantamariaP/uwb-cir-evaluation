"""
table1_anchor_stratified_test.py — Mann-Whitney U at (position, anchor) level
================================================================================
Produces Table I of the paper: a paired DW1000 vs. DW3000 comparison,
stratified by anchor, restricted to matched position-anchor pairs.

Logic:
  1. Aggregate by (chipset, carpeta, punto_id, anc_medicion) -> median of
     the ~20 repeated exchanges for THAT position seen by THAT specific
     anchor.
  2. Compare DW1000 vs. DW3000 only on the (punto_id, anc_medicion) pairs
     present for both chipsets -- a strictly paired comparison.

Notes on methodology:
  - NaNs are dropped per-metric right before each test (scipy.stats.
    mannwhitneyu does not ignore NaN: a single NaN makes U and p come
    out as NaN).
  - Besides the anchor-stratified test (Table I), this script also runs
    the POOLED test (all anchors together), which reproduces the opening
    paragraph of Section III-B (n=176 lab / n=65 corridor).
"""

import pandas as pd
from scipy import stats
from pathlib import Path

OUT = Path(".")
COL_POS = "punto_id"
COL_ANC = "anc_medicion"

print("Loading cir_dataset.csv...")
df = pd.read_csv("cir_dataset.csv")

metrics = [
    ("energy_ratio_fp",      "Energy Ratio (FP/Total)"),
    ("mean_excess_delay_ns", "Mean Excess Delay (ns)"),
    ("rms_delay_spread_ns",  "RMS Delay Spread (ns)"),
]
needed_cols = ["chipset", "carpeta", COL_POS, COL_ANC] + [m[0] for m in metrics]
val = df[df["carpeta"].isin(["lab", "corridor"])][needed_cols].copy()

# --- Aggregation by (chipset, scenario, position, anchor) -----------------
agg = (
    val.groupby(["chipset", "carpeta", COL_POS, COL_ANC])[[m[0] for m in metrics]]
       .median()
       .reset_index()
)

stats_lines = []
def log(msg):
    print(msg)
    stats_lines.append(msg)


def paired_test(dw1_vals_raw, dw3_vals_raw, label, indent="  "):
    """Runs the test after dropping NaN, reports the actual n used."""
    df_pair = pd.DataFrame({"dw1": dw1_vals_raw, "dw3": dw3_vals_raw}).dropna()
    n_valid = len(df_pair)

    if n_valid < 3:
        log(f"{indent}[{label:24s}] insufficient n after dropping NaN ({n_valid}) -- skipped")
        return

    dw1_vals = df_pair["dw1"]
    dw3_vals = df_pair["dw3"]

    u_stat, p_value = stats.mannwhitneyu(dw1_vals, dw3_vals, alternative="two-sided")
    effect_size = 1 - (2 * u_stat) / (n_valid * n_valid)
    sig = "***" if p_value < 0.001 else ("**" if p_value < 0.01 else
          ("*" if p_value < 0.05 else "ns"))

    log(f"{indent}[{label:24s}] n={n_valid:3d} | "
        f"DW1000 median={dw1_vals.median():.3f} vs DW3000 median={dw3_vals.median():.3f} | "
        f"U={u_stat:.0f}  p={p_value:.3f}  effect_r={effect_size:.3f}  [{sig}]")


log("=" * 80)
log(f"  Aggregated rows (chipset x scenario x {COL_POS} x {COL_ANC}): {len(agg)}")
log("=" * 80)
n_per_group = agg.groupby(["carpeta", "chipset"]).size()
log(n_per_group.to_string())

# ════════════════════════════════════════════════════════════════
# POOLED TEST (all anchors together) -- opening paragraph of III-B
# ════════════════════════════════════════════════════════════════
log("\n" + "=" * 80)
log("  POOLED TEST: DW1000 vs. DW3000, all anchors together")
log("  (reproduces n=176 lab / n=65 corridor from the text)")
log("=" * 80)

for scen in ["lab", "corridor"]:
    sub = agg[agg["carpeta"] == scen]
    dw1 = sub[sub["chipset"] == "dw1000"][[COL_POS, COL_ANC] + [m[0] for m in metrics]]
    dw3 = sub[sub["chipset"] == "dw3000"][[COL_POS, COL_ANC] + [m[0] for m in metrics]]

    paired = dw1.merge(dw3, on=[COL_POS, COL_ANC], suffixes=("_dw1", "_dw3"), how="inner")
    n_common = len(paired)

    log(f"\n--- Environment: {scen} (n={n_common} position-anchor pairs) ---")

    for col, label in metrics:
        paired_test(paired[f"{col}_dw1"], paired[f"{col}_dw3"], label)

# ════════════════════════════════════════════════════════════════
# ANCHOR-STRATIFIED TEST -- reproduces Table I
# ════════════════════════════════════════════════════════════════
log("\n" + "=" * 80)
log("  ANCHOR-STRATIFIED TEST (reproduces Table I of the paper)")
log("=" * 80)

for scen in ["lab", "corridor"]:
    log(f"\n--- Environment: {scen} ---")
    sub = agg[agg["carpeta"] == scen]
    anchors_present = sorted(sub[COL_ANC].dropna().unique())

    for anc in anchors_present:
        sub_anc = sub[sub[COL_ANC] == anc]
        dw1 = sub_anc[sub_anc["chipset"] == "dw1000"][[COL_POS] + [m[0] for m in metrics]]
        dw3 = sub_anc[sub_anc["chipset"] == "dw3000"][[COL_POS] + [m[0] for m in metrics]]

        paired = dw1.merge(dw3, on=[COL_POS], suffixes=("_dw1", "_dw3"), how="inner")
        n_common = len(paired)

        log(f"\n  Anchor {int(anc)} (n={n_common} paired positions):")
        # Table I only reports Mean Excess Delay and RMS Delay Spread
        for col, label in metrics[1:]:
            paired_test(paired[f"{col}_dw1"], paired[f"{col}_dw3"], label, indent="    ")

log("\n" + "=" * 80)
log("  Compare the block above with Table I of the paper:")
log("  Laboratory -- Anchor 0: n=44, MED r=-0.10 (p=0.44), RMS r=-0.04 (p=0.74)")
log("  Laboratory -- Anchor 1: n=44, MED r=-0.03 (p=0.81), RMS r=-0.04 (p=0.75)")
log("  Laboratory -- Anchor 2: n=44, MED r=-0.10 (p=0.41), RMS r=-0.10 (p=0.43)")
log("  Laboratory -- Anchor 3: n=44, MED r=-0.16 (p=0.19), RMS r= 0.07 (p=0.57)")
log("  Corridor   -- Anchor 0: n=19, MED r=-0.32 (p=0.096), RMS r=-0.55 (p=0.004)")
log("  Corridor   -- Anchor 1: n=22, MED r=-0.51 (p=0.004), RMS r=-0.59 (p<0.001)")
log("  Corridor   -- Anchor 2: n=12, MED r=-0.40 (p=0.100), RMS r=-0.50 (p=0.040)")
log("  Corridor   -- Anchor 3: n=12, MED r=-0.28 (p=0.260), RMS r=-0.42 (p=0.089)")
log("=" * 80)

with open(OUT / "stats_test_por_posicion_y_ancla.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(stats_lines))
print("\n[OK] stats_test_por_posicion_y_ancla.txt saved")

"""table1_anchor_stratified_test.py — Table I of the paper"""

import pandas as pd
from scipy import stats

COL_POS, COL_ANC = "punto_id", "anc_medicion"

df = pd.read_csv("cir_dataset.csv")
metrics = [
    ("energy_ratio_fp", "Energy Ratio (FP/Total)"),
    ("mean_excess_delay_ns", "Mean Excess Delay (ns)"),
    ("rms_delay_spread_ns", "RMS Delay Spread (ns)"),
]
val = df[df["carpeta"].isin(["lab", "corridor"])][
    ["chipset", "carpeta", COL_POS, COL_ANC] + [m[0] for m in metrics]
]

# median of the ~20 repeated exchanges for each (chipset, scenario, position, anchor)
agg = (
    val.groupby(["chipset", "carpeta", COL_POS, COL_ANC])[[m[0] for m in metrics]]
       .median()
       .reset_index()
)


def paired_test(a, b, label, indent="  "):
    pair = pd.DataFrame({"dw1": a, "dw3": b}).dropna()  # scipy doesn't ignore NaN
    if len(pair) < 3:
        print(f"{indent}[{label:24s}] n too small, skipped")
        return
    u_stat, p_value = stats.mannwhitneyu(pair["dw1"], pair["dw3"], alternative="two-sided")
    effect_r = 1 - (2 * u_stat) / (len(pair) ** 2)
    print(f"{indent}[{label:24s}] n={len(pair):3d} | "
          f"median1={pair['dw1'].median():.3f} median2={pair['dw3'].median():.3f} | "
          f"U={u_stat:.0f} p={p_value:.3f} effect_r={effect_r:.3f}")


print("POOLED TEST (all anchors together, reproduces intro of Section III-B)")
for scen in ["lab", "corridor"]:
    sub = agg[agg["carpeta"] == scen]
    dw1 = sub[sub["chipset"] == "dw1000"]
    dw3 = sub[sub["chipset"] == "dw3000"]
    paired = dw1.merge(dw3, on=[COL_POS, COL_ANC], suffixes=("_dw1", "_dw3"))
    print(f"\n--- {scen} (n={len(paired)} position-anchor pairs) ---")
    for col, label in metrics:
        paired_test(paired[f"{col}_dw1"], paired[f"{col}_dw3"], label)

print("\nANCHOR-STRATIFIED TEST (reproduces Table I)")
for scen in ["lab", "corridor"]:
    print(f"\n--- {scen} ---")
    sub = agg[agg["carpeta"] == scen]
    for anc in sorted(sub[COL_ANC].dropna().unique()):
        sub_anc = sub[sub[COL_ANC] == anc]
        dw1 = sub_anc[sub_anc["chipset"] == "dw1000"]
        dw3 = sub_anc[sub_anc["chipset"] == "dw3000"]
        paired = dw1.merge(dw3, on=[COL_POS], suffixes=("_dw1", "_dw3"))
        print(f"\n  Anchor {int(anc)} (n={len(paired)} paired positions):")
        for col, label in metrics[1:]:  # Table I only reports MED and RMS
            paired_test(paired[f"{col}_dw1"], paired[f"{col}_dw3"], label, indent="    ")
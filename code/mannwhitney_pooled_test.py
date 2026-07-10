"""mannwhitney_pooled_test.py — Pooled Mann-Whitney tests (Section III-B)"""

import pandas as pd
from scipy import stats

df = pd.read_csv("cir_dataset.csv", usecols=[
    "chipset", "carpeta", "energy_ratio_fp",
    "mean_excess_delay_ns", "rms_delay_spread_ns",
    "is_valid", "is_full_length",
])

val = df[
    df["carpeta"].isin(["lab", "corridor"]) &
    (df["is_valid"] == True) &
    (df["is_full_length"] == True)
]

metrics = [
    ("energy_ratio_fp", "Energy Ratio (FP/Total)"),
    ("mean_excess_delay_ns", "Mean Excess Delay (ns)"),
    ("rms_delay_spread_ns", "RMS Delay Spread (ns)"),
]


def run_test(a, b, label):
    u_stat, p_value = stats.mannwhitneyu(a, b, alternative="two-sided")
    effect_r = 1 - (2 * u_stat) / (len(a) * len(b))  # rank-biserial correlation
    print(f"  [{label:24s}] n1={len(a)} n2={len(b)} | "
          f"median1={a.median():.3f} median2={b.median():.3f} | "
          f"U={u_stat:.0f} p={p_value:.2e} effect_r={effect_r:.3f}")


print("TEST 1: Lab vs. Corridor (same chipset)")
for col, label in metrics:
    for chip in ["dw1000", "dw3000"]:
        lab = val[(val["chipset"] == chip) & (val["carpeta"] == "lab")][col].dropna()
        corr = val[(val["chipset"] == chip) & (val["carpeta"] == "corridor")][col].dropna()
        run_test(lab, corr, f"{chip.upper()} - {label}")

print("\nTEST 2: DW1000 vs. DW3000 (same environment)")
for col, label in metrics:
    for scen in ["lab", "corridor"]:
        dw1 = val[(val["carpeta"] == scen) & (val["chipset"] == "dw1000")][col].dropna()
        dw3 = val[(val["carpeta"] == scen) & (val["chipset"] == "dw3000")][col].dropna()
        run_test(dw1, dw3, f"{scen} - {label}")
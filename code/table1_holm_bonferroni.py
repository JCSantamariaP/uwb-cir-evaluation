"""table1_holm_bonferroni.py — Table I of the paper (Section III-B)"""

import numpy as np
import pandas as pd
from scipy import stats
from statsmodels.stats.multitest import multipletests

np.random.seed(42)  # fixed seed for reproducibility

COL_POS, COL_ANC = "punto_id", "anc_medicion"
N_BOOT = 5000

# === LOAD AND AGGREGATE ===

df = pd.read_csv("cir_dataset.csv")

metrics = [
    ("energy_ratio_fp", "Energy Ratio (FP/Total)"),
    ("mean_excess_delay_ns", "Mean Excess Delay (ns)"),
    ("rms_delay_spread_ns", "RMS Delay Spread (ns)"),
]

val = df[df["carpeta"].isin(["lab", "corridor"])][
    ["chipset", "carpeta", COL_POS, COL_ANC] + [m[0] for m in metrics]
]

# median of the repeated exchanges for each (chipset, scenario, position, anchor)
agg = (
    val.groupby(["chipset", "carpeta", COL_POS, COL_ANC])[[m[0] for m in metrics]]
       .median()
       .reset_index()
)


# === STATS HELPERS ===

def bootstrap_r_ci(dw1, dw3, n_boot=N_BOOT):
    """95% CI for rank-biserial r via non-parametric bootstrap."""
    a = dw1.values
    b = dw3.values
    n = len(a)
    rs = []
    for _ in range(n_boot):
        idx_a = np.random.choice(n, n, replace=True)
        idx_b = np.random.choice(n, n, replace=True)
        u, _ = stats.mannwhitneyu(a[idx_a], b[idx_b], alternative="two-sided")
        rs.append(1 - (2 * u) / (n ** 2))
    return np.percentile(rs, [2.5, 97.5])


def calculate_stats(a, b, label, scen, anc):
    pair = pd.DataFrame({"dw1": a, "dw3": b}).dropna()
    n = len(pair)
    if n < 3:
        return None

    u_stat, p_value = stats.mannwhitneyu(pair["dw1"], pair["dw3"], alternative="two-sided")
    effect_r = 1 - (2 * u_stat) / (n ** 2)
    ci_low, ci_high = bootstrap_r_ci(pair["dw1"], pair["dw3"])

    return {
        "scenario": scen, "anchor": int(anc), "label": label, "n": n,
        "med1": pair["dw1"].median(), "med2": pair["dw3"].median(),
        "u": u_stat, "p_raw": p_value, "r": effect_r,
        "ci_low": ci_low, "ci_high": ci_high,
    }


# === RUN ALL TESTS (lab + corridor, Mean Excess Delay + RMS Delay Spread) ===

results_list = []
for scen in ["lab", "corridor"]:
    sub = agg[agg["carpeta"] == scen]
    for anc in sorted(sub[COL_ANC].dropna().unique()):
        sub_anc = sub[sub[COL_ANC] == anc]
        dw1 = sub_anc[sub_anc["chipset"] == "dw1000"]
        dw3 = sub_anc[sub_anc["chipset"] == "dw3000"]
        paired = dw1.merge(dw3, on=[COL_POS], suffixes=("_dw1", "_dw3"))

        for col, label in metrics[1:]:  # skip energy_ratio_fp, not in Table I
            res = calculate_stats(paired[f"{col}_dw1"], paired[f"{col}_dw3"], label, scen, anc)
            if res:
                results_list.append(res)

# global correction (all 16 tests at once)
p_raw_all = [r["p_raw"] for r in results_list]
_, p_corr_global, _, _ = multipletests(p_raw_all, method="holm")
for r, p in zip(results_list, p_corr_global):
    r["p_holm_global"] = p

# by-scenario correction (8 lab tests and 8 corridor tests, corrected separately)
for scen in ["lab", "corridor"]:
    scen_results = [r for r in results_list if r["scenario"] == scen]
    p_raw_scen = [r["p_raw"] for r in scen_results]
    _, p_corr_scen, _, _ = multipletests(p_raw_scen, method="holm")
    for r, p in zip(scen_results, p_corr_scen):
        r["p_holm_scenario"] = p


# === PRINT RESULTS ===

print("ANCHOR-STRATIFIED TEST — Table I")
print(f"Comparing GLOBAL correction (n=16 tests) vs. BY-SCENARIO correction (n=8 tests each)")
print(f"95% CI via bootstrap, n_boot={N_BOOT}\n")

current_scen, current_anc = None, None
for r in results_list:
    if r["scenario"] != current_scen:
        print(f"\n=== {r['scenario'].upper()} ===")
        current_scen = r["scenario"]
        current_anc = None
    if r["anchor"] != current_anc:
        print(f"\n  Anchor {r['anchor']} (n={r['n']}):")
        current_anc = r["anchor"]

    sig_global = "**" if r["p_holm_global"] < 0.05 else "  "
    sig_scen = "**" if r["p_holm_scenario"] < 0.05 else "  "
    print(f"    [{r['label']:24s}] "
          f"p_raw={r['p_raw']:.3f} | "
          f"p_holm_global={r['p_holm_global']:.3f}{sig_global} | "
          f"p_holm_scenario={r['p_holm_scenario']:.3f}{sig_scen} | "
          f"r={r['r']:.3f} (95% CI: [{r['ci_low']:.2f}, {r['ci_high']:.2f}])")

print("\n" + "=" * 70)
print("SUMMARY — significant (p<0.05) after correction:")
sig_global_list = [f"{r['scenario']} Anchor {r['anchor']} ({r['label']})"
                    for r in results_list if r["p_holm_global"] < 0.05]
sig_scen_list = [f"{r['scenario']} Anchor {r['anchor']} ({r['label']})"
                  for r in results_list if r["p_holm_scenario"] < 0.05]
print(f"  Global correction (n=16):    {sig_global_list if sig_global_list else 'none'}")
print(f"  By-scenario correction (8+8): {sig_scen_list if sig_scen_list else 'none'}")
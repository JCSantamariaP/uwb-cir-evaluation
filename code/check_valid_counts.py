"""check_valid_counts.py — verify Section II-B sample counts"""

import pandas as pd

df = pd.read_csv("cir_dataset.csv")

# === COUNT BY chipset/SCENARIO: is_valid & is_full_length only ===

val = df[
    df["carpeta"].isin(["lab", "corridor"]) &
    (df["is_valid"] == True) &
    (df["is_full_length"] == True)
]

print("Valid measurements (is_valid & is_full_length) by chipset and scenario:")
print(val.groupby(["carpeta", "chipset"]).size().to_string())

# === NOTE: this is a looser definition than the one used in the paper ===
# Table I / the pooled tests also require mean_excess_delay_ns to be non-null
# (dropped when the 3-sigma noise mask leaves fewer than 3 samples). The two
# counts can differ by a few dozen rows in the corridor -- shown below for
# DW3000/corridor, which is the case cited in the paper.

corridor_dw3000 = df[
    (df["carpeta"] == "corridor") & (df["chipset"] == "dw3000") &
    df["is_valid"] & df["is_full_length"]
]
print("\nDW3000/corridor:")
print("  is_valid & is_full_length:            ", len(corridor_dw3000))
print("  also with mean_excess_delay_ns valid: ",
      corridor_dw3000["mean_excess_delay_ns"].notna().sum())
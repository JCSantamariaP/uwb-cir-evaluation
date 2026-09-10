"""check_fppwr_consistency.py — verify DW3000 non-monotonic FP power
pattern is not measurement noise (Section III-A)"""

import pandas as pd

df = pd.read_csv("cir_dataset.csv")
val = df[(df["carpeta"] == "calibration_anc0") & df["is_valid"] & df["is_full_length"]]

# === FP power median by distance, per chipset ===

for chip in ["dw1000", "dw3000"]:
    print(chip)
    print(val[val["chipset"] == chip].groupby("dist_real_m")["fp_pwr_dBm"].median())

# === DW3000: spread at the 4 m and 5 m distances (the two points of the
# non-monotonic dip -> recovery -> drop pattern) ===

for dist in [4.0, 5.0]:
    sub = val[(val["chipset"] == "dw3000") & (val["dist_real_m"] == dist)]["fp_pwr_dBm"]
    print(f"{dist}m: n={len(sub)}, p10={sub.quantile(0.10):.2f}, "
          f"p90={sub.quantile(0.90):.2f}, std={sub.std():.2f}")
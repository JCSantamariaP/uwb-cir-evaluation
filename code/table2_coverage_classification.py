"""table2_coverage_classification.py — Table II of the paper"""

import pandas as pd

CORRIDOR_POINTS = list(range(1, 22)) + list(range(51, 77))  # 47 ground-truth positions

df = pd.read_csv("cir_dataset.csv")
corridor = df[
    (df["carpeta"] == "corridor") &
    (df["is_valid"] == True) &
    (df["is_full_length"] == True)
]

rows = []
for chipset in ["dw1000", "dw3000"]:
    sub = corridor[corridor["chipset"] == chipset]
    for punto_id in CORRIDOR_POINTS:
        n_anchors = sub[sub["punto_id"] == punto_id]["anc_medicion"].nunique(dropna=True)
        # classification per the paper: 0 anchors=failed, 1-2=weak, 3-4=valid
        status = "failed" if n_anchors == 0 else "weak" if n_anchors <= 2 else "valid"
        rows.append({"chipset": chipset, "punto_id": punto_id, "status": status})

summary = pd.DataFrame(rows)
n_points = len(CORRIDOR_POINTS)

for chipset in ["dw1000", "dw3000"]:
    counts = summary[summary["chipset"] == chipset]["status"].value_counts()
    print(f"\n{chipset.upper()}:")
    for status in ["valid", "weak", "failed"]:
        n = counts.get(status, 0)
        print(f"  {status:6s}: {n} ({100*n/n_points:.1f}%)")

summary.to_csv("table2_coverage_by_point.csv", index=False)
print("\n[table2_coverage_by_point.csv saved")
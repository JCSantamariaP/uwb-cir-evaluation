"""
table2_coverage_classification.py — Corridor coverage classification (Table II)
==================================================================================
Produces Table II of the paper: for each of the 47 corridor ground-truth
positions, classifies coverage per chipset by the number of unique anchors
that produced a valid CIR capture at that position:

  - failed : 0 anchors with valid data
  - weak   : 1-2 anchors with valid data
  - valid  : 3-4 anchors with valid data

This matches the paper's definition (Section III-C): "Positions where none
of the four anchors produced a valid CIR capture were classified as
failed; those with one or two unique anchors as weak and those with
three or four anchors as valid."
"""

import pandas as pd
from pathlib import Path

OUT = Path(".")

print("Loading cir_dataset.csv...")
df = pd.read_csv("cir_dataset.csv")

# Keep corridor rows only
corridor = df[df["carpeta"] == "corridor"].copy()

# ── Integrity filter ──────────────────────────────────────────────
n_before = len(corridor)
corridor = corridor[
    (corridor["is_valid"] == True) & (corridor["is_full_length"] == True)
].copy()
print(f"Integrity filter: {n_before} -> {len(corridor)} rows "
      f"({n_before - len(corridor)} discarded)")

# The 47 REAL corridor positions (per ground truth)
CORRIDOR_POINTS = list(range(1, 22)) + list(range(51, 77))  # 1-21 and 51-76

stats_lines = []
def log(msg):
    print(msg)
    stats_lines.append(msg)

log("=" * 80)
log("  DETAILED COVERAGE BY POSITION AND ANCHOR (corridor)")
log("=" * 80)

summary_rows = []

for chipset in ["dw1000", "dw3000"]:
    log(f"\n--- {chipset.upper()} ---")
    sub = corridor[corridor["chipset"] == chipset]

    for punto_id in CORRIDOR_POINTS:
        point_data = sub[sub["punto_id"] == punto_id]
        total_captures = len(point_data)
        unique_anchors = point_data["anc_medicion"].nunique(dropna=True)
        anchor_list = sorted(point_data["anc_medicion"].dropna().unique())

        # Classification by number of anchors, not by total capture count
        if unique_anchors == 0:
            status = "FAILED"
        elif unique_anchors <= 2:
            status = "WEAK"
        else:  # 3-4 anchors
            status = "VALID"

        log(f"  Point {punto_id:3d}: {status:6s} | "
            f"total={total_captures:3d} | "
            f"anchors={unique_anchors} ({anchor_list})")

        summary_rows.append({
            "chipset": chipset, "punto_id": punto_id,
            "status": status.lower(), "total": total_captures,
            "anchors": unique_anchors,
        })

# Aggregated summary
log("\n" + "=" * 80)
log("  SUMMARY BY CHIPSET (anchor-based classification)")
log("=" * 80)

summary_df = pd.DataFrame(summary_rows)
n_points = len(CORRIDOR_POINTS)

for chipset in ["dw1000", "dw3000"]:
    res_df = summary_df[summary_df["chipset"] == chipset]

    failed = res_df[res_df["status"] == "failed"]
    weak = res_df[res_df["status"] == "weak"]
    valid = res_df[res_df["status"] == "valid"]

    log(f"\n{chipset.upper()}:")
    log(f"  Failed (0 anchors): {len(failed)} points ({100*len(failed)/n_points:.1f}%)")
    if len(failed) > 0:
        log(f"    IDs: {sorted(failed['punto_id'].tolist())}")

    log(f"  Weak (1-2 anchors): {len(weak)} points ({100*len(weak)/n_points:.1f}%)")

    log(f"  Valid (3-4 anchors): {len(valid)} points ({100*len(valid)/n_points:.1f}%)")
    if len(valid) > 0:
        log(f"\n  Anchor-count distribution among VALID points:")
        log(f"    {valid['anchors'].value_counts().sort_index().to_dict()}")

log("\n" + "=" * 80)
log("  Compare with Table II of the paper:")
log("  DW1000: Valid 2 (4.3%), Weak 35 (74.5%), Failed 10 (21.3%)")
log("  DW3000: Valid 23 (48.9%), Weak 23 (48.9%), Failed 1 (2.1%)")
log("=" * 80)

with open(OUT / "stats_table2_coverage.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(stats_lines))
print("\n[OK] stats_table2_coverage.txt saved")

summary_df.to_csv(OUT / "table2_coverage_by_point.csv", index=False)
print("[OK] table2_coverage_by_point.csv saved")

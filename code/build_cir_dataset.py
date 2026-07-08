"""
build_cir_dataset.py — Build the processed CIR dataset from raw captures
=========================================================================
Reads all raw .txt files (one JSON object per line) from the DW1000 and
DW3000 data folders and produces a SINGLE CSV with:

  - Measurement metadata (chipset, scenario, punto_id/ancla_id,
    carpeta, dist_real_m where applicable)
  - Direct chip metrics (fp_pwr, rx_pwr, Pk_amp, C, stdN, N, temp)
  - CIR morphology metrics computed in this script:
      * energy_ratio_fp       : first-path energy / total window energy
      * mean_excess_delay_ns  : mean delay of the energy relative to the FP
      * rms_delay_spread_ns   : temporal dispersion of the pulse
      * kurtosis_cir          : "peakedness" of the envelope
      * skewness_cir          : asymmetry of the envelope

IMPORTANT — WHAT THIS SCRIPT DOES *NOT* DO:
  - It does NOT compute Tprop, ToF, or measured distance (dist_cruda_m)
  - It does NOT use t1-t6 for ranging
  - It does NOT depend on the DW3000 timestamp-packing firmware
  All metrics derive exclusively from fp_ind and CIR_R/CIR_I, which are
  independent of the payload-alignment issue identified in the ranging
  pipeline (see the paper, Section II-B: "we analyze this CIR data
  rather than distance estimates").

EXPECTED FOLDER STRUCTURE:
  data/
    dw1000/
      calibration_anc0/      *.txt   (filename contains "_idA0_<dist>m")
      calibration_anchors/   *.txt   (filename contains "_idA<n>_2.0m")
      lab/                   *.txt   (filename contains "_id<point>")
      corridor/              *.txt   (filename contains "_id<point>")
    dw3000/
      (same structure; folders containing "_antiguas" are excluded)
    GroundTruth/
      anchors.csv
      points.csv

OUTPUT:
  cir_dataset.csv
"""

import json
import math
import re
import numpy as np
import pandas as pd
from pathlib import Path

# ── Physical constants ──────────────────────────────────────────────
FS = 499.2e6                   # Hz, CIR sampling frequency
TS_NS = (1.0 / FS) * 1e9        # ~2.0032 ns per bin
WINDOW_PRE_BINS = 5
WINDOW_POST_BINS = 75           # ~150 ns after the first path
NOISE_SIGMA_THRESHOLD = 3       # noise threshold: 3x stdN

DATA_ROOT = Path("data")
CHIPSETS = ["dw1000", "dw3000"]
CALIBRATION_FOLDERS = ["calibration_anc0", "calibration_anchors"]
SCENARIO_FOLDERS = ["lab", "corridor"]


# ══════════════════════════════════════════════════════════════════
# READING AND LIGHTWEIGHT REPAIR OF JSON LINES
# ══════════════════════════════════════════════════════════════════

def read_records(path: Path) -> list[dict]:
    records = []
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue

            # Attempt 1: direct parse
            try:
                records.append(json.loads(line))
                continue
            except json.JSONDecodeError:
                pass

            # Attempt 2: forced closing of a truncated JSON object.
            # If it ends in a digit, close the array and the object.
            repaired = re.sub(r"(\d+)$", r"\1]}", line)
            # If it ends in a quote, close the quote, array, and object.
            if repaired == line:
                repaired = line.rstrip('"') + '"]}'

            try:
                records.append(json.loads(repaired))
            except json.JSONDecodeError:
                # Corruption is too severe to repair heuristically; skip.
                continue
    return records


# ══════════════════════════════════════════════════════════════════
# CIR MORPHOLOGY METRICS
# ══════════════════════════════════════════════════════════════════

METRIC_FIELDS = [
    "energy_ratio_fp", "mean_excess_delay_ns",
    "rms_delay_spread_ns", "kurtosis_cir", "skewness_cir",
]


def compute_amplitude_phase(cir_r, cir_i):
    """Computes the envelope (amplitude) and phase of the full CIR.
    Returns Python lists (not numpy arrays) ready for json.dumps,
    rounded to avoid inflating the CSV size unnecessarily."""
    try:
        r = np.asarray(cir_r, dtype=float)
        i = np.asarray(cir_i, dtype=float)
    except (TypeError, ValueError):
        return None, None
    if len(r) == 0 or len(r) != len(i):
        return None, None

    amplitude = np.sqrt(r**2 + i**2)
    phase = np.arctan2(i, r)

    amplitude_list = [round(float(x), 2) for x in amplitude]
    phase_list = [round(float(x), 4) for x in phase]
    return amplitude_list, phase_list


def compute_cir_metrics(cir_r, cir_i, fp_ind, stdN):
    """Computes morphology metrics in a bounded window around the
    first path. Returns a dict of NaN if there is not enough data."""
    empty = dict.fromkeys(METRIC_FIELDS, float("nan"))

    if cir_r is None or cir_i is None or fp_ind is None or stdN is None:
        return empty
    try:
        r = np.asarray(cir_r, dtype=float)
        i = np.asarray(cir_i, dtype=float)
    except (TypeError, ValueError):
        return empty
    if len(r) == 0 or len(r) != len(i):
        return empty

    p = np.sqrt(r**2 + i**2)
    n_total = len(p)
    fp_bins = fp_ind / 64.0  # fp_ind is given in units of 1/64 chip

    start = max(0, int(fp_bins) - WINDOW_PRE_BINS)
    end = min(n_total, int(fp_bins) + WINDOW_POST_BINS)
    if end <= start:
        return empty

    p_window = p[start:end]
    t_window_ns = np.arange(start, end) * TS_NS

    # Energy ratio: first-path energy (±1 bin) / total window energy
    fp_idx_local = int(round(fp_bins)) - start
    fp_idx_local = max(0, min(len(p_window) - 1, fp_idx_local))
    fp_energy = np.sum(p_window[max(0, fp_idx_local-1):fp_idx_local+2] ** 2)
    total_energy = np.sum(p_window ** 2)
    energy_ratio = fp_energy / total_energy if total_energy > 0 else float("nan")

    threshold = NOISE_SIGMA_THRESHOLD * stdN
    mask = p_window > threshold
    if mask.sum() < 3:
        out = dict(empty)
        out["energy_ratio_fp"] = energy_ratio
        return out

    p_clean = p_window[mask]
    t_clean_ns = t_window_ns[mask]
    t_fp_ns = fp_bins * TS_NS
    sum_p = np.sum(p_clean)

    mean_excess_delay = np.sum((t_clean_ns - t_fp_ns) * p_clean) / sum_p
    rms_delay_spread = math.sqrt(
        np.sum(p_clean * (t_clean_ns - t_fp_ns - mean_excess_delay) ** 2) / sum_p
    )

    mean_p = np.mean(p_clean)
    std_p = np.std(p_clean)
    if std_p > 0 and len(p_clean) >= 4:
        skewness = float(np.mean(((p_clean - mean_p) / std_p) ** 3))
        kurtosis = float(np.mean(((p_clean - mean_p) / std_p) ** 4) - 3.0)
    else:
        skewness, kurtosis = float("nan"), float("nan")

    return {
        "energy_ratio_fp": energy_ratio,
        "mean_excess_delay_ns": mean_excess_delay,
        "rms_delay_spread_ns": rms_delay_spread,
        "kurtosis_cir": kurtosis,
        "skewness_cir": skewness,
    }


# ══════════════════════════════════════════════════════════════════
# FILENAME METADATA EXTRACTION
# ══════════════════════════════════════════════════════════════════

def parse_filename(fname: str, folder: str):
    """Extracts ancla_id, dist_real_m (calibration) or punto_id (real
    scenario) from the filename."""
    ancla_id, dist_real_m, punto_id = None, None, None

    m_anc = re.search(r"idA(\d+)", fname)
    if m_anc:
        ancla_id = int(m_anc.group(1))

    m_dist = re.search(r"_(\d+\.?\d*)m", fname, re.IGNORECASE)
    if m_dist and folder in CALIBRATION_FOLDERS:
        dist_real_m = float(m_dist.group(1))

    if folder in SCENARIO_FOLDERS:
        m_pid = re.search(r"_id(\d+)", fname)
        if m_pid:
            punto_id = int(m_pid.group(1))

    return ancla_id, dist_real_m, punto_id


# ══════════════════════════════════════════════════════════════════
# MAIN PROCESSING
# ══════════════════════════════════════════════════════════════════

def process_chipset(chipset: str) -> list[dict]:
    rows = []
    base = DATA_ROOT / chipset
    EXPECTED_LENGTH = 1016

    if not base.exists():
        print(f"  [!] {base} does not exist, skipping {chipset}")
        return rows

    for folder_path in sorted(base.iterdir()):
        if not folder_path.is_dir():
            continue
        folder = folder_path.name
        if "antiguas" in folder:
            continue  # explicitly exclude superseded calibration runs

        is_calib = folder in CALIBRATION_FOLDERS
        is_real = folder in SCENARIO_FOLDERS
        if not (is_calib or is_real):
            continue

        files = sorted(folder_path.glob("*.txt"))
        print(f"  {chipset}/{folder}: {len(files)} files")

        for file in files:
            ancla_id, dist_real_m, punto_id = parse_filename(file.name, folder)
            records = read_records(file)

            for reg in records:
                # --- Integrity check ---
                is_valid = (reg.get("CIR_R") is not None and
                            reg.get("CIR_I") is not None and
                            reg.get("fp_ind") is not None and
                            reg.get("stdN") is not None)

                # --- Full-length check ---
                # Confirms whether the arrays have the expected buffer size.
                cir_r = reg.get("CIR_R") if is_valid else None
                cir_i = reg.get("CIR_I") if is_valid else None
                len_r = len(cir_r) if cir_r is not None else 0
                len_i = len(cir_i) if cir_i is not None else 0
                is_full_length = (len_r == EXPECTED_LENGTH and len_i == EXPECTED_LENGTH)

                fp_ind = reg.get("fp_ind") if is_valid else None
                stdN = reg.get("stdN") if is_valid else None

                met = compute_cir_metrics(cir_r, cir_i, fp_ind, stdN)

                amplitude_list, phase_list = compute_amplitude_phase(cir_r, cir_i)
                row = {
                    "is_valid": is_valid,
                    "is_full_length": is_full_length,
                    "chipset": chipset,
                    "carpeta": folder,
                    "escenario": "calibration" if is_calib else folder,
                    "archivo": file.name,
                    "ancla_id": ancla_id,
                    "anc_medicion": reg.get("Anc"),
                    "dist_real_m": dist_real_m,
                    "punto_id": punto_id,
                    "num": reg.get("Num"),
                    "temp": reg.get("temp"),
                    "vol": reg.get("vol"),
                    "fp_pwr_dBm": reg.get("fp_pwr"),
                    "rx_pwr_dBm": reg.get("rx_pwr"),
                    "fp_ind": reg.get("fp_ind"),
                    "Pk_ind": reg.get("Pk_ind"),
                    "Pk_amp": reg.get("Pk_amp"),
                    "N": reg.get("N"),
                    "C": reg.get("C"),
                    "stdN": reg.get("stdN"),
                    **met,
                    "cir_amplitude": json.dumps(amplitude_list) if amplitude_list else None,
                    "cir_phase": json.dumps(phase_list) if phase_list else None,
                }
                rows.append(row)

    return rows


if __name__ == "__main__":
    print("=" * 65)
    print("  Build CIR dataset (CIR-only metrics)")
    print("=" * 65)
    print(f"\nCIR temporal resolution: {TS_NS:.4f} ns/bin")
    print(f"Analysis window: [fp_ind-{WINDOW_PRE_BINS}, "
          f"fp_ind+{WINDOW_POST_BINS}] bins")
    print(f"Noise threshold: {NOISE_SIGMA_THRESHOLD}x stdN")
    print("\nThis script does NOT compute measured distance or ranging.")
    print("It only uses fp_ind, CIR_R, CIR_I -- independent of the")
    print("DS-TWR timestamp-packing firmware.\n")

    all_rows = []
    for chipset in CHIPSETS:
        print(f"\nProcessing {chipset}...")
        all_rows.extend(process_chipset(chipset))

    df = pd.DataFrame(all_rows)
    df.to_csv("cir_dataset.csv", index=False)

    print(f"\n[OK] cir_dataset.csv saved: {len(df)} rows")
    print("\nSummary by chipset/scenario:")
    print(df.groupby(["chipset", "escenario"]).size().to_string())

    print("\nMetric coverage (% non-null):")
    for col in METRIC_FIELDS:
        pct = 100 * df[col].notna().sum() / len(df)
        print(f"  {col:25s}: {pct:5.1f}%")

    print("\nData integrity (full-length CIR):")
    print(df["is_full_length"].value_counts(normalize=True).map('{:.2%}'.format))

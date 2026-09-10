"""build_cir_dataset.py -- parses raw UWB captures into cir_dataset.csv.

Fixes a firmware bug where CIR_I sometimes misses its closing "]".
"""

import json
import math
import re
from pathlib import Path

import numpy as np
import pandas as pd

# === CONSTANTS ===

FS_HZ = 499.2e6
TS_NS = (1.0 / FS_HZ) * 1e9
WINDOW_PRE_BINS = 5
WINDOW_POST_BINS = 50
NOISE_SIGMA_THRESHOLD = 3
EXPECTED_CIR_LENGTH = 1016

DATA_ROOT = Path("data")
CHIPSETS = ["dw1000", "dw3000"]
CALIBRATION_FOLDERS = ["calibration_anc0", "calibration_anchors"]
SCENARIO_FOLDERS = ["lab", "corridor"]

METRIC_FIELDS = [
    "energy_ratio_fp", "mean_excess_delay_ns", "rms_delay_spread_ns",
    "kurtosis_cir", "skewness_cir",
]


# === PARSING ===

def read_records(path):
    """Read one JSON record per line. Repairs two known bad-line cases."""
    records = []
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue

            try:
                records.append(json.loads(line))
                continue
            except json.JSONDecodeError:
                pass

            # case 1: missing "]" before the final "}" (CIR_I bug)
            repaired = re.sub(r"(-?\d+)\}$", r"\1]}", line)
            try:
                records.append(json.loads(repaired))
                continue
            except json.JSONDecodeError:
                pass

            # case 2: line cut off mid-write
            repaired = re.sub(r"(\d+)$", r"\1]}", line)
            if repaired == line:
                repaired = line.rstrip('"') + '"]}'
            try:
                records.append(json.loads(repaired))
            except json.JSONDecodeError:
                pass  # give up on this line

    return records


# === CIR METRICS ===

def compute_amplitude_phase(cir_r, cir_i):
    try:
        r = np.asarray(cir_r, dtype=float)
        i = np.asarray(cir_i, dtype=float)
    except (TypeError, ValueError):
        return None, None
    if len(r) == 0 or len(r) != len(i):
        return None, None

    amplitude = np.sqrt(r ** 2 + i ** 2)
    phase = np.arctan2(i, r)
    amplitude_list = [round(float(x), 2) for x in amplitude]
    phase_list = [round(float(x), 4) for x in phase]
    return amplitude_list, phase_list


def compute_cir_metrics(cir_r, cir_i, fp_ind, std_noise):
    # fp_ind counts in units of 1/64 of a sample -> divide by 64 for the real index
    empty = dict.fromkeys(METRIC_FIELDS, float("nan"))

    if cir_r is None or cir_i is None or fp_ind is None or std_noise is None:
        return empty

    try:
        r = np.asarray(cir_r, dtype=float)
        i = np.asarray(cir_i, dtype=float)
    except (TypeError, ValueError):
        return empty
    if len(r) == 0 or len(r) != len(i):
        return empty

    amplitude = np.sqrt(r ** 2 + i ** 2)
    fp_bins = fp_ind / 64.0

    start = int(fp_bins) - WINDOW_PRE_BINS
    end = int(fp_bins) + WINDOW_POST_BINS
    start = max(0, start)
    end = min(len(amplitude), end)
    if end <= start:
        return empty

    window = amplitude[start:end]
    t_window_ns = np.arange(start, end) * TS_NS

    fp_idx_local = int(round(fp_bins)) - start
    fp_idx_local = max(0, min(len(window) - 1, fp_idx_local))
    fp_energy = np.sum(window[max(0, fp_idx_local - 2):fp_idx_local + 3] ** 2)
    total_energy = np.sum(window ** 2)
    energy_ratio = fp_energy / total_energy if total_energy > 0 else float("nan")

    noise_mask = window > NOISE_SIGMA_THRESHOLD * std_noise
    if noise_mask.sum() < 3:
        result = dict(empty)
        result["energy_ratio_fp"] = energy_ratio
        return result

    amp_clean = window[noise_mask]
    t_clean_ns = t_window_ns[noise_mask]
    t_fp_ns = fp_bins * TS_NS
    total_amp = np.sum(amp_clean)

    mean_excess_delay = np.sum((t_clean_ns - t_fp_ns) * amp_clean) / total_amp
    rms_delay_spread = math.sqrt(
        np.sum(amp_clean * (t_clean_ns - t_fp_ns - mean_excess_delay) ** 2) / total_amp
    )

    mean_amp = np.mean(amp_clean)
    std_amp = np.std(amp_clean)
    if std_amp > 0 and len(amp_clean) >= 4:
        skewness = float(np.mean(((amp_clean - mean_amp) / std_amp) ** 3))
        kurtosis = float(np.mean(((amp_clean - mean_amp) / std_amp) ** 4) - 3.0)
    else:
        skewness = float("nan")
        kurtosis = float("nan")

    return {
        "energy_ratio_fp": energy_ratio,
        "mean_excess_delay_ns": mean_excess_delay,
        "rms_delay_spread_ns": rms_delay_spread,
        "kurtosis_cir": kurtosis,
        "skewness_cir": skewness,
    }


# === FILENAME METADATA ===

def parse_filename(fname, folder):
    anchor_id = None
    dist_real_m = None
    point_id = None

    m_anchor = re.search(r"idA(\d+)", fname)
    if m_anchor:
        anchor_id = int(m_anchor.group(1))

    if folder in CALIBRATION_FOLDERS:
        m_dist = re.search(r"_(\d+\.?\d*)m", fname, re.IGNORECASE)
        if m_dist:
            dist_real_m = float(m_dist.group(1))

    if folder in SCENARIO_FOLDERS:
        m_point = re.search(r"_id(\d+)", fname)
        if m_point:
            point_id = int(m_point.group(1))

    return anchor_id, dist_real_m, point_id


# === MAIN PROCESSING ===

def process_chipset(chipset):
    rows = []
    base = DATA_ROOT / chipset

    if not base.exists():
        print(f"  [!] {base} does not exist, skipping {chipset}")
        return rows

    for folder_path in sorted(base.iterdir()):
        if not folder_path.is_dir():
            continue

        folder = folder_path.name
        if "old" in folder:
            continue
        if folder not in CALIBRATION_FOLDERS and folder not in SCENARIO_FOLDERS:
            continue

        files = sorted(folder_path.glob("*.txt"))
        print(f"  {chipset}/{folder}: {len(files)} files")

        for file in files:
            anchor_id, dist_real_m, point_id = parse_filename(file.name, folder)

            for record in read_records(file):
                is_valid = (
                    record.get("CIR_R") is not None
                    and record.get("CIR_I") is not None
                    and record.get("fp_ind") is not None
                    and record.get("stdN") is not None
                )

                cir_r = record.get("CIR_R") if is_valid else None
                cir_i = record.get("CIR_I") if is_valid else None
                is_full_length = (
                    len(cir_r or []) == EXPECTED_CIR_LENGTH
                    and len(cir_i or []) == EXPECTED_CIR_LENGTH
                )

                metrics = compute_cir_metrics(
                    cir_r, cir_i, record.get("fp_ind"), record.get("stdN")
                )
                amplitude_list, phase_list = compute_amplitude_phase(cir_r, cir_i)

                row = {
                    "is_valid": is_valid,
                    "is_full_length": is_full_length,
                    "chipset": chipset,
                    "carpeta": folder,
                    "escenario": "calibration" if folder in CALIBRATION_FOLDERS else folder,
                    "archivo": file.name,
                    "ancla_id": anchor_id,
                    "anc_medicion": record.get("Anc"),
                    "dist_real_m": dist_real_m,
                    "punto_id": point_id,
                    "num": record.get("Num"),
                    "temp": record.get("temp"),
                    "vol": record.get("vol"),
                    "fp_pwr_dBm": record.get("fp_pwr"),
                    "rx_pwr_dBm": record.get("rx_pwr"),
                    "fp_ind": record.get("fp_ind"),
                    "Pk_ind": record.get("Pk_ind"),
                    "Pk_amp": record.get("Pk_amp"),
                    "N": record.get("N"),
                    "C": record.get("C"),
                    "stdN": record.get("stdN"),
                    "cir_amplitude": json.dumps(amplitude_list) if amplitude_list else None,
                    "cir_phase": json.dumps(phase_list) if phase_list else None,
                }
                row.update(metrics)
                rows.append(row)

    return rows


# === ENTRY POINT ===

if __name__ == "__main__":
    all_rows = []
    for chipset in CHIPSETS:
        print(f"Processing {chipset}...")
        all_rows.extend(process_chipset(chipset))

    df = pd.DataFrame(all_rows)
    df.to_csv("cir_dataset.csv", index=False)

    print(f"\ncir_dataset.csv saved: {len(df)} rows")
    print(df.groupby(["chipset", "escenario"]).size().to_string())
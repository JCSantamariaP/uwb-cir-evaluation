"""build_cir_dataset.py — builds cir_dataset.csv from raw captures (Section II-B)

Uses only fp_ind, CIR_R, CIR_I -- no ranging/ToF, independent of the
DW3000 timestamp-packing firmware issue.

Expects:
  data/dw1000/{calibration_anc0,calibration_anchors,lab,corridor}/*.txt
  data/dw3000/(same, folders with "_old" are excluded)
  data/GroundTruth/{anchors.csv,points.csv}
"""

import json
import math
import re
import numpy as np
import pandas as pd
from pathlib import Path

FS = 499.2e6                   # Hz, CIR sampling frequency
TS_NS = (1.0 / FS) * 1e9        # ~2.0032 ns per bin
WINDOW_PRE_BINS = 5
WINDOW_POST_BINS = 75            # ~150 ns after the first path
NOISE_SIGMA_THRESHOLD = 3

DATA_ROOT = Path("data")
CHIPSETS = ["dw1000", "dw3000"]
CALIBRATION_FOLDERS = ["calibration_anc0", "calibration_anchors"]
SCENARIO_FOLDERS = ["lab", "corridor"]

METRIC_FIELDS = [
    "energy_ratio_fp", "mean_excess_delay_ns",
    "rms_delay_spread_ns", "kurtosis_cir", "skewness_cir",
]


def read_records(path):
    """Parses one JSON object per line, with a light repair attempt
    for lines truncated mid-write."""
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
            repaired = re.sub(r"(\d+)$", r"\1]}", line)
            if repaired == line:
                repaired = line.rstrip('"') + '"]}'
            try:
                records.append(json.loads(repaired))
            except json.JSONDecodeError:
                continue
    return records


def compute_amplitude_phase(cir_r, cir_i):
    try:
        r = np.asarray(cir_r, dtype=float)
        i = np.asarray(cir_i, dtype=float)
    except (TypeError, ValueError):
        return None, None
    if len(r) == 0 or len(r) != len(i):
        return None, None
    amplitude = np.sqrt(r**2 + i**2)
    phase = np.arctan2(i, r)
    return [round(float(x), 2) for x in amplitude], [round(float(x), 4) for x in phase]


def compute_cir_metrics(cir_r, cir_i, fp_ind, stdN):
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
    fp_bins = fp_ind / 64.0  # fp_ind is in units of 1/64 chip

    start = max(0, int(fp_bins) - WINDOW_PRE_BINS)
    end = min(len(p), int(fp_bins) + WINDOW_POST_BINS)
    if end <= start:
        return empty

    p_window = p[start:end]
    t_window_ns = np.arange(start, end) * TS_NS

    fp_idx_local = max(0, min(len(p_window) - 1, int(round(fp_bins)) - start))
    fp_energy = np.sum(p_window[max(0, fp_idx_local-1):fp_idx_local+2] ** 2)
    total_energy = np.sum(p_window ** 2)
    energy_ratio = fp_energy / total_energy if total_energy > 0 else float("nan")

    mask = p_window > NOISE_SIGMA_THRESHOLD * stdN
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


def parse_filename(fname, folder):
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


def process_chipset(chipset):
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
        if "old" in folder:
            continue  # excludes superseded calibration runs
        if folder not in CALIBRATION_FOLDERS + SCENARIO_FOLDERS:
            continue

        files = sorted(folder_path.glob("*.txt"))
        print(f"  {chipset}/{folder}: {len(files)} files")

        for file in files:
            ancla_id, dist_real_m, punto_id = parse_filename(file.name, folder)
            for reg in read_records(file):
                is_valid = (reg.get("CIR_R") is not None and reg.get("CIR_I") is not None
                            and reg.get("fp_ind") is not None and reg.get("stdN") is not None)
                cir_r = reg.get("CIR_R") if is_valid else None
                cir_i = reg.get("CIR_I") if is_valid else None
                is_full_length = (len(cir_r or []) == EXPECTED_LENGTH and
                                   len(cir_i or []) == EXPECTED_LENGTH)

                met = compute_cir_metrics(cir_r, cir_i, reg.get("fp_ind"), reg.get("stdN"))
                amplitude_list, phase_list = compute_amplitude_phase(cir_r, cir_i)

                rows.append({
                    "is_valid": is_valid,
                    "is_full_length": is_full_length,
                    "chipset": chipset,
                    "carpeta": folder,
                    "escenario": "calibration" if folder in CALIBRATION_FOLDERS else folder,
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
                })
    return rows


if __name__ == "__main__":
    all_rows = []
    for chipset in CHIPSETS:
        print(f"Processing {chipset}...")
        all_rows.extend(process_chipset(chipset))

    df = pd.DataFrame(all_rows)
    df.to_csv("cir_dataset.csv", index=False)
    print(f"\n cir_dataset.csv saved: {len(df)} rows")
    print(df.groupby(["chipset", "escenario"]).size().to_string())
# UWB DW1000 vs DW3000 — CIR and Coverage Analysis

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.21099647.svg)](https://doi.org/10.5281/zenodo.21099647)
![Python Version](https://img.shields.io/badge/python-3.10%2B-blue.svg)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)

This repository contains the code for the paper "**Performance Evaluation of UWB in
Indoor Environments: CIR and Coverage Analysis**" (submitted to IEEE SENSORS 2026). The
paper compares the DW1000 and DW3000 UWB transceivers in laboratory and corridor
environments, analyzing Channel Impulse Response (CIR) morphology (RMS Delay Spread,
Mean Excess Delay) to evaluate whether transceiver-specific differences affect channel
signature consistency. Results show CIR morphology is predominantly determined by
environmental topology, with negligible hardware impact in diffuse multipath, while the
DW3000 achieves superior coverage robustness at longer range. Full results are reported
in the paper.

---

## :file_folder: Repository Structure

- [`build_cir_dataset.py`](code/build_cir_dataset.py): Builds `cir_dataset.csv` from the
  raw CIR captures (Section II-B).
- [`fig1_power_energy_vs_distance.py`](code/fig1_power_energy_vs_distance.py): Fig. 1 —
  First-path power & Energy Ratio vs. distance.
- [`cross_anchor_consistency.py`](code/cross_anchor_consistency.py): Cross-anchor
  consistency figures and stats (Section III-A).
- [`fig2_cir_envelope.py`](code/fig2_cir_envelope.py): Fig. 2 — normalized CIR envelope.
- [`fig3_channel_fingerprint.py`](code/fig3_channel_fingerprint.py): Fig. 3 — Mean Excess
  Delay vs. RMS Delay Spread.
- [`mannwhitney_pooled_test.py`](code/mannwhitney_pooled_test.py): Pooled Mann-Whitney
  tests (Section III-B).
- [`table1_anchor_stratified_test.py`](code/table1_anchor_stratified_test.py): Table I —
  anchor-stratified paired test.
- [`table2_coverage_classification.py`](code/table2_coverage_classification.py): Table II
  — corridor coverage classification.
- [`download_data.py`](download_data.py): Downloads the dataset from the Zenodo record.

---

## :rocket: Workflow

> [!IMPORTANT]
> All scripts must be executed from the **root directory** of this repository.

### 1. Environment Setup

```bash
git clone https://github.com/<your-username>/<repo-name>.git
cd <repo-name>

python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Data Preparation

```bash
python3 download_data.py            # downloads cir_dataset.csv and data_raw.zip
```

This fetches the files directly from the [Zenodo record](https://doi.org/10.5281/zenodo.21099647).
`build_cir_dataset.py` additionally needs the raw data unzipped into `data/` (from
`data_raw.zip`); the rest of the scripts only need `cir_dataset.csv` in the repo root.

### 3. Full Pipeline

```bash
python3 code/build_cir_dataset.py                  # optional: rebuild cir_dataset.csv
python3 code/fig1_power_energy_vs_distance.py
python3 code/cross_anchor_consistency.py
python3 code/fig2_cir_envelope.py
python3 code/fig3_channel_fingerprint.py
python3 code/mannwhitney_pooled_test.py
python3 code/table1_anchor_stratified_test.py
python3 code/table2_coverage_classification.py
```

---

## :memo: Citation

If you use this code or dataset, please cite:

Original Paper:
> J.C. Santamaria-Pedron, R. Berkvens, C. Reaño, J.J. Perez-Solano, J. Torres-Sospedra,
> "Performance Evaluation of UWB in Indoor Environments: CIR and Coverage Analysis,"
> submitted to IEEE SENSORS 2026.

Dataset (includes this code):
> J.C. Santamaria Pedron, R. Berkvens, C. Reaño, J.J. Perez Solano, J. Torres-Sospedra,
> "Reproducible package for 'Performance evaluation of UWB in indoor environments: CIR
> and coverage analysis'," Jul. 2026. DOI: 10.5281/zenodo.21099647.

---

## :page_facing_up: License

Code: this project is licensed under the [MIT License](LICENSE). The dataset (Zenodo)
has its own license (CC-BY 4.0), specified in that record.

# Reproducible Package for 'Performance Evaluation of UWB in Indoor Environments: CIR and Coverage Analysis'

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.21099647.svg)](https://doi.org/10.5281/zenodo.21099647)
![Python Version](https://img.shields.io/badge/python-3.10%2B-blue.svg)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)

This repository contains the code for the paper "**Performance Evaluation of UWB in Indoor Environments: CIR and Coverage Analysis**", submitted to IEEE SENSORS 2026. The paper presents a controlled comparison of the DW1000 and DW3000 UWB transceivers in laboratory and corridor environments, analyzing Channel Impulse Response (CIR) morphology to evaluate whether transceiver-specific differences affect channel signature consistency and localization model transferability.

<p align="center">
  <img src="fig/fig3_channel_fingerprint.pdf" width="70%">
  <br><i>Fig. 1. Channel morphology fingerprint: Mean Excess Delay vs. RMS Delay Spread for DW1000 and DW3000.</i>
</p>

---

## :file_folder: Repository Structure

- [`download_data.py`](download_data.py): Downloads the complete dataset from the Zenodo record.
- [`code/build_cir_dataset.py`](code/build_cir_dataset.py): Processes raw CIR captures into `cir_dataset.csv` (Section II-B).
- [`code/fig1_power_energy_vs_distance.py`](code/fig1_power_energy_vs_distance.py): Analyzes First-path power and Energy Ratio trends.
- [`code/cross_anchor_consistency.py`](code/cross_anchor_consistency.py): Quantifies baseline hardware variability across anchors.
- [`code/fig2_cir_envelope.py`](code/fig2_cir_envelope.py): Visualizes normalized CIR envelopes per chipset/environment.
- [`code/fig3_channel_fingerprint.py`](code/fig3_channel_fingerprint.py): Generates the 2D morphological fingerprint plot.
- [`code/mannwhitney_pooled_test.py`](code/mannwhitney_pooled_test.py): Performs pooled statistical tests to assess hardware vs. environmental impact.
- [`code/table1_anchor_stratified_test.py`](code/table1_anchor_stratified_test.py): Anchor-stratified paired comparisons.
- [`code/table2_coverage_classification.py`](code/table2_coverage_classification.py): Corridor coverage summary and link-budget analysis.

---

## :rocket: Workflow

> [!IMPORTANT]
> All scripts must be executed from the **root directory** of this repository.

### 1. Environment Setup

```bash
git clone [https://github.com/JCSantamariaP/uwb-cir-evaluation.git](https://github.com/JCSantamariaP/uwb-cir-evaluation.git)
cd uwb-cir-evaluation

python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
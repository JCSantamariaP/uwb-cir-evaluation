# UWB DW1000 vs DW3000 — CIR Analysis Code

Code accompanying:

> J. C. Santamaria-Pedron, R. Berkvens, C. Reaño, J. J. Perez-Solano, J. Torres-Sospedra,
> **"Performance Evaluation of UWB in Indoor Environments: CIR and Coverage Analysis,"**
> IEEE SENSORS 2026.

This repository contains only the scripts needed to reproduce the paper's figures and
tables. The dataset (raw captures and the processed `cir_dataset.csv`) is archived
separately on Zenodo:

**Dataset DOI: [10.5281/zenodo.21099647](https://doi.org/10.5281/zenodo.21099647)**

## Scripts

| Script | Produces |
|---|---|
| `build_cir_dataset.py` | `cir_dataset.csv`, from the raw captures (Section II-B) |
| `fig1_power_energy_vs_distance.py` | Fig. 1 — FP power & Energy Ratio vs. distance |
| `cross_anchor_consistency.py` | Cross-anchor consistency figures & stats (Section III-A) |
| `fig2_cir_envelope.py` | Fig. 2 — normalized CIR envelope |
| `fig3_channel_fingerprint.py` | Fig. 3 — Mean Excess Delay vs. RMS Delay Spread |
| `mannwhitney_pooled_test.py` | Pooled Mann-Whitney tests (Section III-B) |
| `table1_anchor_stratified_test.py` | Table I — anchor-stratified paired test |
| `table2_coverage_classification.py` | Table II — corridor coverage classification |

## Getting the data

```bash
pip install -r requirements.txt
python download_data.py            # downloads cir_dataset.csv and data_raw.zip
```

This fetches the files directly from the [Zenodo record](https://doi.org/10.5281/zenodo.21099647).
`build_cir_dataset.py` additionally needs the raw data unzipped into `data/` (from
`data_raw.zip`); the rest of the scripts only need `cir_dataset.csv` in the repo root.

## Running

```bash
python build_cir_dataset.py                  # optional: rebuild cir_dataset.csv from raw data
python fig1_power_energy_vs_distance.py
python cross_anchor_consistency.py
python fig2_cir_envelope.py
python fig3_channel_fingerprint.py
python mannwhitney_pooled_test.py
python table1_anchor_stratified_test.py
python table2_coverage_classification.py
```

## Citation

```
Santamaria-Pedron, J.C., Berkvens, R., Reaño, C., Perez-Solano, J.J., Torres-Sospedra, J.
"Performance Evaluation of UWB in Indoor Environments: CIR and Coverage Analysis."
IEEE SENSORS 2026.

Dataset: https://doi.org/10.5281/zenodo.21099647
```

## License

MIT — see `LICENSE`.

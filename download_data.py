#!/usr/bin/env python3
"""download_data.py — fetches the dataset from the Zenodo record

Usage:
    python download_data.py            # downloads cir_dataset.csv and data_raw.zip
    python download_data.py --only csv # downloads only cir_dataset.csv
"""
import argparse
import json
import sys
from pathlib import Path
from urllib.request import urlopen, urlretrieve

ZENODO_RECORD_ID = "21099647"  # https://doi.org/10.5281/zenodo.21099647
ZENODO_API = f"https://zenodo.org/api/records/{ZENODO_RECORD_ID}"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--only", choices=["csv", "raw", "all"], default="all")
    args = parser.parse_args()

    name_filter = {"csv": "cir_dataset.csv", "raw": "data.zip", "all": None}[args.only]

    with urlopen(ZENODO_API) as resp:
        files = json.load(resp).get("files", [])

    if not files:
        print(f"No files found. Download manually from https://doi.org/10.5281/zenodo.{ZENODO_RECORD_ID}")
        sys.exit(1)

    for f in files:
        if name_filter and f["key"] != name_filter:
            continue
        print(f"Downloading {f['key']} ...")
        urlretrieve(f["links"]["self"], Path(f["key"]))
        print(f"  -> saved to {f['key']}")

    print("Done.")


if __name__ == "__main__":
    main()
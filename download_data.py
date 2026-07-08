#!/usr/bin/env python3
"""
Downloads the dataset (cir_dataset.csv and raw data) from the Zenodo record
associated with this repository, using Zenodo's public REST API.

Usage:
    python download_data.py            # downloads cir_dataset.csv and data_raw.zip
    python download_data.py --only csv # downloads only cir_dataset.csv
"""
import argparse
import json
import sys
from pathlib import Path
from urllib.request import urlopen, urlretrieve

# Zenodo record for the dataset referenced in the paper:
# https://doi.org/10.5281/zenodo.21099647
ZENODO_RECORD_ID = "21099647"
ZENODO_API = f"https://zenodo.org/api/records/{ZENODO_RECORD_ID}"


def get_file_list():
    with urlopen(ZENODO_API) as resp:
        record = json.load(resp)
    return record.get("files", [])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--only",
        choices=["csv", "raw", "all"],
        default="all",
        help="Which asset to download (default: all)",
    )
    args = parser.parse_args()

    name_filter = {
        "csv": "cir_dataset.csv",
        "raw": "data_raw.zip",
        "all": None,
    }[args.only]

    files = get_file_list()
    if not files:
        print("No files found in the Zenodo record. Check ZENODO_RECORD_ID or "
              f"download manually from https://doi.org/10.5281/zenodo.{ZENODO_RECORD_ID}")
        sys.exit(1)

    for f in files:
        fname = f["key"]
        if name_filter and fname != name_filter:
            continue
        url = f["links"]["self"]
        dest = Path(fname)
        print(f"Downloading {fname} ...")
        urlretrieve(url, dest)
        print(f"  -> saved to {dest}")

    print("Done.")


if __name__ == "__main__":
    main()

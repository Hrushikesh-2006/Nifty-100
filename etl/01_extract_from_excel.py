"""
ETL Script 01 — Extract from Excel files
Reads all 7 source Excel files and saves them as clean CSVs in data/raw/
"""

import pandas as pd
import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_DIR  = os.path.join(BASE_DIR, "data", "raw")
OUT_DIR  = os.path.join(BASE_DIR, "data", "raw")  # CSVs alongside xlsx

TABLE_MAP = {
    "companies":     "companies.xlsx",
    "analysis":      "analysis.xlsx",
    "balancesheet":  "balancesheet.xlsx",
    "profitandloss": "profitandloss.xlsx",
    "cashflow":      "cashflow.xlsx",
    "prosandcons":   "prosandcons.xlsx",
    "documents":     "documents.xlsx",
}

def read_excel_table(filepath: str) -> pd.DataFrame:
    """
    All source Excel files have a metadata header row 0 (merged title cell),
    and row 1 contains actual column names. Data starts from row 2.
    """
    # Read skipping the banner row; row index 0 becomes actual columns
    df = pd.read_excel(filepath, header=1)
    # Drop completely empty rows/cols
    df.dropna(how="all", inplace=True)
    df.dropna(axis=1, how="all", inplace=True)
    return df


def extract_all():
    print("=" * 60)
    print("ETL Step 01 -- Extract from Excel -> CSV")
    print("=" * 60)

    for name, filename in TABLE_MAP.items():
        src = os.path.join(RAW_DIR, filename)
        dst = os.path.join(OUT_DIR, f"{name}.csv")

        if not os.path.exists(src):
            print(f"  [SKIP] {filename} not found at {src}")
            continue

        df = read_excel_table(src)
        df.to_csv(dst, index=False, encoding="utf-8-sig")

        print(f"  [{name}]  rows={len(df)}  cols={list(df.columns)}")
        print(f"           -> saved to {dst}")

    print("\nExtraction complete.")


if __name__ == "__main__":
    extract_all()

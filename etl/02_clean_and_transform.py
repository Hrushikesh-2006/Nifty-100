"""
ETL Script 02 — Clean & Transform
Reads raw CSVs, standardises year formats, parses analysis strings,
computes derived metrics, and saves to data/clean/.
"""

import pandas as pd
import numpy as np
import re
import os
import sys

BASE_DIR  = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_DIR   = os.path.join(BASE_DIR, "data", "raw")
CLEAN_DIR = os.path.join(BASE_DIR, "data", "clean")
os.makedirs(CLEAN_DIR, exist_ok=True)

# ─────────────────────────────────────────────
# SECTOR MAPPING  (manual classification)
# ─────────────────────────────────────────────
SECTOR_MAP = {
    "ABB":        "Capital Goods",
    "ADANIENSOL": "Energy",
    "ADANIENT":   "Diversified",
    "ADANIGREEN": "Energy",
    "ADANIPORTS": "Infrastructure",
    "ADANIPOWER": "Power",
    "AMBUJACEM":  "Cement",
    "APOLLOHOSP": "Healthcare",
    "ASIANPAINT": "Paints",
    "ATGL":       "Energy",
    "AXISBANK":   "Banking",
    "BAJAJ-AUTO": "Auto",
    "BAJAJFINSV": "Finance",
    "BAJFINANCE": "NBFC",
    "BANKBARODA": "Banking",
    "BEL":        "Defence",
    "BHEL":       "Capital Goods",
    "BPCL":       "Oil & Gas",
    "BRITANNIA":  "FMCG",
    "CHOLAFIN":   "NBFC",
    "CIPLA":      "Pharma",
    "COALINDIA":  "Mining",
    "DABUR":      "FMCG",
    "DLF":        "Real Estate",
    "DRREDDY":    "Pharma",
    "EICHERMOT":  "Auto",
    "GAIL":       "Oil & Gas",
    "GODREJCP":   "FMCG",
    "GRASIM":     "Diversified",
    "HCLTECH":    "IT",
    "HDFCBANK":   "Banking",
    "HDFCLIFE":   "Insurance",
    "HEROMOTOCO": "Auto",
    "HINDALCO":   "Metals",
    "HINDUNILVR": "FMCG",
    "ICICIBANK":  "Banking",
    "ICICIGI":    "Insurance",
    "ICICIPRULI": "Insurance",
    "INDUSINDBK": "Banking",
    "INDUSTOWER": "Telecom",
    "INFY":       "IT",
    "IOC":        "Oil & Gas",
    "IRCTC":      "Travel",
    "ITC":        "FMCG",
    "JIOFIN":     "Finance",
    "JSWSTEEL":   "Metals",
    "KOTAKBANK":  "Banking",
    "LT":         "Capital Goods",
    "LTIM":       "IT",
    "LTIMINDTRE": "IT",
    "M&M":        "Auto",
    "MARUTI":     "Auto",
    "MARICO":     "FMCG",
    "MOTHERSON":  "Auto Ancillary",
    "MPHASIS":    "IT",
    "NAUKRI":     "Internet",
    "NESTLEIND":  "FMCG",
    "NTPC":       "Power",
    "ONGC":       "Oil & Gas",
    "PAGEIND":    "Textile",
    "PIDILITIND": "Chemicals",
    "PIIND":      "Chemicals",
    "PNB":        "Banking",
    "POLYCAB":    "Capital Goods",
    "POWERGRID":  "Power",
    "RECLTD":     "Finance",
    "RELIANCE":   "Diversified",
    "SBICARD":    "Finance",
    "SBILIFE":    "Insurance",
    "SHREECEM":   "Cement",
    "SIEMENS":    "Capital Goods",
    "SRF":        "Chemicals",
    "SUNPHARMA":  "Pharma",
    "TATACONSUM": "FMCG",
    "TATAMOTORS": "Auto",
    "TATAPOWER":  "Power",
    "TATASTEEL":  "Metals",
    "TCS":        "IT",
    "TECHM":      "IT",
    "TITAN":      "Consumer Goods",
    "TORNTPHARM": "Pharma",
    "TRENT":      "Retail",
    "ULTRACEMCO": "Cement",
    "UNIONBANK":  "Banking",
    "VEDL":       "Metals",
    "WIPRO":      "IT",
    "ZOMATO":     "Internet",
    "ZYDUSLIFE":  "Pharma",
}

# Month → sort weight (so Mar is fiscal year-end)
MONTH_ORDER = {
    "Jan": 1, "Feb": 2, "Mar": 3, "Apr": 4,
    "May": 5, "Jun": 6, "Jul": 7, "Aug": 8,
    "Sep": 9, "Oct": 10, "Nov": 11, "Dec": 12,
}


# ─────────────────────────────────────────────
# HELPER: standardise year strings
# ─────────────────────────────────────────────
def standardise_year(val):
    """
    'Mar 2024' → ('Mar 2024', 2024, 3, 20240)
    'Dec 2023' → ('Dec 2023', 2024, 12, 20231)   # Dec is FY+1
    'TTM'  → ('TTM', None, None, 99999)
    """
    if pd.isna(val):
        return np.nan, np.nan, np.nan, np.nan

    val = str(val).strip()

    if val in ("TTM", "ttm"):
        return "TTM", np.nan, np.nan, 99999

    # Pattern: "Mon YYYY"
    m = re.match(r"([A-Za-z]{3})\s*(\d{4})", val)
    if m:
        mon, yr = m.group(1).capitalize(), int(m.group(2))
        mo_num = MONTH_ORDER.get(mon, 3)
        # fiscal year: Mar YYYY → FY YYYY; Dec YYYY → FY YYYY+1
        fiscal = yr if mo_num >= 4 else yr + 1
        sort_order = yr * 100 + mo_num
        return f"{mon} {yr}", fiscal, mo_num, sort_order

    # Pattern: "Mon-YY"
    m2 = re.match(r"([A-Za-z]{3})-(\d{2})$", val)
    if m2:
        mon = m2.group(1).capitalize()
        yr  = 2000 + int(m2.group(2))
        mo_num = MONTH_ORDER.get(mon, 3)
        fiscal = yr if mo_num >= 4 else yr + 1
        sort_order = yr * 100 + mo_num
        return f"{mon} {yr}", fiscal, mo_num, sort_order

    return val, np.nan, np.nan, 99998  # unknown format


def add_year_cols(df):
    results = df["year"].apply(standardise_year)
    df["year_label"]  = results.apply(lambda x: x[0])
    df["fiscal_year"] = results.apply(lambda x: x[1])
    df["month_num"]   = results.apply(lambda x: x[2])
    df["sort_order"]  = results.apply(lambda x: x[3])
    return df


# ─────────────────────────────────────────────
# HELPER: parse analysis strings like "10 Years: 21%"
# ─────────────────────────────────────────────
PERIOD_MAP = {
    "10 years": "10Y", "10years": "10Y",
    "5 years":  "5Y",  "5years":  "5Y",
    "3 years":  "3Y",  "3years":  "3Y",
    "ttm":      "TTM",
    "1 year":   "1Y",  "1year":   "1Y",
    "last year": "1Y",
}

def parse_growth_field(s):
    """
    '10 Years: 11%' → ('10Y', 11.0)
    '5 Years: -3%'  → ('5Y', -3.0)
    """
    if pd.isna(s):
        return np.nan, np.nan
    s = str(s).strip()
    # get period
    period = np.nan
    for key, label in PERIOD_MAP.items():
        if key in s.lower():
            period = label
            break
    # get number
    num_m = re.search(r"(-?\d+\.?\d*)\s*%", s)
    value = float(num_m.group(1)) if num_m else np.nan
    return period, value


# ─────────────────────────────────────────────
# CLEAN: companies
# ─────────────────────────────────────────────
def clean_companies():
    df = pd.read_csv(os.path.join(RAW_DIR, "companies.csv"))
    df["company_name"] = df["company_name"].astype(str).str.replace(r"[\r\n]+", " ", regex=True).str.strip()
    df["about_company"] = df["about_company"].astype(str).str.replace(r"[\r\n]+", " ", regex=True).str.strip()
    df.rename(columns={"id": "symbol"}, inplace=True)
    df["sector"] = df["symbol"].map(SECTOR_MAP).fillna("Others")
    df.to_csv(os.path.join(CLEAN_DIR, "companies.csv"), index=False, encoding="utf-8-sig")
    print(f"  [companies]  {len(df)} rows")
    return df


# ─────────────────────────────────────────────
# CLEAN: analysis
# ─────────────────────────────────────────────
def clean_analysis():
    df = pd.read_csv(os.path.join(RAW_DIR, "analysis.csv"))
    df.rename(columns={"company_id": "symbol"}, inplace=True)

    rows = []
    for _, row in df.iterrows():
        sym = row["symbol"]
        for col in ["compounded_sales_growth", "compounded_profit_growth", "stock_price_cagr", "roe"]:
            period, value = parse_growth_field(row[col])
            rows.append({
                "symbol":       sym,
                "metric":       col,
                "period_label": period,
                "value_pct":    value,
            })

    clean_df = pd.DataFrame(rows).dropna(subset=["period_label"])
    clean_df.to_csv(os.path.join(CLEAN_DIR, "analysis.csv"), index=False, encoding="utf-8-sig")
    print(f"  [analysis]  {len(clean_df)} rows (unpivoted)")
    return clean_df


# ─────────────────────────────────────────────
# CLEAN: balance sheet
# ─────────────────────────────────────────────
def clean_balancesheet():
    df = pd.read_csv(os.path.join(RAW_DIR, "balancesheet.csv"))
    df.rename(columns={"company_id": "symbol", "other_asset": "other_assets"}, inplace=True)
    df = add_year_cols(df)

    num_cols = ["equity_capital","reserves","borrowings","other_liabilities",
                "total_liabilities","fixed_assets","cwip","investments",
                "other_assets","total_assets"]
    for c in num_cols:
        df[c] = pd.to_numeric(df[c], errors="coerce")

    # Computed columns
    df["debt_to_equity"]  = df["borrowings"] / (df["equity_capital"] + df["reserves"]).replace(0, np.nan)
    df["equity_ratio"]    = (df["equity_capital"] + df["reserves"]) / df["total_assets"].replace(0, np.nan)

    df.replace([np.inf, -np.inf], np.nan, inplace=True)
    df.to_csv(os.path.join(CLEAN_DIR, "balancesheet.csv"), index=False, encoding="utf-8-sig")
    print(f"  [balancesheet]  {len(df)} rows")
    return df


# ─────────────────────────────────────────────
# CLEAN: profit & loss
# ─────────────────────────────────────────────
def clean_profitandloss():
    df = pd.read_csv(os.path.join(RAW_DIR, "profitandloss.csv"))
    df.rename(columns={"company_id": "symbol", "opm_percentage": "opm_pct",
                        "tax_percentage": "tax_pct", "dividend_payout": "dividend_payout_pct"}, inplace=True)
    df = add_year_cols(df)

    num_cols = ["sales","expenses","operating_profit","opm_pct","other_income",
                "interest","depreciation","profit_before_tax","tax_pct","net_profit","eps","dividend_payout_pct"]
    for c in num_cols:
        df[c] = pd.to_numeric(df[c], errors="coerce")

    # Computed columns
    df["net_profit_margin_pct"] = (df["net_profit"] / df["sales"].replace(0, np.nan)) * 100
    df["expense_ratio_pct"]     = (df["expenses"]   / df["sales"].replace(0, np.nan)) * 100
    df["interest_coverage"]     = df["operating_profit"] / df["interest"].replace(0, np.nan)

    df.replace([np.inf, -np.inf], np.nan, inplace=True)
    df.to_csv(os.path.join(CLEAN_DIR, "profitandloss.csv"), index=False, encoding="utf-8-sig")
    print(f"  [profitandloss]  {len(df)} rows")
    return df


# ─────────────────────────────────────────────
# CLEAN: cash flow
# ─────────────────────────────────────────────
def clean_cashflow():
    df = pd.read_csv(os.path.join(RAW_DIR, "cashflow.csv"))
    df.rename(columns={"company_id": "symbol"}, inplace=True)
    df = add_year_cols(df)

    num_cols = ["operating_activity","investing_activity","financing_activity","net_cash_flow"]
    for c in num_cols:
        df[c] = pd.to_numeric(df[c], errors="coerce")

    df["free_cash_flow"] = df["operating_activity"] + df["investing_activity"]

    df.replace([np.inf, -np.inf], np.nan, inplace=True)
    df.to_csv(os.path.join(CLEAN_DIR, "cashflow.csv"), index=False, encoding="utf-8-sig")
    print(f"  [cashflow]  {len(df)} rows")
    return df


# ─────────────────────────────────────────────
# CLEAN: pros & cons
# ─────────────────────────────────────────────
def clean_prosandcons():
    df = pd.read_csv(os.path.join(RAW_DIR, "prosandcons.csv"))
    df.rename(columns={"company_id": "symbol"}, inplace=True)
    rows = []
    for _, row in df.iterrows():
        if pd.notna(row["pros"]) and str(row["pros"]).strip() not in ("", "nan"):
            rows.append({"symbol": row["symbol"], "is_pro": True,  "text": str(row["pros"]).strip()})
        if pd.notna(row["cons"]) and str(row["cons"]).strip() not in ("", "nan"):
            rows.append({"symbol": row["symbol"], "is_pro": False, "text": str(row["cons"]).strip()})
    clean_df = pd.DataFrame(rows)
    clean_df.to_csv(os.path.join(CLEAN_DIR, "prosandcons.csv"), index=False, encoding="utf-8-sig")
    print(f"  [prosandcons]  {len(clean_df)} rows")
    return clean_df


# ─────────────────────────────────────────────
# CLEAN: documents
# ─────────────────────────────────────────────
def clean_documents():
    df = pd.read_csv(os.path.join(RAW_DIR, "documents.csv"))
    df.rename(columns={"company_id": "symbol", "Year": "year", "Annual_Report": "report_url"}, inplace=True)
    df.to_csv(os.path.join(CLEAN_DIR, "documents.csv"), index=False, encoding="utf-8-sig")
    print(f"  [documents]  {len(df)} rows")
    return df


# ─────────────────────────────────────────────
# SECTOR MAPPING CSV
# ─────────────────────────────────────────────
def save_sector_mapping():
    rows = [{"symbol": sym, "sector": sec} for sym, sec in SECTOR_MAP.items()]
    pd.DataFrame(rows).to_csv(
        os.path.join(BASE_DIR, "data", "sector_mapping.csv"),
        index=False, encoding="utf-8-sig"
    )
    print("  [sector_mapping] saved")


# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 60)
    print("ETL Step 02 -- Clean & Transform")
    print("=" * 60)
    save_sector_mapping()
    clean_companies()
    clean_analysis()
    clean_balancesheet()
    clean_profitandloss()
    clean_cashflow()
    clean_prosandcons()
    clean_documents()
    print("\nCleaning complete. Files in data/clean/")

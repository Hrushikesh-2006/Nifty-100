"""
ETL Script 03 — Load to Django Database
Loads all clean CSVs into Django models (SQLite for dev, PostgreSQL for prod).
Run after: python manage.py migrate
"""

import os
import sys
import django
import pandas as pd
import numpy as np

# Setup Django
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from companies.models import (
    Sector, Company, YearDimension, HealthLabel,
    ProfitAndLoss, BalanceSheet, CashFlow,
    Analysis, ProsCons, Document
)

CLEAN_DIR = os.path.join(BASE_DIR, "data", "clean")


def nan_to_none(val):
    """Convert numpy NaN / inf to Python None for Django."""
    if val is None:
        return None
    try:
        if np.isnan(val) or np.isinf(val):
            return None
    except (TypeError, ValueError):
        pass
    return val


def load_sectors():
    print("Loading sectors...")
    df = pd.read_csv(os.path.join(BASE_DIR, "data", "sector_mapping.csv"))
    sectors = df["sector"].unique()
    created = 0
    for s in sectors:
        _, is_new = Sector.objects.get_or_create(sector_name=s)
        if is_new:
            created += 1
    print(f"  Sectors: {Sector.objects.count()} total ({created} new)")


def load_health_labels():
    labels = [
        ("EXCELLENT", 80, 100, "#22c55e"),
        ("GOOD",      60, 79,  "#6366f1"),
        ("AVERAGE",   40, 59,  "#f59e0b"),
        ("WEAK",      20, 39,  "#f97316"),
        ("POOR",       0, 19,  "#ef4444"),
    ]
    for name, lo, hi, color in labels:
        HealthLabel.objects.get_or_create(
            label_name=name,
            defaults={"min_score": lo, "max_score": hi, "color_hex": color}
        )
    print(f"  Health labels: {HealthLabel.objects.count()}")


def load_companies():
    print("Loading companies...")
    df = pd.read_csv(os.path.join(CLEAN_DIR, "companies.csv"))
    created = updated = 0
    for _, row in df.iterrows():
        sector = Sector.objects.filter(sector_name=row.get("sector", "Others")).first()
        obj, is_new = Company.objects.update_or_create(
            symbol=str(row["symbol"]).strip(),
            defaults={
                "company_name": str(row.get("company_name", "")).strip()[:255],
                "sector":       sector,
                "company_logo": str(row.get("company_logo", "")).strip()[:500] if pd.notna(row.get("company_logo")) else "",
                "chart_link":   str(row.get("chart_link", "")).strip()[:500] if pd.notna(row.get("chart_link")) else "",
                "website":      str(row.get("website", "")).strip()[:500] if pd.notna(row.get("website")) else "",
                "nse_profile":  str(row.get("nse_profile", "")).strip()[:500] if pd.notna(row.get("nse_profile")) else "",
                "bse_profile":  str(row.get("bse_profile", "")).strip()[:500] if pd.notna(row.get("bse_profile")) else "",
                "about_company": str(row.get("about_company", "")).strip() if pd.notna(row.get("about_company")) else "",
                "face_value":   nan_to_none(row.get("face_value")),
                "book_value":   nan_to_none(row.get("book_value")),
                "roce_percentage": nan_to_none(row.get("roce_percentage")),
                "roe_percentage":  nan_to_none(row.get("roe_percentage")),
            }
        )
        if is_new: created += 1
        else: updated += 1
    print(f"  Companies: {Company.objects.count()} total ({created} new, {updated} updated)")


def get_or_create_year(year_label, fiscal_year, month_num, sort_order):
    obj, _ = YearDimension.objects.get_or_create(
        year_label=str(year_label).strip(),
        defaults={
            "fiscal_year": int(fiscal_year) if pd.notna(fiscal_year) else None,
            "month_num":   int(month_num)   if pd.notna(month_num)   else None,
            "is_ttm":      str(year_label).strip() == "TTM",
            "sort_order":  int(sort_order)  if pd.notna(sort_order)  else 99999,
        }
    )
    return obj


def load_profit_loss():
    print("Loading Profit & Loss...")
    df = pd.read_csv(os.path.join(CLEAN_DIR, "profitandloss.csv"))
    created = skipped = 0
    for _, row in df.iterrows():
        company = Company.objects.filter(symbol=str(row["symbol"]).strip()).first()
        if not company:
            skipped += 1; continue
        year    = get_or_create_year(row["year_label"], row["fiscal_year"], row["month_num"], row["sort_order"])
        obj, is_new = ProfitAndLoss.objects.update_or_create(
            company=company, year=year,
            defaults={
                "sales":            nan_to_none(row.get("sales")),
                "expenses":         nan_to_none(row.get("expenses")),
                "operating_profit": nan_to_none(row.get("operating_profit")),
                "opm_pct":          nan_to_none(row.get("opm_pct")),
                "other_income":     nan_to_none(row.get("other_income")),
                "interest":         nan_to_none(row.get("interest")),
                "depreciation":     nan_to_none(row.get("depreciation")),
                "profit_before_tax": nan_to_none(row.get("profit_before_tax")),
                "tax_pct":          nan_to_none(row.get("tax_pct")),
                "net_profit":       nan_to_none(row.get("net_profit")),
                "eps":              nan_to_none(row.get("eps")),
                "dividend_payout_pct": nan_to_none(row.get("dividend_payout_pct")),
                "net_profit_margin_pct": nan_to_none(row.get("net_profit_margin_pct")),
                "expense_ratio_pct": nan_to_none(row.get("expense_ratio_pct")),
                "interest_coverage": nan_to_none(row.get("interest_coverage")),
            }
        )
        if is_new: created += 1
    print(f"  P&L: {ProfitAndLoss.objects.count()} rows ({created} new, {skipped} skipped)")


def load_balance_sheet():
    print("Loading Balance Sheet...")
    df = pd.read_csv(os.path.join(CLEAN_DIR, "balancesheet.csv"))
    created = skipped = 0
    for _, row in df.iterrows():
        company = Company.objects.filter(symbol=str(row["symbol"]).strip()).first()
        if not company:
            skipped += 1; continue
        year = get_or_create_year(row["year_label"], row["fiscal_year"], row["month_num"], row["sort_order"])
        obj, is_new = BalanceSheet.objects.update_or_create(
            company=company, year=year,
            defaults={
                "equity_capital":   nan_to_none(row.get("equity_capital")),
                "reserves":         nan_to_none(row.get("reserves")),
                "borrowings":       nan_to_none(row.get("borrowings")),
                "other_liabilities": nan_to_none(row.get("other_liabilities")),
                "total_liabilities": nan_to_none(row.get("total_liabilities")),
                "fixed_assets":     nan_to_none(row.get("fixed_assets")),
                "cwip":             nan_to_none(row.get("cwip")),
                "investments":      nan_to_none(row.get("investments")),
                "other_assets":     nan_to_none(row.get("other_assets")),
                "total_assets":     nan_to_none(row.get("total_assets")),
                "debt_to_equity":   nan_to_none(row.get("debt_to_equity")),
                "equity_ratio":     nan_to_none(row.get("equity_ratio")),
            }
        )
        if is_new: created += 1
    print(f"  Balance Sheet: {BalanceSheet.objects.count()} rows ({created} new, {skipped} skipped)")


def load_cash_flow():
    print("Loading Cash Flow...")
    df = pd.read_csv(os.path.join(CLEAN_DIR, "cashflow.csv"))
    created = skipped = 0
    for _, row in df.iterrows():
        company = Company.objects.filter(symbol=str(row["symbol"]).strip()).first()
        if not company:
            skipped += 1; continue
        year = get_or_create_year(row["year_label"], row["fiscal_year"], row["month_num"], row["sort_order"])
        obj, is_new = CashFlow.objects.update_or_create(
            company=company, year=year,
            defaults={
                "operating_activity": nan_to_none(row.get("operating_activity")),
                "investing_activity": nan_to_none(row.get("investing_activity")),
                "financing_activity": nan_to_none(row.get("financing_activity")),
                "net_cash_flow":      nan_to_none(row.get("net_cash_flow")),
                "free_cash_flow":     nan_to_none(row.get("free_cash_flow")),
            }
        )
        if is_new: created += 1
    print(f"  Cash Flow: {CashFlow.objects.count()} rows ({created} new, {skipped} skipped)")


def load_analysis():
    print("Loading Analysis...")
    df = pd.read_csv(os.path.join(CLEAN_DIR, "analysis.csv"))
    created = skipped = 0
    for _, row in df.iterrows():
        company = Company.objects.filter(symbol=str(row["symbol"]).strip()).first()
        if not company:
            skipped += 1; continue
        obj, is_new = Analysis.objects.update_or_create(
            company=company,
            metric=str(row["metric"]),
            period_label=str(row["period_label"]),
            defaults={"value_pct": nan_to_none(row.get("value_pct"))}
        )
        if is_new: created += 1
    print(f"  Analysis: {Analysis.objects.count()} rows ({created} new, {skipped} skipped)")


def load_pros_cons():
    print("Loading Pros & Cons...")
    df = pd.read_csv(os.path.join(CLEAN_DIR, "prosandcons.csv"))
    ProsCons.objects.all().delete()
    created = skipped = 0
    for _, row in df.iterrows():
        company = Company.objects.filter(symbol=str(row["symbol"]).strip()).first()
        if not company:
            skipped += 1; continue
        ProsCons.objects.create(
            company=company,
            is_pro=bool(row["is_pro"]),
            text=str(row["text"]).strip()
        )
        created += 1
    print(f"  Pros/Cons: {ProsCons.objects.count()} rows ({created} new, {skipped} skipped)")


def load_documents():
    print("Loading Documents...")
    df = pd.read_csv(os.path.join(CLEAN_DIR, "documents.csv"))
    Document.objects.all().delete()
    created = skipped = 0
    for _, row in df.iterrows():
        company = Company.objects.filter(symbol=str(row["symbol"]).strip()).first()
        if not company:
            skipped += 1; continue
        url = str(row.get("report_url", "")).strip()
        if url and url != "nan":
            Document.objects.create(company=company, year=str(row["year"]), report_url=url[:500])
            created += 1
    print(f"  Documents: {Document.objects.count()} rows ({created} new, {skipped} skipped)")


def data_quality_checks():
    print("\n--- Data Quality Checks ---")
    print(f"  Companies with no P&L:  {Company.objects.filter(profit_loss__isnull=True).count()}")
    print(f"  Companies with no BS:   {Company.objects.filter(balance_sheets__isnull=True).count()}")
    print(f"  Companies with no CF:   {Company.objects.filter(cash_flows__isnull=True).count()}")
    print(f"  P&L rows with null sales: {ProfitAndLoss.objects.filter(sales__isnull=True).count()}")
    print(f"  Total year dimensions:  {YearDimension.objects.count()}")


if __name__ == "__main__":
    print("=" * 60)
    print("ETL Step 03 -- Load to Database")
    print("=" * 60)
    load_sectors()
    load_health_labels()
    load_companies()
    load_profit_loss()
    load_balance_sheet()
    load_cash_flow()
    load_analysis()
    load_pros_cons()
    load_documents()
    data_quality_checks()
    print("\nLoad complete.")

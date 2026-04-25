"""
ETL Script 04 — ML Health Scoring
Computes a composite health score (0-100) for every company.
Dimensions: Profitability, Growth, Leverage, Cash Flow, Dividend, Trend.
"""

import os
import sys
import django
import numpy as np
import pandas as pd

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from companies.models import Company, MLScore, ProfitAndLoss, BalanceSheet, CashFlow, Analysis


def safe_mean(vals):
    clean = [v for v in vals if v is not None and not np.isnan(v)]
    return np.mean(clean) if clean else None


def percentile_score(value, all_vals, higher_is_better=True):
    """Convert a raw value to a 0-100 percentile score."""
    clean = [v for v in all_vals if v is not None and not np.isnan(v)]
    if not clean or value is None or np.isnan(value):
        return 50.0  # neutral score when no data
    pct = np.sum(np.array(clean) <= value) / len(clean) * 100
    return pct if higher_is_better else (100 - pct)


def compute_scores():
    from django.db.models import Prefetch
    companies = list(Company.objects.prefetch_related(
        Prefetch("profit_loss", queryset=ProfitAndLoss.objects.select_related("year")),
        Prefetch("balance_sheets", queryset=BalanceSheet.objects.select_related("year")),
        Prefetch("cash_flows", queryset=CashFlow.objects.select_related("year")),
        "analysis"
    ).all())

    print(f"Computing ML scores for {len(companies)} companies...")

    # Pre-build benchmark arrays from last 3 years of all companies
    all_npm, all_roe, all_d2e, all_icr, all_fcf, all_opm = [], [], [], [], [], []

    for c in companies:
        pl = list(c.profit_loss.order_by("-year__sort_order")[:3])
        bs = list(c.balance_sheets.order_by("-year__sort_order")[:3])
        cf = list(c.cash_flows.order_by("-year__sort_order")[:3])
        all_npm.extend([r.net_profit_margin_pct for r in pl if r.net_profit_margin_pct is not None])
        all_opm.extend([r.opm_pct for r in pl if r.opm_pct is not None])
        all_d2e.extend([r.debt_to_equity for r in bs if r.debt_to_equity is not None])
        all_icr.extend([r.interest_coverage for r in pl if r.interest_coverage is not None])
        all_fcf.extend([r.free_cash_flow for r in cf if r.free_cash_flow is not None])
        all_roe.extend([c.roe_percentage] if c.roe_percentage else [])

    results = []
    for c in companies:
        pl_qs = list(c.profit_loss.exclude(year__is_ttm=True).order_by("-year__sort_order")[:5])
        bs_qs = list(c.balance_sheets.order_by("-year__sort_order")[:3])
        cf_qs = list(c.cash_flows.order_by("-year__sort_order")[:3])

        # ── Profitability Score ───────────────────────────
        npm_vals = [r.net_profit_margin_pct for r in pl_qs if r.net_profit_margin_pct is not None]
        opm_vals = [r.opm_pct for r in pl_qs if r.opm_pct is not None]
        avg_npm = safe_mean(npm_vals)
        avg_opm = safe_mean(opm_vals)
        prof_score = 0.5 * percentile_score(avg_npm, all_npm) + 0.5 * percentile_score(avg_opm, all_opm)

        # ── Growth Score ──────────────────────────────────
        sales_vals = [r.sales for r in pl_qs if r.sales is not None]
        growth_arr = []
        for i in range(len(sales_vals) - 1):
            if sales_vals[i+1] and sales_vals[i+1] != 0:
                growth_arr.append((sales_vals[i] - sales_vals[i+1]) / abs(sales_vals[i+1]) * 100)
        avg_growth = safe_mean(growth_arr)
        # Also use 5Y analysis
        analysis_growth = [a.value_pct for a in c.analysis.filter(metric="compounded_sales_growth", period_label="5Y")]
        combined_growth = (avg_growth or 0) * 0.4 + (safe_mean(analysis_growth) or 0) * 0.6
        growth_score = min(100.0, max(0.0, 50 + combined_growth * 2))

        # ── Leverage Score (lower D/E = better) ───────────
        d2e_vals = [r.debt_to_equity for r in bs_qs if r.debt_to_equity is not None]
        avg_d2e  = safe_mean(d2e_vals)
        leverage_score = percentile_score(avg_d2e, all_d2e, higher_is_better=False)

        # ── Cash Flow Score ───────────────────────────────
        fcf_vals = [r.free_cash_flow for r in cf_qs if r.free_cash_flow is not None]
        avg_fcf  = safe_mean(fcf_vals)
        cashflow_score = percentile_score(avg_fcf, all_fcf)

        # ── Dividend Score ────────────────────────────────
        div_vals    = [r.dividend_payout_pct for r in pl_qs if r.dividend_payout_pct is not None]
        avg_div     = safe_mean(div_vals)
        dividend_score = min(100.0, max(0.0, (avg_div or 0) * 2))

        # ── Trend Score (last 2y vs prev 3y profit) ───────
        profits = [r.net_profit for r in pl_qs if r.net_profit is not None]
        if len(profits) >= 4:
            recent = safe_mean(profits[:2])
            older  = safe_mean(profits[2:])
            trend  = ((recent - older) / abs(older)) * 100 if older and older != 0 else 0
            trend_score = min(100.0, max(0.0, 50 + trend))
        else:
            trend_score = 50.0

        # ── Overall Score (weighted) ───────────────────────
        overall = (
            prof_score     * 0.25 +
            growth_score   * 0.20 +
            leverage_score * 0.20 +
            cashflow_score * 0.20 +
            dividend_score * 0.05 +
            trend_score    * 0.10
        )
        overall = round(min(100.0, max(0.0, overall)), 2)

        # Health label
        if overall >= 80:   label = "EXCELLENT"
        elif overall >= 60: label = "GOOD"
        elif overall >= 40: label = "AVERAGE"
        elif overall >= 20: label = "WEAK"
        else:               label = "POOR"

        results.append({
            "company":             c,
            "overall_score":       overall,
            "profitability_score": round(prof_score, 2),
            "growth_score":        round(growth_score, 2),
            "leverage_score":      round(leverage_score, 2),
            "cashflow_score":      round(cashflow_score, 2),
            "dividend_score":      round(dividend_score, 2),
            "trend_score":         round(trend_score, 2),
            "health_label":        label,
        })

    # Bulk save
    MLScore.objects.all().delete()
    MLScore.objects.bulk_create([MLScore(**r) for r in results])
    print(f"  Saved {MLScore.objects.count()} ML scores.")

    # Leaderboard preview
    top = sorted(results, key=lambda x: x["overall_score"], reverse=True)[:5]
    print("\nTop 5 companies:")
    for r in top:
        print(f"  {r['company'].symbol:<15} {r['overall_score']:>6.1f}  {r['health_label']}")


if __name__ == "__main__":
    print("=" * 60)
    print("ETL Step 04 -- ML Scoring")
    print("=" * 60)
    compute_scores()
    print("\nScoring complete.")

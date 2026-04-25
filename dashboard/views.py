"""
Dashboard views — serve context data for Chart.js-powered pages
"""
import json
from django.shortcuts import render, get_object_or_404
from django.db.models import Avg, Count, Q, Prefetch
from companies.models import (
    Company, Sector, MLScore,
    ProfitAndLoss, BalanceSheet, CashFlow, Analysis, ProsCons
)


def _safe_list(qs, field):
    return [float(v) if v is not None else None for v in qs.values_list(field, flat=True)]


def home(request):
    companies = Company.objects.select_related("sector").prefetch_related("ml_scores").all()
    sectors   = Sector.objects.annotate(count=Count("companies")).order_by("sector_name")

    # sector filter
    sector_filter = request.GET.get("sector", "")
    search_q      = request.GET.get("q", "")
    if sector_filter:
        companies = companies.filter(sector__sector_name__iexact=sector_filter)
    if search_q:
        companies = companies.filter(
            Q(symbol__icontains=search_q) | Q(company_name__icontains=search_q)
        )

    # Leaderboard top 10
    leaderboard = sorted(
        [c for c in Company.objects.prefetch_related("ml_scores").all()
         if c.ml_scores.exists()],
        key=lambda c: c.ml_scores.order_by("-computed_at").first().overall_score or 0,
        reverse=True
    )[:10]

    return render(request, "home.html", {
        "companies":     companies,
        "sectors":       sectors,
        "sector_filter": sector_filter,
        "search_q":      search_q,
        "leaderboard":   leaderboard,
        "total_companies": Company.objects.count(),
        "total_sectors":   Sector.objects.count(),
    })


def company_detail(request, symbol):
    company = get_object_or_404(
        Company.objects.select_related("sector").prefetch_related(
            Prefetch("profit_loss", queryset=ProfitAndLoss.objects.select_related("year")),
            Prefetch("balance_sheets", queryset=BalanceSheet.objects.select_related("year")),
            Prefetch("cash_flows", queryset=CashFlow.objects.select_related("year")),
            "analysis", "ml_scores", "pros_cons", "documents"
        ),
        symbol=symbol.upper()
    )

    pl  = company.profit_loss.order_by("year__sort_order")
    bs  = company.balance_sheets.order_by("year__sort_order")
    cf  = company.cash_flows.order_by("year__sort_order")
    latest_score = company.ml_scores.order_by("-computed_at").first()
    pros = company.pros_cons.filter(is_pro=True)
    cons = company.pros_cons.filter(is_pro=False)
    docs = company.documents.order_by("-year")[:5]

    # Chart data (JSON-serialisable)
    chart = {
        "years":         [r.year.year_label for r in pl],
        "sales":         [r.sales            for r in pl],
        "net_profit":    [r.net_profit        for r in pl],
        "opm_pct":       [r.opm_pct           for r in pl],
        "npm_pct":       [r.net_profit_margin_pct for r in pl],
        "eps":           [r.eps               for r in pl],
        "bs_years":      [r.year.year_label   for r in bs],
        "borrowings":    [r.borrowings        for r in bs],
        "reserves":      [r.reserves          for r in bs],
        "total_assets":  [r.total_assets      for r in bs],
        "d2e":           [r.debt_to_equity    for r in bs],
        "cf_years":      [r.year.year_label   for r in cf],
        "op_cf":         [r.operating_activity  for r in cf],
        "inv_cf":        [r.investing_activity  for r in cf],
        "fin_cf":        [r.financing_activity  for r in cf],
        "fcf":           [r.free_cash_flow      for r in cf],
    }

    # Analysis pivoted
    analysis_map = {}
    for a in company.analysis.all():
        analysis_map.setdefault(a.metric, {})[a.period_label] = a.value_pct

    return render(request, "company_detail.html", {
        "company":      company,
        "latest_score": latest_score,
        "pros":         pros,
        "cons":         cons,
        "docs":         docs,
        "chart_json":   json.dumps(chart),
        "analysis_map": analysis_map,
        "pl_records":   pl,
        "bs_records":   bs,
        "cf_records":   cf,
    })


def sector_view(request, name):
    sector    = get_object_or_404(Sector, sector_name__iexact=name)
    companies = Company.objects.filter(sector=sector).prefetch_related("ml_scores")
    avg_roce  = companies.aggregate(v=Avg("roce_percentage"))["v"]
    avg_roe   = companies.aggregate(v=Avg("roe_percentage"))["v"]

    return render(request, "sector_view.html", {
        "sector":    sector,
        "companies": companies,
        "avg_roce":  round(avg_roce, 2) if avg_roce else None,
        "avg_roe":   round(avg_roe, 2)  if avg_roe  else None,
    })


def compare(request):
    sym1 = request.GET.get("sym1", "")
    sym2 = request.GET.get("sym2", "")
    c1   = Company.objects.filter(symbol=sym1.upper()).prefetch_related(
        Prefetch("profit_loss", queryset=ProfitAndLoss.objects.select_related("year")), "ml_scores"
    ).first()
    c2   = Company.objects.filter(symbol=sym2.upper()).prefetch_related(
        Prefetch("profit_loss", queryset=ProfitAndLoss.objects.select_related("year")), "ml_scores"
    ).first()

    all_companies = Company.objects.values_list("symbol", "company_name").order_by("symbol")

    companies_to_compare = [c for c in (c1, c2) if c]

    return render(request, "compare.html", {
        "c1":           c1,
        "c2":           c2,
        "sym1":         sym1,
        "sym2":         sym2,
        "all_companies": all_companies,
        "companies_to_compare": companies_to_compare,
    })


def screener(request):
    sectors   = Sector.objects.all().order_by("sector_name")
    companies = Company.objects.select_related("sector").prefetch_related("ml_scores").all()

    sector_f = request.GET.get("sector", "")
    min_roce = request.GET.get("min_roce", "")
    min_roe  = request.GET.get("min_roe", "")

    if sector_f:
        companies = companies.filter(sector__sector_name__iexact=sector_f)
    if min_roce:
        companies = companies.filter(roce_percentage__gte=float(min_roce))
    if min_roe:
        companies = companies.filter(roe_percentage__gte=float(min_roe))

    return render(request, "screener.html", {
        "companies": companies,
        "sectors":   sectors,
        "sector_f":  sector_f,
        "min_roce":  min_roce,
        "min_roe":   min_roe,
    })


def powerbi_view(request):
    """
    Produces the 7 pseudo-PowerBI analytical dashboards inside the web app.
    """
    sectors = Sector.objects.annotate(count=Count("companies")).order_by("sector_name")
    
    sector_filter = request.GET.get("sector", "")
    companies = Company.objects.select_related("sector").prefetch_related(
        Prefetch("profit_loss", queryset=ProfitAndLoss.objects.select_related("year")),
        Prefetch("balance_sheets", queryset=BalanceSheet.objects.select_related("year")),
        Prefetch("cash_flows", queryset=CashFlow.objects.select_related("year")),
        "ml_scores"
    ).all()
    
    if sector_filter:
        companies = companies.filter(sector__sector_name__iexact=sector_filter)
        
    total_revenue_all = 0
    total_health = 0
    total_margin = 0
    health_count = 0
    margin_count = 0
    
    for c in companies:
        pl = c.profit_loss.order_by("-year__sort_order").first()
        if pl and pl.sales:
            total_revenue_all += float(pl.sales)
        if pl and pl.net_profit_margin_pct is not None:
            total_margin += float(pl.net_profit_margin_pct)
            margin_count += 1
            
        score = c.ml_scores.order_by("-computed_at").first()
        if score and score.overall_score is not None:
            total_health += float(score.overall_score)
            health_count += 1
            
    avg_health = (total_health / health_count) if health_count else 0
    avg_margin = (total_margin / margin_count) if margin_count else 0
    
    # Leaderboard
    leaderboard = sorted(
        [c for c in companies if c.ml_scores.exists()],
        key=lambda c: c.ml_scores.order_by("-computed_at").first().overall_score or 0,
        reverse=True
    )[:50]

    # Sector Benchmarking Data
    sector_scores = []
    for s in sectors:
        sc = Company.objects.filter(sector=s, ml_scores__isnull=False).distinct()
        if sc.exists():
            scores_list = []
            for c in sc:
                latest = c.ml_scores.order_by("-computed_at").first()
                if latest and latest.overall_score is not None:
                    scores_list.append(float(latest.overall_score))
            if scores_list:
                avg_sc = sum(scores_list) / len(scores_list)
                sector_scores.append({"sector": s.sector_name, "avg_score": round(avg_sc, 1)})
            
    # Sorted sector scores
    sector_scores = sorted(sector_scores, key=lambda x: x["avg_score"], reverse=True)

    pbi_data = {
        "sector_scores_val": [round(s["avg_score"], 1) for s in sector_scores],
        "sector_scores_lbl": [s["sector"] for s in sector_scores],
    }

    return render(request, "powerbi_dashboards.html", {
        "total_revenue": total_revenue_all,
        "avg_health": avg_health,
        "avg_margin": avg_margin,
        "leaderboard": leaderboard,
        "sector_f":  sector_filter,
        "sectors":   sectors,
        "pbi_data":  json.dumps(pbi_data)
    })


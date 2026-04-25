"""
DRF Views for Nifty 100 REST API
"""
from rest_framework import viewsets, generics, filters, views
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Avg, Count, Q
from django.db.models import FloatField
from drf_spectacular.utils import extend_schema, OpenApiParameter
import yfinance as yf
from django.core.cache import cache

from django.db.models import Prefetch
from companies.models import Company, Sector, MLScore, ProfitAndLoss, BalanceSheet, CashFlow
from .serializers import (
    CompanyListSerializer, CompanyDetailSerializer,
    SectorSerializer, MLScoreSerializer,
    ProfitAndLossSerializer, BalanceSheetSerializer, CashFlowSerializer,
)


class CompanyViewSet(viewsets.ReadOnlyModelViewSet):
    """
    List all Nifty 100 companies or retrieve one by symbol.
    """
    queryset = Company.objects.select_related("sector").prefetch_related(
        "ml_scores"
    ).all()
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields   = ["symbol", "company_name", "sector__sector_name"]
    ordering_fields = ["symbol", "company_name", "roce_percentage", "roe_percentage"]
    ordering        = ["symbol"]

    def get_serializer_class(self):
        if self.action == "retrieve":
            return CompanyDetailSerializer
        return CompanyListSerializer

    @extend_schema(description="Full financial history for a company")
    @action(detail=True, url_path="financials")
    def financials(self, request, pk=None):
        company = self.get_object()
        return Response({
            "symbol": company.symbol,
            "profit_loss":    ProfitAndLossSerializer(
                company.profit_loss.order_by("year__sort_order"), many=True).data,
            "balance_sheets": BalanceSheetSerializer(
                company.balance_sheets.order_by("year__sort_order"), many=True).data,
            "cash_flows":     CashFlowSerializer(
                company.cash_flows.order_by("year__sort_order"), many=True).data,
        })

    @extend_schema(description="Latest ML health score for a company")
    @action(detail=True, url_path="score")
    def score(self, request, pk=None):
        company = self.get_object()
        score = company.ml_scores.order_by("-computed_at").first()
        if not score:
            return Response({"detail": "No score computed yet."}, status=404)
        return Response(MLScoreSerializer(score).data)


class SectorViewSet(viewsets.ReadOnlyModelViewSet):
    """
    List all sectors with company count and average metrics.
    """
    queryset = Sector.objects.annotate(
        company_count=Count("companies"),
        avg_roce=Avg("companies__roce_percentage"),
        avg_roe=Avg("companies__roe_percentage"),
    )
    serializer_class = SectorSerializer

    def list(self, request, *args, **kwargs):
        qs = self.get_queryset()
        data = []
        for s in qs:
            data.append({
                "id":            s.id,
                "sector_name":   s.sector_name,
                "company_count": s.company_count,
                "avg_roce":      round(s.avg_roce, 2) if s.avg_roce else None,
                "avg_roe":       round(s.avg_roe, 2)  if s.avg_roe  else None,
            })
        return Response(data)


class LeaderboardView(generics.ListAPIView):
    """
    Top / bottom N companies by ML overall_score.
    Query params: n=10, order=desc (default) | asc
    """
    serializer_class = CompanyListSerializer

    @extend_schema(parameters=[
        OpenApiParameter("n",     int,  description="Number of results (default 10)"),
        OpenApiParameter("order", str,  description="asc | desc (default desc)"),
        OpenApiParameter("sector", str, description="Filter by sector name"),
    ])
    def get_queryset(self):
        n      = int(self.request.query_params.get("n", 10))
        order  = self.request.query_params.get("order", "desc")
        sector = self.request.query_params.get("sector", None)

        qs = Company.objects.select_related("sector").prefetch_related("ml_scores")
        if sector:
            qs = qs.filter(sector__sector_name__iexact=sector)

        # annotate with latest score
        from django.db.models import Subquery, OuterRef
        latest_score_sq = MLScore.objects.filter(
            company=OuterRef("pk")
        ).order_by("-computed_at").values("overall_score")[:1]

        qs = qs.annotate(latest_score_val=Subquery(latest_score_sq, output_field=FloatField()))

        if order == "asc":
            qs = qs.order_by("latest_score_val")
        else:
            qs = qs.order_by("-latest_score_val")

        return qs[:n]


class SearchView(generics.ListAPIView):
    """Full-text search across company name and symbol"""
    serializer_class = CompanyListSerializer

    def get_queryset(self):
        q = self.request.query_params.get("q", "")
        return Company.objects.select_related("sector").prefetch_related("ml_scores").filter(
            Q(symbol__icontains=q) | Q(company_name__icontains=q)
        )[:20]




class ScreenerView(generics.ListAPIView):
    """
    Screener endpoint for filtered companies (AJAX support for frontend).
    Params: sector, min_roce, min_roe, n
    """
    serializer_class = CompanyListSerializer

    def get_queryset(self):
        companies = Company.objects.select_related("sector").prefetch_related("ml_scores").all()
        
        sector_f = self.request.query_params.get("sector", "")
        min_roce = self.request.query_params.get("min_roce")
        min_roe = self.request.query_params.get("min_roe")
        n = int(self.request.query_params.get("n", 100))
        
        if sector_f:
            companies = companies.filter(sector__sector_name__iexact=sector_f)
        if min_roce:
            companies = companies.filter(roce_percentage__gte=float(min_roce))
        if min_roe:
            companies = companies.filter(roe_percentage__gte=float(min_roe))
        
        return companies.order_by("-roce_percentage")[:n]


class CompareView(generics.ListAPIView):
    """
    Compare 2+ companies. Params: sym=SYM1&sym=SYM2 or sym1=SYM1&sym2=SYM2
    """
    serializer_class = CompanyDetailSerializer

    def get_queryset(self):
        symbols = [s.upper().strip() for s in self.request.query_params.getlist("sym") if s]
        if not symbols:
            sym1 = self.request.query_params.get("sym1", "").upper().strip()
            sym2 = self.request.query_params.get("sym2", "").upper().strip()
            symbols = [s for s in [sym1, sym2] if s]
        
        return Company.objects.filter(symbol__in=symbols).select_related("sector").prefetch_related(
            "ml_scores",
            Prefetch("profit_loss", queryset=ProfitAndLoss.objects.select_related("year")),
            Prefetch("balance_sheets", queryset=BalanceSheet.objects.select_related("year")),
            Prefetch("cash_flows", queryset=CashFlow.objects.select_related("year")),
            "pros_cons", "documents"
        ).order_by("symbol")


class PowerBIDashboardView(views.APIView):
    """
    PowerBI aggregates: totals, avgs, leaderboard, sector benchmarks.
    """
    def get(self, request):
        sector_filter = self.request.query_params.get("sector", "")
        companies = Company.objects.select_related("sector").prefetch_related(
            Prefetch("profit_loss", queryset=ProfitAndLoss.objects.select_related("year")),
            "ml_scores"
        )
        if sector_filter:
            companies = companies.filter(sector__sector_name__iexact=sector_filter)
        companies = companies.all()
        
        # Aggregates
        total_revenue = sum([c.profit_loss.order_by("-year__sort_order").first().sales or 0 for c in companies])
        scores = [c.ml_scores.order_by("-computed_at").first() for c in companies if c.ml_scores.exists()]
        avg_health = sum([s.overall_score for s in scores]) / len(scores) if scores else 0
        
        # Leaderboard top 50
        leaderboard = sorted(
            [c for c in companies if c.ml_scores.exists()],
            key=lambda c: c.ml_scores.order_by("-computed_at").first().overall_score or 0,
            reverse=True
        )[:50]
        
        return Response({
            "total_revenue": total_revenue,
            "avg_health_score": round(avg_health, 2),
            "leaderboard_count": len(leaderboard),
            "leaderboard": CompanyListSerializer(leaderboard, many=True).data,
        })


class LivePricingView(views.APIView):
    """
    Fetches real-time price data using yfinance.
    Params: symbols=RELIANCE,TCS
    """
    def get(self, request):
        symbols_param = request.GET.get("symbols", "")
        if not symbols_param:
            return Response({})
            
        symbols = [s.strip().upper() for s in symbols_param.split(",") if s.strip()]
        
        # Sort to make cache key consistent
        cache_symbols = sorted(symbols)
        cache_key = f"live_price_{'_'.join(cache_symbols)}"
        cached_data = cache.get(cache_key)
        if cached_data:
            return Response(cached_data)
            
        # Append .NS to symbols if they don't have it
        yf_symbols = [f"{s}.NS" if not s.endswith(".NS") and not s.endswith(".BO") else s for s in symbols]
        
        try:
            tickers = yf.Tickers(" ".join(yf_symbols))
            data = {}
            for i, symbol in enumerate(symbols):
                yf_sym = yf_symbols[i]
                try:
                    ticker = tickers.tickers[yf_sym]
                    fast_info = ticker.fast_info
                    
                    current_price = float(fast_info.last_price)
                    prev_close = float(fast_info.previous_close)
                    change = current_price - prev_close
                    pct_change = (change / prev_close * 100) if prev_close else 0
                    
                    data[symbol] = {
                        "price": round(current_price, 2),
                        "change": round(change, 2),
                        "pct_change": round(pct_change, 2),
                    }
                except Exception:
                    # Ignore failing tickers gracefully
                    pass
            
            cache.set(cache_key, data, 15)  # Cache for 15 seconds
            return Response(data)
        except Exception as e:
            return Response({"error": str(e)}, status=500)


class RealtimeFinancialDataView(generics.RetrieveAPIView):
    """
    Fetch real-time financial metrics from Financial Modeling Prep API for a company.
    """
    from companies.models import RealtimeFinancialData
    from .serializers import RealtimeFinancialDataSerializer
    
    queryset = RealtimeFinancialData.objects.all()
    serializer_class = RealtimeFinancialDataSerializer
    lookup_field = "company__symbol"
    lookup_url_kwarg = "symbol"


class CompareWithRealtimeView(generics.ListAPIView):
    """
    Compare 2+ companies with real-time financial data.
    Params: sym1=RELIANCE&sym2=TCS or sym=RELIANCE&sym=TCS
    """
    from .serializers import CompanyWithRealtimeSerializer
    
    serializer_class = CompanyWithRealtimeSerializer

    def get_queryset(self):
        symbols = [s.upper().strip() for s in self.request.query_params.getlist("sym") if s]
        if not symbols:
            sym1 = self.request.query_params.get("sym1", "").upper().strip()
            sym2 = self.request.query_params.get("sym2", "").upper().strip()
            symbols = [s for s in [sym1, sym2] if s]
        
        return Company.objects.filter(symbol__in=symbols).select_related(
            "sector",
            "realtime_data",
            "realtime_price"
        ).prefetch_related(
            "ml_scores"
        ).order_by("symbol")


class FetchRealtimeDataView(views.APIView):
    """
    Manually fetch and update real-time data for a company.
    POST /api/realtime/fetch/?symbol=RELIANCE
    """
    from .realtime_service import RealtimeDataService
    from companies.models import RealtimeFinancialData
    
    def post(self, request):
        symbol = request.query_params.get("symbol", "").upper().strip()
        
        if not symbol:
            return Response({"error": "symbol parameter required"}, status=400)
        
        # Check if company exists
        try:
            company = Company.objects.get(symbol=symbol)
        except Company.DoesNotExist:
            return Response({"error": f"Company {symbol} not found"}, status=404)
        
        # Fetch real-time data
        metrics = RealtimeDataService.get_company_realtime_snapshot(symbol)
        
        if not metrics:
            return Response({"error": "Failed to fetch real-time data"}, status=500)
        
        # Update or create RealtimeFinancialData record
        realtime_data, created = RealtimeFinancialData.objects.update_or_create(
            company=company,
            defaults={
                'revenue': metrics.get('revenue'),
                'net_income': metrics.get('net_income'),
                'operating_income': metrics.get('operating_income'),
                'gross_profit_margin': metrics.get('gross_profit_margin'),
                'operating_income_ratio': metrics.get('operating_income_ratio'),
                'net_income_ratio': metrics.get('net_income_ratio'),
                'eps': metrics.get('eps'),
                'ebitda': metrics.get('ebitda'),
                'total_assets': metrics.get('total_assets'),
                'total_liabilities': metrics.get('total_liabilities'),
                'total_equity': metrics.get('total_equity'),
                'current_assets': metrics.get('current_assets'),
                'current_liabilities': metrics.get('current_liabilities'),
                'operating_cash_flow': metrics.get('operating_cash_flow'),
                'free_cash_flow': metrics.get('free_cash_flow'),
                'capital_expenditure': metrics.get('capital_expenditure'),
                'pe_ratio': metrics.get('pe_ratio'),
                'roe': metrics.get('roe'),
                'roa': metrics.get('roa'),
                'debt_to_equity': metrics.get('debt_to_equity'),
                'current_ratio': metrics.get('current_ratio'),
                'quick_ratio': metrics.get('quick_ratio'),
                'dividend_yield': metrics.get('dividend_yield'),
            }
        )
        
        from .serializers import RealtimeFinancialDataSerializer
        
        return Response({
            "status": "created" if created else "updated",
            "symbol": symbol,
            "data": RealtimeFinancialDataSerializer(realtime_data).data,
        }, status=201 if created else 200)

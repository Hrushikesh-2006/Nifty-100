"""
DRF Serializers for Nifty 100 API
"""
from rest_framework import serializers
from companies.models import (
    Company, Sector, YearDimension,
    ProfitAndLoss, BalanceSheet, CashFlow,
    Analysis, MLScore, ProsCons, Document,
    RealtimeFinancialData, RealtimeStockPrice
)

from drf_spectacular.utils import extend_schema_field

class SectorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Sector
        fields = "__all__"


class CompanyListSerializer(serializers.ModelSerializer):
    sector_name   = serializers.CharField(source="sector.sector_name", default="")
    latest_score  = serializers.SerializerMethodField()
    health_label  = serializers.SerializerMethodField()

    class Meta:
        model = Company
        fields = [
            "symbol", "company_name", "sector_name",
            "company_logo", "website", "face_value", "book_value",
            "roce_percentage", "roe_percentage",
            "latest_score", "health_label",
        ]

    @extend_schema_field(serializers.FloatField(allow_null=True))
    def get_latest_score(self, obj):
        score = obj.ml_scores.order_by("-computed_at").first()
        return round(score.overall_score, 1) if score and score.overall_score else None

    @extend_schema_field(serializers.CharField(allow_null=True))
    def get_health_label(self, obj):
        score = obj.ml_scores.order_by("-computed_at").first()
        return score.health_label if score else None


class ProfitAndLossSerializer(serializers.ModelSerializer):
    year_label = serializers.CharField(source="year.year_label")
    sort_order = serializers.IntegerField(source="year.sort_order")

    class Meta:
        model = ProfitAndLoss
        exclude = ["company", "year"]


class BalanceSheetSerializer(serializers.ModelSerializer):
    year_label = serializers.CharField(source="year.year_label")
    sort_order = serializers.IntegerField(source="year.sort_order")

    class Meta:
        model = BalanceSheet
        exclude = ["company", "year"]


class CashFlowSerializer(serializers.ModelSerializer):
    year_label = serializers.CharField(source="year.year_label")
    sort_order = serializers.IntegerField(source="year.sort_order")

    class Meta:
        model = CashFlow
        exclude = ["company", "year"]


class AnalysisSerializer(serializers.ModelSerializer):
    class Meta:
        model = Analysis
        fields = ["metric", "period_label", "value_pct"]


class MLScoreSerializer(serializers.ModelSerializer):
    class Meta:
        model = MLScore
        exclude = ["id", "company"]


class ProsConsSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProsCons
        fields = ["is_pro", "text", "generated_at"]


class DocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Document
        fields = ["year", "report_url"]


class CompanyDetailSerializer(serializers.ModelSerializer):
    sector_name    = serializers.CharField(source="sector.sector_name", default="")
    profit_loss    = ProfitAndLossSerializer(many=True, read_only=True)
    balance_sheets = BalanceSheetSerializer(many=True, read_only=True)
    cash_flows     = CashFlowSerializer(many=True, read_only=True)
    analysis       = AnalysisSerializer(many=True, read_only=True)
    latest_score   = serializers.SerializerMethodField()
    pros_cons      = ProsConsSerializer(many=True, read_only=True)
    documents      = DocumentSerializer(many=True, read_only=True)

    class Meta:
        model = Company
        fields = [
            "symbol", "company_name", "sector_name",
            "company_logo", "chart_link", "website",
            "nse_profile", "bse_profile", "about_company",
            "face_value", "book_value", "roce_percentage", "roe_percentage",
            "latest_score", "profit_loss", "balance_sheets",
            "cash_flows", "analysis", "pros_cons", "documents",
        ]

    @extend_schema_field(MLScoreSerializer)
    def get_latest_score(self, obj):
        score = obj.ml_scores.order_by("-computed_at").first()
        if not score:
            return None
        return MLScoreSerializer(score).data


class RealtimeFinancialDataSerializer(serializers.ModelSerializer):
    """Serialize real-time financial data from Financial Modeling Prep API"""
    class Meta:
        model = RealtimeFinancialData
        fields = [
            "revenue", "net_income", "operating_income",
            "gross_profit_margin", "operating_income_ratio", "net_income_ratio",
            "eps", "ebitda",
            "total_assets", "total_liabilities", "total_equity",
            "current_assets", "current_liabilities",
            "operating_cash_flow", "free_cash_flow", "capital_expenditure",
            "pe_ratio", "roe", "roa", "debt_to_equity",
            "current_ratio", "quick_ratio", "dividend_yield",
            "income_statement_date", "balance_sheet_date", "cash_flow_date",
            "fetched_at",
        ]


class RealtimeStockPriceSerializer(serializers.ModelSerializer):
    """Serialize real-time stock price data"""
    class Meta:
        model = RealtimeStockPrice
        fields = [
            "current_price", "open_price", "high", "low", "volume",
            "market_cap", "pe_ratio", "dividend_per_share",
            "week_52_high", "week_52_low",
            "price_change", "price_change_percent",
            "last_updated",
        ]


class CompanyWithRealtimeSerializer(serializers.ModelSerializer):
    """Company details with real-time financial data"""
    sector_name = serializers.CharField(source="sector.sector_name", default="")
    latest_score = serializers.SerializerMethodField()
    health_label = serializers.SerializerMethodField()
    realtime_data = RealtimeFinancialDataSerializer(read_only=True, allow_null=True)
    realtime_price = RealtimeStockPriceSerializer(read_only=True, allow_null=True)

    class Meta:
        model = Company
        fields = [
            "symbol", "company_name", "sector_name",
            "company_logo", "website", "face_value", "book_value",
            "roce_percentage", "roe_percentage",
            "latest_score", "health_label",
            "realtime_data", "realtime_price",
        ]

    @extend_schema_field(serializers.FloatField(allow_null=True))
    def get_latest_score(self, obj):
        score = obj.ml_scores.order_by("-computed_at").first()
        return round(score.overall_score, 1) if score and score.overall_score else None

    @extend_schema_field(serializers.CharField(allow_null=True))
    def get_health_label(self, obj):
        score = obj.ml_scores.order_by("-computed_at").first()
        return score.health_label if score else None

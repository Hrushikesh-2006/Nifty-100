"""
Django models for Nifty 100 Financial Intelligence System
Mirrors the star-schema data warehouse tables
"""
from django.db import models


# ══════════════════════════════════════════════════════════════
# DIMENSION TABLES
# ══════════════════════════════════════════════════════════════

class Sector(models.Model):
    sector_name = models.CharField(max_length=100, unique=True)
    sector_code = models.CharField(max_length=20, blank=True)
    description = models.TextField(blank=True)

    class Meta:
        db_table = "dim_sector"
        ordering = ["sector_name"]

    def __str__(self):
        return self.sector_name


class Company(models.Model):
    symbol       = models.CharField(max_length=20, primary_key=True)
    company_name = models.CharField(max_length=255, db_index=True)
    sector       = models.ForeignKey(Sector, on_delete=models.SET_NULL, null=True, blank=True, related_name="companies")
    company_logo = models.URLField(blank=True)
    chart_link   = models.URLField(blank=True)
    website      = models.URLField(blank=True)
    nse_profile  = models.URLField(blank=True)
    bse_profile  = models.URLField(blank=True)
    about_company = models.TextField(blank=True)
    face_value   = models.FloatField(null=True, blank=True)
    book_value   = models.FloatField(null=True, blank=True)
    roce_percentage = models.FloatField(null=True, blank=True)
    roe_percentage  = models.FloatField(null=True, blank=True)
    created_at   = models.DateTimeField(auto_now_add=True)
    updated_at   = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "dim_company"
        ordering = ["symbol"]

    def __str__(self):
        return f"{self.symbol} — {self.company_name}"


class YearDimension(models.Model):
    year_label  = models.CharField(max_length=20, unique=True)
    fiscal_year = models.IntegerField(null=True, blank=True)
    month_num   = models.IntegerField(null=True, blank=True)
    is_ttm      = models.BooleanField(default=False)
    sort_order  = models.IntegerField(default=0)

    class Meta:
        db_table = "dim_year"
        ordering = ["sort_order"]

    def __str__(self):
        return self.year_label


class HealthLabel(models.Model):
    label_name = models.CharField(max_length=20)   # EXCELLENT/GOOD/AVERAGE/WEAK/POOR
    min_score  = models.FloatField()
    max_score  = models.FloatField()
    color_hex  = models.CharField(max_length=7)

    class Meta:
        db_table = "dim_health_label"

    def __str__(self):
        return self.label_name


# ══════════════════════════════════════════════════════════════
# FACT TABLES
# ══════════════════════════════════════════════════════════════

class ProfitAndLoss(models.Model):
    company          = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="profit_loss")
    year             = models.ForeignKey(YearDimension, on_delete=models.CASCADE, related_name="profit_loss")
    sales            = models.FloatField(null=True, blank=True)
    expenses         = models.FloatField(null=True, blank=True)
    operating_profit = models.FloatField(null=True, blank=True)
    opm_pct          = models.FloatField(null=True, blank=True)
    other_income     = models.FloatField(null=True, blank=True)
    interest         = models.FloatField(null=True, blank=True)
    depreciation     = models.FloatField(null=True, blank=True)
    profit_before_tax = models.FloatField(null=True, blank=True)
    tax_pct          = models.FloatField(null=True, blank=True)
    net_profit       = models.FloatField(null=True, blank=True)
    eps              = models.FloatField(null=True, blank=True)
    dividend_payout_pct = models.FloatField(null=True, blank=True)
    # Computed
    net_profit_margin_pct = models.FloatField(null=True, blank=True)
    expense_ratio_pct     = models.FloatField(null=True, blank=True)
    interest_coverage     = models.FloatField(null=True, blank=True)

    class Meta:
        db_table = "fact_profit_loss"
        unique_together = [("company", "year")]
        ordering = ["company", "year__sort_order"]

    def __str__(self):
        return f"{self.company_id} | {self.year_id} | Sales={self.sales}"


class BalanceSheet(models.Model):
    company          = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="balance_sheets")
    year             = models.ForeignKey(YearDimension, on_delete=models.CASCADE, related_name="balance_sheets")
    equity_capital   = models.FloatField(null=True, blank=True)
    reserves         = models.FloatField(null=True, blank=True)
    borrowings       = models.FloatField(null=True, blank=True)
    other_liabilities = models.FloatField(null=True, blank=True)
    total_liabilities = models.FloatField(null=True, blank=True)
    fixed_assets     = models.FloatField(null=True, blank=True)
    cwip             = models.FloatField(null=True, blank=True)
    investments      = models.FloatField(null=True, blank=True)
    other_assets     = models.FloatField(null=True, blank=True)
    total_assets     = models.FloatField(null=True, blank=True)
    # Computed
    debt_to_equity   = models.FloatField(null=True, blank=True)
    equity_ratio     = models.FloatField(null=True, blank=True)

    class Meta:
        db_table = "fact_balance_sheet"
        unique_together = [("company", "year")]
        ordering = ["company", "year__sort_order"]

    def __str__(self):
        return f"{self.company_id} | {self.year_id}"


class CashFlow(models.Model):
    company             = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="cash_flows")
    year                = models.ForeignKey(YearDimension, on_delete=models.CASCADE, related_name="cash_flows")
    operating_activity  = models.FloatField(null=True, blank=True)
    investing_activity  = models.FloatField(null=True, blank=True)
    financing_activity  = models.FloatField(null=True, blank=True)
    net_cash_flow       = models.FloatField(null=True, blank=True)
    free_cash_flow      = models.FloatField(null=True, blank=True)

    class Meta:
        db_table = "fact_cash_flow"
        unique_together = [("company", "year")]
        ordering = ["company", "year__sort_order"]


class Analysis(models.Model):
    company      = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="analysis")
    metric       = models.CharField(max_length=60)
    period_label = models.CharField(max_length=10)   # 10Y / 5Y / 3Y / TTM / 1Y
    value_pct    = models.FloatField(null=True, blank=True)

    class Meta:
        db_table = "fact_analysis"
        unique_together = [("company", "metric", "period_label")]

    def __str__(self):
        return f"{self.company_id} | {self.metric} | {self.period_label} = {self.value_pct}%"


class MLScore(models.Model):
    company             = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="ml_scores")
    computed_at         = models.DateTimeField(auto_now_add=True)
    overall_score       = models.FloatField(null=True)
    profitability_score = models.FloatField(null=True)
    growth_score        = models.FloatField(null=True)
    leverage_score      = models.FloatField(null=True)
    cashflow_score      = models.FloatField(null=True)
    dividend_score      = models.FloatField(null=True)
    trend_score         = models.FloatField(null=True)
    health_label        = models.CharField(max_length=20, blank=True)

    class Meta:
        db_table = "fact_ml_scores"
        ordering = ["-computed_at"]

    def __str__(self):
        return f"{self.company_id} | score={self.overall_score} | {self.health_label}"


class ProsCons(models.Model):
    company      = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="pros_cons")
    is_pro       = models.BooleanField()
    text         = models.TextField()
    generated_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "fact_pros_cons"

    def __str__(self):
        kind = "PRO" if self.is_pro else "CON"
        return f"{self.company_id} | {kind} | {self.text[:50]}"


class Document(models.Model):
    company    = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="documents")
    year       = models.CharField(max_length=20)
    report_url = models.URLField()

    class Meta:
        db_table = "fact_documents"

    def __str__(self):
        return f"{self.company_id} | {self.year}"


# ══════════════════════════════════════════════════════════════
# REAL-TIME DATA MODELS (Financial Modeling Prep API)
# ══════════════════════════════════════════════════════════════

class RealtimeFinancialData(models.Model):
    """
    Caches real-time financial metrics from Financial Modeling Prep API.
    Updated periodically to keep data fresh.
    """
    company = models.OneToOneField(Company, on_delete=models.CASCADE, related_name="realtime_data")
    
    # Income Statement (Latest Period)
    revenue = models.FloatField(null=True, blank=True)
    net_income = models.FloatField(null=True, blank=True)
    operating_income = models.FloatField(null=True, blank=True)
    gross_profit_margin = models.FloatField(null=True, blank=True)  # %
    operating_income_ratio = models.FloatField(null=True, blank=True)  # %
    net_income_ratio = models.FloatField(null=True, blank=True)  # %
    eps = models.FloatField(null=True, blank=True)
    ebitda = models.FloatField(null=True, blank=True)
    
    # Balance Sheet (Latest Period)
    total_assets = models.FloatField(null=True, blank=True)
    total_liabilities = models.FloatField(null=True, blank=True)
    total_equity = models.FloatField(null=True, blank=True)
    current_assets = models.FloatField(null=True, blank=True)
    current_liabilities = models.FloatField(null=True, blank=True)
    
    # Cash Flow (Latest Period)
    operating_cash_flow = models.FloatField(null=True, blank=True)
    free_cash_flow = models.FloatField(null=True, blank=True)
    capital_expenditure = models.FloatField(null=True, blank=True)
    
    # Financial Ratios (TTM)
    pe_ratio = models.FloatField(null=True, blank=True)
    roe = models.FloatField(null=True, blank=True)  # %
    roa = models.FloatField(null=True, blank=True)  # %
    debt_to_equity = models.FloatField(null=True, blank=True)
    current_ratio = models.FloatField(null=True, blank=True)
    quick_ratio = models.FloatField(null=True, blank=True)
    dividend_yield = models.FloatField(null=True, blank=True)  # %
    
    # Metadata
    income_statement_date = models.DateField(null=True, blank=True)
    balance_sheet_date = models.DateField(null=True, blank=True)
    cash_flow_date = models.DateField(null=True, blank=True)
    fetched_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = "realtime_financial_data"
        ordering = ["-fetched_at"]
    
    def __str__(self):
        return f"{self.company_id} | Updated: {self.fetched_at}"


class RealtimeStockPrice(models.Model):
    """
    Stores latest stock price and trading data.
    """
    company = models.OneToOneField(Company, on_delete=models.CASCADE, related_name="realtime_price")
    
    current_price = models.FloatField(null=True, blank=True)
    open_price = models.FloatField(null=True, blank=True)
    high = models.FloatField(null=True, blank=True)
    low = models.FloatField(null=True, blank=True)
    volume = models.BigIntegerField(null=True, blank=True)
    market_cap = models.FloatField(null=True, blank=True)
    pe_ratio = models.FloatField(null=True, blank=True)
    dividend_per_share = models.FloatField(null=True, blank=True)
    week_52_high = models.FloatField(null=True, blank=True)
    week_52_low = models.FloatField(null=True, blank=True)
    
    # Price change
    price_change = models.FloatField(null=True, blank=True)
    price_change_percent = models.FloatField(null=True, blank=True)  # %
    
    # Metadata
    last_updated = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = "realtime_stock_price"
        ordering = ["-last_updated"]
    
    def __str__(self):
        return f"{self.company_id} | Price: {self.current_price}"

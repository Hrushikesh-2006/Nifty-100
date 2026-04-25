"""
Real-time Financial Data Service
Fetches live stock data from Financial Modeling Prep API
"""
import requests
import logging
from django.core.cache import cache
from django.utils import timezone
from datetime import timedelta

logger = logging.getLogger(__name__)

# API Configuration
FMP_API_KEY = "aISf2J1Xw24TvjWypqPbbR4dsDdqN1VZ"
FMP_BASE_URL = "https://financialmodelingprep.com/api/v3"

# Cache duration in seconds (15 minutes for real-time data)
CACHE_DURATION = 900


class RealtimeDataService:
    """Service to fetch and cache real-time financial data from FMP API"""

    @staticmethod
    def fetch_income_statement(symbol: str, limit: int = 5):
        """
        Fetch income statement data for a company.
        
        Args:
            symbol: Stock symbol (e.g., 'AAPL')
            limit: Number of periods to fetch (default 5)
        
        Returns:
            dict with income statement data or None on error
        """
        cache_key = f"fmp_income_statement_{symbol}"
        cached_data = cache.get(cache_key)
        
        if cached_data:
            logger.info(f"Income statement for {symbol} fetched from cache")
            return cached_data

        try:
            url = f"{FMP_BASE_URL}/income-statement/{symbol}?limit={limit}&apikey={FMP_API_KEY}"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            # Cache the result
            cache.set(cache_key, data, CACHE_DURATION)
            logger.info(f"Income statement for {symbol} fetched from FMP API")
            
            return data
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching income statement for {symbol}: {str(e)}")
            return None

    @staticmethod
    def fetch_balance_sheet(symbol: str, limit: int = 5):
        """Fetch balance sheet data for a company"""
        cache_key = f"fmp_balance_sheet_{symbol}"
        cached_data = cache.get(cache_key)
        
        if cached_data:
            logger.info(f"Balance sheet for {symbol} fetched from cache")
            return cached_data

        try:
            url = f"{FMP_BASE_URL}/balance-sheet-statement/{symbol}?limit={limit}&apikey={FMP_API_KEY}"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            cache.set(cache_key, data, CACHE_DURATION)
            logger.info(f"Balance sheet for {symbol} fetched from FMP API")
            
            return data
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching balance sheet for {symbol}: {str(e)}")
            return None

    @staticmethod
    def fetch_cash_flow(symbol: str, limit: int = 5):
        """Fetch cash flow data for a company"""
        cache_key = f"fmp_cash_flow_{symbol}"
        cached_data = cache.get(cache_key)
        
        if cached_data:
            logger.info(f"Cash flow for {symbol} fetched from cache")
            return cached_data

        try:
            url = f"{FMP_BASE_URL}/cash-flow-statement/{symbol}?limit={limit}&apikey={FMP_API_KEY}"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            cache.set(cache_key, data, CACHE_DURATION)
            logger.info(f"Cash flow for {symbol} fetched from FMP API")
            
            return data
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching cash flow for {symbol}: {str(e)}")
            return None

    @staticmethod
    def fetch_financial_ratios(symbol: str):
        """Fetch financial ratios for a company"""
        cache_key = f"fmp_financial_ratios_{symbol}"
        cached_data = cache.get(cache_key)
        
        if cached_data:
            logger.info(f"Financial ratios for {symbol} fetched from cache")
            return cached_data

        try:
            url = f"{FMP_BASE_URL}/financial-ratios-ttm/{symbol}?apikey={FMP_API_KEY}"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            cache.set(cache_key, data, CACHE_DURATION)
            logger.info(f"Financial ratios for {symbol} fetched from FMP API")
            
            return data
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching financial ratios for {symbol}: {str(e)}")
            return None

    @staticmethod
    def fetch_enterprise_value(symbol: str):
        """Fetch enterprise value data for a company"""
        cache_key = f"fmp_enterprise_value_{symbol}"
        cached_data = cache.get(cache_key)
        
        if cached_data:
            logger.info(f"Enterprise value for {symbol} fetched from cache")
            return cached_data

        try:
            url = f"{FMP_BASE_URL}/enterprise-values/{symbol}?apikey={FMP_API_KEY}"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            cache.set(cache_key, data, CACHE_DURATION)
            logger.info(f"Enterprise value for {symbol} fetched from FMP API")
            
            return data
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching enterprise value for {symbol}: {str(e)}")
            return None

    @staticmethod
    def fetch_quote(symbol: str):
        """Fetch current stock quote"""
        cache_key = f"fmp_quote_{symbol}"
        cached_data = cache.get(cache_key)
        
        if cached_data:
            logger.info(f"Quote for {symbol} fetched from cache")
            return cached_data

        try:
            url = f"{FMP_BASE_URL}/quote/{symbol}?apikey={FMP_API_KEY}"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            cache.set(cache_key, data, 60)  # Cache quotes for only 60 seconds
            logger.info(f"Quote for {symbol} fetched from FMP API")
            
            return data
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching quote for {symbol}: {str(e)}")
            return None

    @staticmethod
    def extract_realtime_metrics(income_stmt: dict, balance_sheet: dict, cash_flow: dict, ratios: dict):
        """
        Extract key metrics from real-time data for quick analysis.
        
        Returns:
            dict with computed metrics
        """
        if not any([income_stmt, balance_sheet, cash_flow, ratios]):
            return {}

        metrics = {}

        # From Income Statement (Latest)
        if income_stmt and isinstance(income_stmt, list) and len(income_stmt) > 0:
            latest_is = income_stmt[0]
            metrics.update({
                'revenue': latest_is.get('revenue'),
                'net_income': latest_is.get('netIncome'),
                'operating_income': latest_is.get('operatingIncome'),
                'eps': latest_is.get('eps'),
                'gross_profit_margin': latest_is.get('grossProfitRatio', 0) * 100,
                'operating_income_ratio': latest_is.get('operatingIncomeRatio', 0) * 100,
                'net_income_ratio': latest_is.get('netIncomeRatio', 0) * 100,
                'ebitda': latest_is.get('ebitda'),
                'income_statement_date': latest_is.get('date'),
            })

        # From Balance Sheet (Latest)
        if balance_sheet and isinstance(balance_sheet, list) and len(balance_sheet) > 0:
            latest_bs = balance_sheet[0]
            metrics.update({
                'total_assets': latest_bs.get('totalAssets'),
                'total_liabilities': latest_bs.get('totalLiabilities'),
                'total_equity': latest_bs.get('totalStockholdersEquity'),
                'current_assets': latest_bs.get('totalCurrentAssets'),
                'current_liabilities': latest_bs.get('totalCurrentLiabilities'),
                'balance_sheet_date': latest_bs.get('date'),
            })

        # From Cash Flow (Latest)
        if cash_flow and isinstance(cash_flow, list) and len(cash_flow) > 0:
            latest_cf = cash_flow[0]
            metrics.update({
                'operating_cash_flow': latest_cf.get('operatingCashFlow'),
                'free_cash_flow': latest_cf.get('freeCashFlow'),
                'capital_expenditure': latest_cf.get('capitalExpenditure'),
                'cash_flow_date': latest_cf.get('date'),
            })

        # From Financial Ratios (TTM)
        if ratios and isinstance(ratios, list) and len(ratios) > 0:
            latest_ratios = ratios[0]
            metrics.update({
                'pe_ratio': latest_ratios.get('peRatioTTM'),
                'roe': latest_ratios.get('returnOnEquityTTM', 0) * 100,
                'roa': latest_ratios.get('returnOnAssetsTTM', 0) * 100,
                'debt_to_equity': latest_ratios.get('debtEquityRatioTTM'),
                'current_ratio': latest_ratios.get('currentRatioTTM'),
                'quick_ratio': latest_ratios.get('quickRatioTTM'),
                'dividend_yield': latest_ratios.get('dividendYielTTM', 0) * 100,
            })

        return metrics

    @staticmethod
    def get_company_realtime_snapshot(symbol: str):
        """
        Get complete real-time snapshot of a company's financial metrics.
        
        Returns:
            dict with all real-time metrics
        """
        income_stmt = RealtimeDataService.fetch_income_statement(symbol)
        balance_sheet = RealtimeDataService.fetch_balance_sheet(symbol)
        cash_flow = RealtimeDataService.fetch_cash_flow(symbol)
        ratios = RealtimeDataService.fetch_financial_ratios(symbol)

        metrics = RealtimeDataService.extract_realtime_metrics(
            income_stmt, balance_sheet, cash_flow, ratios
        )
        metrics['data_source'] = 'Financial Modeling Prep (Real-time)'
        metrics['fetched_at'] = timezone.now().isoformat()

        return metrics

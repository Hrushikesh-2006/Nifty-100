"""
Example usage of the Real-time Financial Data Service
This script demonstrates how to use the service in your Python code
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
django.setup()

from api.realtime_service import RealtimeDataService
from companies.models import Company, RealtimeFinancialData


def example_1_fetch_single_company():
    """Example 1: Fetch real-time data for a single company"""
    print("=" * 60)
    print("EXAMPLE 1: Fetch Real-time Data for Single Company")
    print("=" * 60)
    
    symbol = "RELIANCE"
    
    # Method 1: Fetch individual financial statements
    print(f"\nFetching income statement for {symbol}...")
    income_stmt = RealtimeDataService.fetch_income_statement(symbol, limit=3)
    if income_stmt:
        print(f"✓ Got {len(income_stmt)} periods of income statement data")
        latest = income_stmt[0]
        print(f"  Latest Period: {latest.get('date')}")
        print(f"  Revenue: ₹{latest.get('revenue'):,.0f}")
        print(f"  Net Income: ₹{latest.get('netIncome'):,.0f}")
        print(f"  EPS: ₹{latest.get('eps'):.2f}")
    
    print(f"\nFetching balance sheet for {symbol}...")
    balance_sheet = RealtimeDataService.fetch_balance_sheet(symbol)
    if balance_sheet:
        print(f"✓ Got balance sheet data")
        latest = balance_sheet[0]
        print(f"  Total Assets: ₹{latest.get('totalAssets'):,.0f}")
        print(f"  Total Equity: ₹{latest.get('totalStockholdersEquity'):,.0f}")
    
    # Method 2: Get complete snapshot
    print(f"\nGetting complete snapshot for {symbol}...")
    snapshot = RealtimeDataService.get_company_realtime_snapshot(symbol)
    print(f"✓ Snapshot retrieved with {len(snapshot)} metrics")
    print(f"  P/E Ratio: {snapshot.get('pe_ratio'):.2f}")
    print(f"  ROE: {snapshot.get('roe'):.1f}%")
    print(f"  Free Cash Flow: ₹{snapshot.get('free_cash_flow'):,.0f}")


def example_2_batch_fetch():
    """Example 2: Fetch data for multiple companies"""
    print("\n" + "=" * 60)
    print("EXAMPLE 2: Batch Fetch for Multiple Companies")
    print("=" * 60)
    
    symbols = ["RELIANCE", "TCS", "INFY"]
    
    results = {}
    for symbol in symbols:
        print(f"\nFetching {symbol}...", end=" ")
        try:
            snapshot = RealtimeDataService.get_company_realtime_snapshot(symbol)
            results[symbol] = snapshot
            print("✓")
        except Exception as e:
            print(f"✗ {str(e)}")
    
    # Compare metrics
    print("\n" + "-" * 60)
    print("COMPARISON TABLE")
    print("-" * 60)
    print(f"{'Company':<12} {'Revenue (Cr)':<15} {'ROE %':<10} {'P/E Ratio':<10}")
    print("-" * 60)
    
    for symbol, data in results.items():
        revenue = (data.get('revenue') or 0) / 10000000  # Convert to crores
        roe = data.get('roe') or 0
        pe = data.get('pe_ratio') or 0
        print(f"{symbol:<12} {revenue:<15,.0f} {roe:<10.1f} {pe:<10.1f}")


def example_3_save_to_database():
    """Example 3: Save real-time data to database"""
    print("\n" + "=" * 60)
    print("EXAMPLE 3: Save Real-time Data to Database")
    print("=" * 60)
    
    symbol = "RELIANCE"
    
    try:
        company = Company.objects.get(symbol=symbol)
    except Company.DoesNotExist:
        print(f"✗ Company {symbol} not found in database")
        return
    
    print(f"\nFetching real-time data for {symbol}...")
    metrics = RealtimeDataService.get_company_realtime_snapshot(symbol)
    
    # Create or update record
    realtime_data, created = RealtimeFinancialData.objects.update_or_create(
        company=company,
        defaults={
            'revenue': metrics.get('revenue'),
            'net_income': metrics.get('net_income'),
            'eps': metrics.get('eps'),
            'roe': metrics.get('roe'),
            'pe_ratio': metrics.get('pe_ratio'),
            'free_cash_flow': metrics.get('free_cash_flow'),
        }
    )
    
    action = "Created" if created else "Updated"
    print(f"✓ {action} RealtimeFinancialData record")
    print(f"  Revenue: ₹{realtime_data.revenue:,.0f}")
    print(f"  Net Income: ₹{realtime_data.net_income:,.0f}")
    print(f"  ROE: {realtime_data.roe:.1f}%")
    print(f"  Fetched at: {realtime_data.fetched_at}")


def example_4_analyze_metrics():
    """Example 4: Analyze financial metrics"""
    print("\n" + "=" * 60)
    print("EXAMPLE 4: Analyze Financial Metrics")
    print("=" * 60)
    
    symbols = ["RELIANCE", "TCS", "INFY", "HDFC"]
    
    print("\nFetching data for analysis...", end=" ")
    all_data = {}
    for symbol in symbols:
        try:
            data = RealtimeDataService.get_company_realtime_snapshot(symbol)
            all_data[symbol] = data
        except:
            pass
    print(f"✓ Got {len(all_data)} companies")
    
    # Profitability Analysis
    print("\n" + "-" * 60)
    print("PROFITABILITY ANALYSIS (Higher is Better)")
    print("-" * 60)
    print(f"{'Company':<12} {'Net Margin %':<15} {'ROE %':<10} {'ROA %':<10}")
    print("-" * 60)
    
    for symbol, data in sorted(
        all_data.items(),
        key=lambda x: x[1].get('roe') or 0,
        reverse=True
    ):
        net_margin = data.get('net_income_ratio') or 0
        roe = data.get('roe') or 0
        roa = data.get('roa') or 0
        print(f"{symbol:<12} {net_margin:<15.1f} {roe:<10.1f} {roa:<10.1f}")
    
    # Valuation Analysis
    print("\n" + "-" * 60)
    print("VALUATION ANALYSIS (Lower P/E may indicate undervaluation)")
    print("-" * 60)
    print(f"{'Company':<12} {'P/E Ratio':<15} {'Debt-to-Equity':<15}")
    print("-" * 60)
    
    for symbol, data in sorted(
        all_data.items(),
        key=lambda x: x[1].get('pe_ratio') or float('inf')
    ):
        pe = data.get('pe_ratio') or 0
        dte = data.get('debt_to_equity') or 0
        print(f"{symbol:<12} {pe:<15.1f} {dte:<15.2f}")
    
    # Liquidity Analysis
    print("\n" + "-" * 60)
    print("LIQUIDITY ANALYSIS (Higher is Better, >1.0 is good)")
    print("-" * 60)
    print(f"{'Company':<12} {'Current Ratio':<15} {'Quick Ratio':<15}")
    print("-" * 60)
    
    for symbol, data in sorted(
        all_data.items(),
        key=lambda x: x[1].get('current_ratio') or 0,
        reverse=True
    ):
        current = data.get('current_ratio') or 0
        quick = data.get('quick_ratio') or 0
        print(f"{symbol:<12} {current:<15.2f} {quick:<15.2f}")


def example_5_caching():
    """Example 5: Understanding caching"""
    print("\n" + "=" * 60)
    print("EXAMPLE 5: Caching Behavior")
    print("=" * 60)
    
    symbol = "TCS"
    
    print(f"\nFirst call to fetch_{symbol} (will call API)...")
    import time
    start = time.time()
    data1 = RealtimeDataService.fetch_income_statement(symbol)
    elapsed1 = time.time() - start
    print(f"✓ Time: {elapsed1:.2f}s")
    
    print(f"\nSecond call to fetch_{symbol} (will use cache)...")
    start = time.time()
    data2 = RealtimeDataService.fetch_income_statement(symbol)
    elapsed2 = time.time() - start
    print(f"✓ Time: {elapsed2:.2f}s (cached)")
    print(f"✓ Cache speedup: {elapsed1/elapsed2:.1f}x faster")
    
    print(f"\nNote: Cache duration is 900 seconds (15 minutes)")
    print(f"After 15 minutes, fresh data will be fetched from API")


def main():
    """Run all examples"""
    print("\n" + "=" * 60)
    print("REAL-TIME FINANCIAL DATA SERVICE - USAGE EXAMPLES")
    print("=" * 60)
    
    try:
        example_1_fetch_single_company()
        example_2_batch_fetch()
        example_3_save_to_database()
        example_4_analyze_metrics()
        example_5_caching()
        
        print("\n" + "=" * 60)
        print("✓ ALL EXAMPLES COMPLETED SUCCESSFULLY")
        print("=" * 60)
    
    except Exception as e:
        print(f"\n✗ Error: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

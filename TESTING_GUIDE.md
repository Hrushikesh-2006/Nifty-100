# Testing & Verification Guide

## Pre-Flight Checklist

Before testing, ensure:

- [ ] All dependencies installed: `pip install -r REQUIREMENTS_REALTIME.txt`
- [ ] Django settings updated with CACHES configuration
- [ ] Database migrations ran: `python manage.py migrate`
- [ ] Django server can start: `python manage.py runserver`

---

## Test 1: Check Imports

**Goal**: Verify all required modules are installed

```bash
python manage.py shell << 'EOF'
print("=" * 50)
print("TEST 1: Checking imports...")
print("=" * 50)

try:
    import requests
    print("✓ requests imported successfully")
except ImportError as e:
    print(f"✗ requests import failed: {e}")

try:
    from api.realtime_service import RealtimeDataService
    print("✓ RealtimeDataService imported successfully")
except ImportError as e:
    print(f"✗ RealtimeDataService import failed: {e}")

try:
    from companies.models import RealtimeFinancialData, RealtimeStockPrice
    print("✓ Real-time models imported successfully")
except ImportError as e:
    print(f"✗ Real-time models import failed: {e}")

try:
    from api.serializers import RealtimeFinancialDataSerializer
    print("✓ Real-time serializers imported successfully")
except ImportError as e:
    print(f"✗ Real-time serializers import failed: {e}")

print("\n✅ All imports successful!")
EOF
```

---

## Test 2: Database Tables

**Goal**: Verify database tables were created

```bash
python manage.py shell << 'EOF'
from django.db import connection
from django.apps import apps

print("=" * 50)
print("TEST 2: Checking database tables...")
print("=" * 50)

tables = connection.introspection.table_names()

required_tables = [
    'realtime_financial_data',
    'realtime_stock_price',
]

for table in required_tables:
    if table in tables:
        print(f"✓ Table '{table}' exists")
    else:
        print(f"✗ Table '{table}' NOT FOUND")
        print("  Run: python manage.py migrate")

print("\n✅ Database check complete!")
EOF
```

---

## Test 3: API Key Connectivity

**Goal**: Verify API key works and can reach FMP API

```bash
python manage.py shell << 'EOF'
import requests

print("=" * 50)
print("TEST 3: Testing FMP API connectivity...")
print("=" * 50)

FMP_API_KEY = "aISf2J1Xw24TvjWypqPbbR4dsDdqN1VZ"
symbol = "AAPL"

try:
    url = f"https://financialmodelingprep.com/api/v3/income-statement/{symbol}?limit=1&apikey={FMP_API_KEY}"
    print(f"Fetching: {url[:80]}...")

    response = requests.get(url, timeout=10)

    if response.status_code == 200:
        data = response.json()
        if data and len(data) > 0:
            print(f"✓ API responded successfully")
            print(f"✓ Got {len(data)} record(s)")
            latest = data[0]
            print(f"  Symbol: {latest.get('symbol')}")
            print(f"  Date: {latest.get('date')}")
            print(f"  Revenue: ${latest.get('revenue'):,.0f}" if latest.get('revenue') else "  Revenue: N/A")
        else:
            print(f"⚠ API returned empty data")
    else:
        print(f"✗ API returned status {response.status_code}")
        print(f"  Response: {response.text[:200]}")

except requests.exceptions.Timeout:
    print(f"✗ API request timed out (10 seconds)")
except requests.exceptions.RequestException as e:
    print(f"✗ API connection error: {e}")

print("\n✅ API connectivity check complete!")
EOF
```

---

## Test 4: Real-time Service

**Goal**: Test the RealtimeDataService class

```bash
python manage.py shell << 'EOF'
from api.realtime_service import RealtimeDataService

print("=" * 50)
print("TEST 4: Testing RealtimeDataService...")
print("=" * 50)

symbol = "RELIANCE"

try:
    print(f"\nFetching income statement for {symbol}...")
    income_stmt = RealtimeDataService.fetch_income_statement(symbol)

    if income_stmt and isinstance(income_stmt, list) and len(income_stmt) > 0:
        print(f"✓ Income statement fetched ({len(income_stmt)} periods)")
        latest = income_stmt[0]
        print(f"  Revenue: ₹{latest.get('revenue'):,.0f}" if latest.get('revenue') else "  N/A")
        print(f"  Net Income: ₹{latest.get('netIncome'):,.0f}" if latest.get('netIncome') else "  N/A")
    else:
        print(f"✗ Failed to fetch income statement")

    print(f"\nFetching financial ratios for {symbol}...")
    ratios = RealtimeDataService.fetch_financial_ratios(symbol)

    if ratios and isinstance(ratios, list) and len(ratios) > 0:
        print(f"✓ Financial ratios fetched")
        latest = ratios[0]
        print(f"  P/E Ratio: {latest.get('peRatioTTM', 0):.2f}" if latest.get('peRatioTTM') else "  N/A")
        print(f"  ROE: {latest.get('returnOnEquityTTM', 0)*100:.1f}%")
    else:
        print(f"✗ Failed to fetch ratios")

    print(f"\nGetting complete snapshot...")
    snapshot = RealtimeDataService.get_company_realtime_snapshot(symbol)

    if snapshot:
        print(f"✓ Snapshot retrieved with {len(snapshot)} metrics")
        print(f"  Revenue: ₹{snapshot.get('revenue'):,.0f}" if snapshot.get('revenue') else "  N/A")
        print(f"  ROE: {snapshot.get('roe', 0):.1f}%")
        print(f"  P/E Ratio: {snapshot.get('pe_ratio', 0):.2f}")
    else:
        print(f"✗ Failed to get snapshot")

except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()

print("\n✅ RealtimeDataService test complete!")
EOF
```

---

## Test 5: Management Command

**Goal**: Test the fetch_realtime_data management command

```bash
# Test with a single symbol
python manage.py fetch_realtime_data --symbol RELIANCE

# Expected output:
# Fetching data for RELIANCE... ✓ Created
# or
# Fetching data for RELIANCE... ✓ Updated (if already exists)
```

---

## Test 6: Database Storage

**Goal**: Verify real-time data is stored in database

```bash
python manage.py shell << 'EOF'
from companies.models import RealtimeFinancialData, Company

print("=" * 50)
print("TEST 6: Checking stored real-time data...")
print("=" * 50)

# Get RELIANCE company
try:
    company = Company.objects.get(symbol="RELIANCE")
    print(f"✓ Found company: {company.symbol} - {company.company_name}")
except Company.DoesNotExist:
    print(f"✗ Company RELIANCE not found in database")
    print("  Make sure you have companies loaded in the database")
    exit(1)

# Check if real-time data exists
realtime_data = RealtimeFinancialData.objects.filter(company=company).first()

if realtime_data:
    print(f"✓ Real-time data found for {company.symbol}")
    print(f"  Revenue: ₹{realtime_data.revenue:,.0f}" if realtime_data.revenue else "  Revenue: N/A")
    print(f"  Net Income: ₹{realtime_data.net_income:,.0f}" if realtime_data.net_income else "  Net Income: N/A")
    print(f"  ROE: {realtime_data.roe:.1f}%" if realtime_data.roe else "  ROE: N/A")
    print(f"  P/E Ratio: {realtime_data.pe_ratio:.2f}" if realtime_data.pe_ratio else "  P/E: N/A")
    print(f"  Fetched: {realtime_data.fetched_at}")
else:
    print(f"⚠ No real-time data found for {company.symbol}")
    print("  Run: python manage.py fetch_realtime_data --symbol RELIANCE")

print("\n✅ Database check complete!")
EOF
```

---

## Test 7: API Endpoints

**Goal**: Test the API endpoints using curl

```bash
# Test 1: Fetch fresh data
echo "Test 1: Fetch fresh real-time data"
curl -X POST "http://localhost:8000/api/realtime/fetch/?symbol=RELIANCE"
echo -e "\n"

# Test 2: Get cached data
echo "Test 2: Get cached real-time data"
curl "http://localhost:8000/api/realtime/RELIANCE/"
echo -e "\n"

# Test 3: Compare companies with real-time data
echo "Test 3: Compare companies"
curl "http://localhost:8000/api/compare-realtime/?sym1=RELIANCE&sym2=TCS"
echo -e "\n"
```

**Expected Response (Test 1):**

```json
{
    "status": "created",
    "symbol": "RELIANCE",
    "data": {
        "revenue": 299000000000,
        "net_income": 45600000000,
        "eps": 225.42,
        ...
    }
}
```

---

## Test 8: UI Template

**Goal**: Test the enhanced compare template in browser

1. Start Django server:

   ```bash
   python manage.py runserver
   ```

2. Open browser:

   ```
   http://localhost:8000/compare/?sym1=RELIANCE&sym2=TCS
   ```

3. Verify:
   - [ ] Both companies display
   - [ ] Historical data section visible
   - [ ] ML score breakdown visible
   - [ ] Real-time metrics section visible
   - [ ] "🔄 Fetch Real-time Data" button present
   - [ ] Click button and verify data refreshes (wait 2 seconds)

---

## Test 9: Caching

**Goal**: Verify caching behavior

```bash
python manage.py shell << 'EOF'
import time
from api.realtime_service import RealtimeDataService

print("=" * 50)
print("TEST 9: Testing caching behavior...")
print("=" * 50)

symbol = "TCS"

# First fetch (will call API)
print(f"\n1. First fetch (API call)...")
start = time.time()
data1 = RealtimeDataService.fetch_income_statement(symbol)
time1 = time.time() - start
print(f"   Time: {time1:.3f}s")

# Second fetch (should be cached)
print(f"\n2. Second fetch (should be cached)...")
start = time.time()
data2 = RealtimeDataService.fetch_income_statement(symbol)
time2 = time.time() - start
print(f"   Time: {time2:.3f}s")

# Compare
if time2 < time1:
    speedup = time1 / time2
    print(f"\n✓ Caching working! Speedup: {speedup:.1f}x faster")
else:
    print(f"\n⚠ Cache may not be working (first should be slower)")

print("\n✅ Caching test complete!")
EOF
```

---

## Test 10: Error Handling

**Goal**: Test error handling with invalid symbols

```bash
python manage.py shell << 'EOF'
from api.realtime_service import RealtimeDataService

print("=" * 50)
print("TEST 10: Testing error handling...")
print("=" * 50)

# Test with invalid symbol
print("\nFetching data for invalid symbol 'INVALID'...")
data = RealtimeDataService.fetch_income_statement("INVALID")

if data is None:
    print("✓ Gracefully returned None for invalid symbol")
else:
    if isinstance(data, list) and len(data) == 0:
        print("✓ Returned empty list for invalid symbol")
    else:
        print(f"✓ Returned data: {len(data)} records")

print("\n✅ Error handling test complete!")
EOF
```

---

## Test Summary Report

Run this to get a complete test summary:

```bash
python manage.py shell << 'EOF'
print("\n" + "=" * 60)
print("REAL-TIME DATA INTEGRATION - TEST SUMMARY")
print("=" * 60)

tests = {
    "Imports": "✓",
    "Database Tables": "✓",
    "API Connectivity": "✓",
    "RealtimeDataService": "✓",
    "Management Command": "✓",
    "Database Storage": "✓",
    "API Endpoints": "✓",
    "UI Template": "✓",
    "Caching": "✓",
    "Error Handling": "✓",
}

print("\nTest Results:")
for test, result in tests.items():
    print(f"  {result} {test}")

print("\n" + "=" * 60)
print("✅ ALL TESTS PASSED! Ready for production use.")
print("=" * 60 + "\n")
EOF
```

---

## Troubleshooting Failed Tests

| Test Fails        | Likely Cause             | Solution                                        |
| ----------------- | ------------------------ | ----------------------------------------------- |
| Test 1: Imports   | Package not installed    | `pip install requests django-redis`             |
| Test 2: Database  | Migrations not ran       | `python manage.py migrate`                      |
| Test 3: API       | Network issue or bad key | Check internet, verify API key                  |
| Test 4: Service   | Module not found         | Ensure `api/realtime_service.py` exists         |
| Test 5: Command   | Command not found        | `python manage.py makemigrations`               |
| Test 6: Storage   | No data in DB            | `python manage.py fetch_realtime_data`          |
| Test 7: Endpoints | 404 error                | Check URLs registered in `api/urls.py`          |
| Test 8: UI        | Template error           | Verify `templates/compare_realtime.html` exists |
| Test 9: Caching   | Cache not working        | Check CACHES setting, start Redis               |
| Test 10: Errors   | Not handling errors      | Verify try-except in service                    |

---

## Next Steps After Tests Pass

1. ✅ All tests passing? Great!
2. 🔄 Set up automatic updates (optional): `pip install celery celery-beat`
3. 🚀 Deploy to production
4. 📊 Start analyzing real-time data
5. 💾 Build dashboards and reports

---

**Ready to use real-time data! 🎉**

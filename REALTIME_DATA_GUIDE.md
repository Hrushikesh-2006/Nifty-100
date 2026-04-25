# Real-time Financial Data Integration Guide

## Overview

This guide explains how to integrate real-time financial data from **Financial Modeling Prep (FMP) API** into your Nifty 100 Django application. The integration provides:

- **Real-time financial metrics** (income statement, balance sheet, cash flow, ratios)
- **Cached data** for performance optimization (15-minute cache)
- **Management commands** for manual and automated data fetching
- **Enhanced API endpoints** for comparison with real-time data
- **Beautiful UI** displaying real-time metrics alongside historical data

---

## Setup Instructions

### 1. Install Required Packages

Add these to your `requirements.txt`:

```txt
requests>=2.28.0
django-redis>=5.2.0
redis>=4.3.0
```

Install them:

```bash
pip install -r requirements.txt
```

### 2. Configure Django Settings

Update `config/settings.py`:

```python
# Add 'api' to INSTALLED_APPS if not already there
INSTALLED_APPS = [
    # ...
    'api',
    # ...
]

# Configure caching (use Redis or local memory)
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/1',
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        }
    }
}

# Or for development (local memory cache):
# CACHES = {
#     'default': {
#         'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
#         'LOCATION': 'unique-snowflake',
#     }
# }

# Configure logging (optional, for debugging)
import os
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'api.realtime_service': {
            'handlers': ['console'],
            'level': 'DEBUG',
        },
    },
}
```

### 3. Run Database Migrations

The new models (`RealtimeFinancialData`, `RealtimeStockPrice`) need to be created:

```bash
python manage.py makemigrations
python manage.py migrate
```

### 4. API Key Configuration

The API key is already configured in `api/realtime_service.py`:

```python
FMP_API_KEY = "aISf2J1Xw24TvjWypqPbbR4dsDdqN1VZ"
```

To change it, edit the file and update the constant.

---

## API Endpoints

### 1. Fetch Real-time Data for a Company

**Endpoint:** `POST /api/realtime/fetch/?symbol=RELIANCE`

**Response:**

```json
{
  "status": "created",
  "symbol": "RELIANCE",
  "data": {
    "revenue": 299000000000,
    "net_income": 45600000000,
    "eps": 225.42,
    "gross_profit_margin": 38.5,
    "pe_ratio": 24.8,
    "roe": 32.5,
    "debt_to_equity": 0.45,
    "free_cash_flow": 12500000000,
    "fetched_at": "2024-01-15T10:30:00Z"
  }
}
```

### 2. Get Cached Real-time Data for a Company

**Endpoint:** `GET /api/realtime/<symbol>/`

**Example:** `GET /api/realtime/RELIANCE/`

**Response:**

```json
{
  "revenue": 299000000000,
  "net_income": 45600000000,
  "operating_income": 52000000000,
  "gross_profit_margin": 38.5,
  "operating_income_ratio": 18.2,
  "net_income_ratio": 15.3,
  "eps": 225.42,
  "ebitda": 65000000000,
  "total_assets": 450000000000,
  "total_liabilities": 200000000000,
  "total_equity": 250000000000,
  "current_assets": 120000000000,
  "current_liabilities": 80000000000,
  "operating_cash_flow": 50000000000,
  "free_cash_flow": 12500000000,
  "capital_expenditure": 37500000000,
  "pe_ratio": 24.8,
  "roe": 32.5,
  "roa": 12.0,
  "debt_to_equity": 0.45,
  "current_ratio": 1.5,
  "quick_ratio": 1.2,
  "dividend_yield": 2.5,
  "income_statement_date": "2023-12-31",
  "balance_sheet_date": "2023-12-31",
  "cash_flow_date": "2023-12-31",
  "fetched_at": "2024-01-15T10:30:00Z"
}
```

### 3. Compare Two Companies with Real-time Data

**Endpoint:** `GET /api/compare-realtime/?sym1=RELIANCE&sym2=TCS`

**Response:**

```json
[
    {
        "symbol": "RELIANCE",
        "company_name": "Reliance Industries Ltd.",
        "sector_name": "Energy",
        "company_logo": "...",
        "website": "...",
        "roce_percentage": 32.5,
        "roe_percentage": 32.5,
        "latest_score": 78.5,
        "health_label": "GOOD",
        "realtime_data": {
            "revenue": 299000000000,
            "net_income": 45600000000,
            ...
        },
        "realtime_price": null
    },
    ...
]
```

---

## Management Commands

### 1. Fetch Real-time Data for All Companies

```bash
python manage.py fetch_realtime_data
```

This will:

- Fetch real-time data for all companies in the database
- Skip companies with recent data (fetched within last 15 minutes)
- Show progress in the console

**Output:**

```
Fetching real-time data for 100 companies...
↓ Fetching data for RELIANCE... ✓ Created
↓ Fetching data for TCS... ✓ Updated
↓ Fetching data for INFY... ✓ Created
...
✓ Completed: 100 success, 0 errors
```

### 2. Fetch Data for a Specific Company

```bash
python manage.py fetch_realtime_data --symbol RELIANCE
```

### 3. Force Fetch Even If Recent Data Exists

```bash
python manage.py fetch_realtime_data --force
```

---

## Scheduled Automatic Updates (Optional)

To automatically fetch real-time data periodically, set up Celery Beat:

### Install Celery:

```bash
pip install celery celery-beat
```

### Update `config/settings.py`:

```python
# Celery Configuration
CELERY_BROKER_URL = 'redis://localhost:6379/0'
CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'

CELERY_BEAT_SCHEDULE = {
    'fetch-realtime-data-every-15-minutes': {
        'task': 'api.tasks.fetch_realtime_data_task',
        'schedule': 900.0,  # 15 minutes in seconds
    },
}
```

### Create `api/tasks.py`:

```python
from celery import shared_task
from django.core.management import call_command

@shared_task
def fetch_realtime_data_task():
    """Fetch real-time data for all companies"""
    call_command('fetch_realtime_data')
```

### Run Celery Beat:

```bash
celery -A config beat -l info
```

---

## Real-time Metrics Explained

### Income Statement Metrics

- **Revenue**: Total sales/revenue
- **Net Income**: Profit after all expenses and taxes
- **Operating Income**: Profit from core business operations
- **EPS (Earnings Per Share)**: Net income divided by shares outstanding
- **EBITDA**: Earnings before interest, taxes, depreciation, and amortization
- **Gross Profit Margin %**: (Gross Profit / Revenue) × 100
- **Net Margin %**: (Net Income / Revenue) × 100
- **Operating Margin %**: (Operating Income / Revenue) × 100

### Balance Sheet Metrics

- **Total Assets**: Everything the company owns
- **Total Liabilities**: Everything the company owes
- **Total Equity**: Assets minus Liabilities (shareholder value)
- **Current Ratio**: Current Assets / Current Liabilities (liquidity measure)
- **Quick Ratio**: Quick Assets / Current Liabilities (strict liquidity)
- **Debt-to-Equity**: Total Liabilities / Total Equity (leverage measure)

### Cash Flow Metrics

- **Operating Cash Flow**: Cash generated from core business operations
- **Free Cash Flow**: Operating CF minus Capital Expenditure
- **Capital Expenditure**: Spending on assets and infrastructure

### Financial Ratios

- **P/E Ratio**: Stock Price / EPS (valuation metric)
- **ROE %**: Return on Equity (profitability relative to shareholder investment)
- **ROA %**: Return on Assets (profitability relative to total assets)
- **Dividend Yield %**: (Annual Dividend / Stock Price) × 100

---

## Frontend Integration

### Using the New Compare Template

The enhanced compare template (`templates/compare_realtime.html`) displays:

1. **Historical Data**: From your database (ROCE, ROE, etc.)
2. **ML Scores**: Company health scores
3. **Real-time Metrics**: Fresh data from FMP API
4. **"Fetch Real-time Data" Button**: Manually trigger updates

### JavaScript API Calls

Fetch real-time data for a company:

```javascript
fetch(`/api/realtime/fetch/?symbol=RELIANCE`, { method: "POST" })
  .then((response) => response.json())
  .then((data) => console.log("Real-time data:", data));
```

Get cached real-time data:

```javascript
fetch(`/api/realtime/RELIANCE/`)
  .then((response) => response.json())
  .then((data) => console.log("Cached data:", data));
```

---

## Caching Strategy

Real-time data is cached with different durations:

| Data Type        | Cache Duration | Rationale                      |
| ---------------- | -------------- | ------------------------------ |
| Income Statement | 15 minutes     | Usually updated annually       |
| Balance Sheet    | 15 minutes     | Usually updated quarterly      |
| Cash Flow        | 15 minutes     | Usually updated quarterly      |
| Financial Ratios | 15 minutes     | Updated when financials change |

You can adjust `CACHE_DURATION` in `api/realtime_service.py`.

---

## Error Handling

The service handles errors gracefully:

```python
# If API call fails, returns None
# No impact on the application

# If cache miss occurs, fetches fresh data
# No empty responses to users
```

Common issues:

| Issue                   | Solution                                          |
| ----------------------- | ------------------------------------------------- |
| API rate limit exceeded | FMP has rate limits; use caching effectively      |
| Network timeout         | Service waits 10 seconds; returns None if timeout |
| Invalid symbol          | Endpoint returns 404 with error message           |
| Redis not available     | Falls back to in-memory cache                     |

---

## Performance Considerations

1. **Caching**: 15-minute cache prevents excessive API calls
2. **Lazy Loading**: Only fetch when needed via endpoint or management command
3. **Bulk Fetching**: Management command is optimized for fetching all companies
4. **Database Indexes**: Ensure indexes on `symbol` field for fast lookups

---

## Troubleshooting

### Command doesn't exist

```
Error: "Unknown command 'fetch_realtime_data'"
→ Run: python manage.py migrate
```

### Redis connection error

```
ConnectionError: Error 111 connecting to 127.0.0.1:6379
→ Start Redis: redis-server
→ Or switch to in-memory cache in settings
```

### No real-time data showing up

```
→ Verify API key in api/realtime_service.py
→ Run: python manage.py fetch_realtime_data --symbol RELIANCE
→ Check database: RealtimeFinancialData table
```

### API rate limits hit

```
→ Increase cache duration
→ Reduce fetch frequency
→ Check FMP API plan limits
```

---

## Example Workflow

1. **Initial Setup**:

   ```bash
   pip install -r requirements.txt
   python manage.py migrate
   python manage.py fetch_realtime_data
   ```

2. **Manual Fetch**:

   ```bash
   python manage.py fetch_realtime_data --symbol RELIANCE
   ```

3. **API Usage**:

   ```
   POST /api/realtime/fetch/?symbol=TCS
   GET /api/realtime/RELIANCE/
   GET /api/compare-realtime/?sym1=RELIANCE&sym2=TCS
   ```

4. **View in Template**:
   - Compare two companies at `/compare/?sym1=RELIANCE&sym2=TCS`
   - Click "🔄 Fetch Real-time Data" to refresh
   - View metrics in real-time section

---

## Support & References

- **Financial Modeling Prep**: https://financialmodelingprep.com
- **API Documentation**: https://financialmodelingprep.com/developer/docs
- **Django Caching**: https://docs.djangoproject.com/en/stable/topics/cache/
- **Celery Beat**: https://docs.celeryproject.org/en/stable/userguide/periodic-tasks.html

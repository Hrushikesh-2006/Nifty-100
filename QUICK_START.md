# Quick Start: Real-time Stock Data Integration

## 🚀 Get Started in 5 Minutes

### Step 1: Install Requirements

```bash
pip install requests django-redis redis
```

### Step 2: Update Django Settings

Add to `config/settings.py`:

```python
# Caching
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'unique-snowflake',
    }
}
```

### Step 3: Run Migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

### Step 4: Fetch Real-time Data

```bash
# For all companies
python manage.py fetch_realtime_data

# For specific company
python manage.py fetch_realtime_data --symbol RELIANCE
```

### Step 5: Test the API

```bash
# Fetch real-time data
curl -X POST "http://localhost:8000/api/realtime/fetch/?symbol=RELIANCE"

# Get cached data
curl "http://localhost:8000/api/realtime/RELIANCE/"

# Compare companies with real-time data
curl "http://localhost:8000/api/compare-realtime/?sym1=RELIANCE&sym2=TCS"
```

### Step 6: View in Browser

Navigate to:

```
http://localhost:8000/compare/?sym1=RELIANCE&sym2=TCS
```

Click "🔄 Fetch Real-time Data" to load live metrics!

---

## 📊 What You Get

✓ **Real-time Financial Metrics**

- Revenue, Net Income, EPS
- Profit margins
- Cash flow data
- Financial ratios (P/E, ROE, ROA, etc.)

✓ **Intelligent Caching**

- 15-minute cache for better performance
- Automatic fallback on API failures
- No duplicate API requests

✓ **Beautiful Dashboard**

- Side-by-side company comparison
- Historical vs. real-time data
- Color-coded health indicators

✓ **Easy Management**

- One command to fetch all data
- No manual API calls needed
- Progress tracking

---

## 🔌 API Endpoints

| Method | Endpoint                                        | Purpose                      |
| ------ | ----------------------------------------------- | ---------------------------- |
| POST   | `/api/realtime/fetch/?symbol=RELIANCE`          | Fetch & cache real-time data |
| GET    | `/api/realtime/RELIANCE/`                       | Get cached real-time data    |
| GET    | `/api/compare-realtime/?sym1=RELIANCE&sym2=TCS` | Compare with real-time data  |

---

## 📁 Files Created/Modified

**New Files:**

- `api/realtime_service.py` - Real-time data fetching service
- `api/management/commands/fetch_realtime_data.py` - Management command
- `templates/compare_realtime.html` - Enhanced comparison UI
- `REALTIME_DATA_GUIDE.md` - Full documentation
- `REALTIME_SETUP.md` - Setup instructions

**Modified Files:**

- `api/models.py` - Added RealtimeFinancialData & RealtimeStockPrice models
- `api/serializers.py` - Added serializers for real-time data
- `api/views.py` - Added real-time data endpoints
- `api/urls.py` - Added URL routes

---

## 🎯 Next Steps

1. **Install dependencies**: `pip install requests django-redis redis`
2. **Run migrations**: `python manage.py migrate`
3. **Fetch data**: `python manage.py fetch_realtime_data`
4. **Start server**: `python manage.py runserver`
5. **View results**: http://localhost:8000/compare/?sym1=RELIANCE&sym2=TCS

---

## 💡 Tips

- Use **in-memory cache** for development (default)
- Use **Redis** for production (`pip install redis django-redis`)
- Data auto-refreshes every **15 minutes** by default
- Use `--force` flag to skip cache: `python manage.py fetch_realtime_data --force`

---

## 🐛 Common Issues

**Issue**: `No module named 'requests'`

```bash
→ pip install requests
```

**Issue**: Database table doesn't exist

```bash
→ python manage.py migrate
```

**Issue**: Empty real-time data section

```bash
→ python manage.py fetch_realtime_data
→ Wait 2 seconds for API response
```

---

## 📞 API Key

Already configured in `api/realtime_service.py`:

```python
FMP_API_KEY = "aISf2J1Xw24TvjWypqPbbR4dsDdqN1VZ"
```

Free tier includes:

- ✓ 250 API calls/month
- ✓ All financial statements
- ✓ Financial ratios

For more info: https://financialmodelingprep.com

---

## 🎉 You're All Set!

Your Nifty 100 app now has real-time stock data. Start comparing companies with live metrics!

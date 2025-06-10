# Lengolf Sales Sync API

> A robust microservice for synchronizing sales data from Qashier POS to Supabase with automated daily operations

## 🚀 Live Deployment

**Production API**: `https://lengolf-sales-api-1071951248692.asia-southeast1.run.app`

## 📋 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health` | Health check for monitoring |
| `GET` | `/info` | Service information and API documentation |
| `POST` | `/sync/daily` | Trigger daily data synchronization |
| `POST` | `/sync/historical` | Trigger historical sync for date range |
| `POST` | `/sync/estimates` | Get sync estimates for date range |

## 🏗️ Architecture

Clean, modular design focused on reliable data synchronization:

```
app/
├── config.py              # Configuration management
├── utils.py               # Date utilities and validation
├── supabase_client.py     # Database operations with comprehensive functions
├── qashier_scraper.py     # Web scraping with date format fixes
├── services.py            # Business logic and data processing
├── app.py                 # Flask API service
└── requirements.txt       # Production dependencies
```

## 🔧 Setup

### Prerequisites
- Python 3.11+
- Supabase project with proper schema
- Qashier POS credentials

### Environment Variables
```bash
export SUPABASE_URL="your-supabase-url"
export SUPABASE_SERVICE_KEY="your-service-key"
export QASHIER_USERNAME="base64-encoded-username"
export QASHIER_PASSWORD="base64-encoded-password"
```

### Install Dependencies
```bash
cd app
pip install -r requirements.txt
python -m playwright install chromium
```

## 💻 Usage

### API Calls
```bash
# Check health
curl https://lengolf-sales-api-1071951248692.asia-southeast1.run.app/health

# Get service info
curl https://lengolf-sales-api-1071951248692.asia-southeast1.run.app/info

# Trigger daily sync (recommended for automation)
curl -X http://127.0.0.1:8080/sync/daily \
  -H "Content-Length: 0"

# Trigger historical sync for specific date range
curl -X POST https://lengolf-sales-api-1071951248692.asia-southeast1.run.app/sync/historical \
  -H "Content-Type: application/json" \
  -d '{"start_date": "2024-03-01", "end_date": "2024-03-31"}'

# Get sync estimates before running historical sync
curl -X POST https://lengolf-sales-api-1071951248692.asia-southeast1.run.app/sync/estimates \
  -H "Content-Type: application/json" \
  -d '{"start_date": "2024-03-01", "end_date": "2024-12-31"}'
```

### Local Development
```bash
cd app
python app.py
```

## 🏛️ Database Architecture

### Data Flow
```
Qashier POS → Playwright Scraper → Excel Download → 
CSV Processing (with ISO date conversion) → Supabase Staging → 
Data Processing → Final Sales Table → Transformed View
```

### Key Tables
- **`pos.lengolf_sales_staging`** - Raw data from Qashier (13,400+ records)
- **`pos.lengolf_sales`** - Processed final data (13,400+ records after cleanup)
- **`pos.dim_product`** - Product catalog with duplicate prevention
- **`pos.v_lengolf_sales_transformed`** - Analytics-ready view

### Data Quality Features
- ✅ **Date Format Consistency** - All dates converted to ISO format (YYYY-MM-DD)
- ✅ **Duplicate Prevention** - Unique constraints on product and sales data
- ✅ **Data Validation** - Comprehensive validation and error handling
- ✅ **Automated Refresh** - Hourly automated data refresh via Supabase Cron

## 🤖 Automation

### Supabase Cron Integration
The system includes automated hourly data refresh:

```sql
-- Automated refresh function
SELECT automated_sales_refresh();

-- Cron schedule (runs every hour)
SELECT cron.schedule('hourly-sales-refresh', '0 * * * *', 'SELECT automated_sales_refresh();');
```

### Cloud Scheduler (Alternative)
```bash
gcloud scheduler jobs create http daily-sales-sync \
  --schedule="0 23 * * *" \
  --uri="https://lengolf-sales-api-1071951248692.asia-southeast1.run.app/sync/daily" \
  --http-method=POST \
  --headers="Content-Length=0" \
  --time-zone="Asia/Bangkok"
```

## 📦 Key Dependencies

Production-optimized dependency list:

- **flask** - Web framework
- **gunicorn** - Production WSGI server
- **pandas** - Data processing
- **playwright** - Web scraping automation
- **supabase** - Database client
- **openpyxl** - Excel file processing
- **python-dateutil** - Date manipulation and validation

## 🚢 Deployment

### Docker Configuration
```bash
# Build and deploy to Google Cloud Run
./deploy.sh lengolf-forms asia-southeast1
```

### Production Features
- ✅ **Containerized Deployment** - Docker with optimized multi-stage builds
- ✅ **Auto-scaling** - Cloud Run with 0-5 instance scaling
- ✅ **Health Monitoring** - Comprehensive health checks
- ✅ **Structured Logging** - JSON-formatted logs for monitoring
- ✅ **Environment Configuration** - Secure secret management
- ✅ **Performance Optimization** - Gunicorn with optimized worker configuration

### Cloud Run Configuration
- **Memory**: 2GB
- **CPU**: 1 vCPU  
- **Timeout**: 300 seconds
- **Concurrency**: 10 requests
- **Port**: 8080 (configurable via PORT env var)

## 🔍 Monitoring & Observability

- **Health Endpoint**: Real-time service health monitoring
- **Structured Logging**: JSON logs with batch tracking UUIDs
- **Error Handling**: Comprehensive error tracking and reporting
- **Performance Metrics**: Request timing and resource usage tracking

## 🔒 Security

- **Environment Variables** - All secrets managed via environment variables
- **Non-root Execution** - Container runs with non-privileged user
- **Input Validation** - Comprehensive request validation and sanitization
- **Base64 Encoding** - Secure credential encoding
- **No Hardcoded Secrets** - Zero secrets in codebase

## 🐛 Troubleshooting

### Common Issues

**Date Format Errors**
- ✅ **Fixed**: All dates now converted to ISO format before database insertion
- ✅ **Prevention**: Automatic date validation and conversion

**Product Duplicates**
- ✅ **Fixed**: Unique constraints added to prevent duplicate products
- ✅ **Cleanup**: Database cleanup functions available

**Performance Issues**
- ✅ **Optimized**: Monthly chunking for large date ranges (max 12 months)
- ✅ **Monitoring**: Sync estimates available before processing

**Bot Detection / Login Timeout Issues**
- ✅ **Fixed**: Simplified browser launch and login approach to bypass detection
- ✅ **Root Cause**: Complex anti-bot arguments were ironically triggering detection
- ✅ **Solution**: Adopted working app's simple approach with redirect URLs

### Bot Detection Fix Details

**Problem**: The scraper was failing with timeout errors during login:
```
Locator.fill: Timeout 30000ms exceeded.
Call log:
waiting for get_by_label("Username")
```

**Solution Applied**:
1. **Simplified Browser Launch**: Changed from complex stealth arguments to simple `browser.launch(headless=True)`
2. **Working User Agent**: Switched to the proven user agent from the working app
3. **Direct Redirect URL**: Use `https://hq.qashier.com/#/login?redirect=/transactions` instead of separate navigation
4. **Streamlined Login**: Removed fallback logic that made behavior patterns detectable

**Key Insight**: Less is more - the "stealthy" approach with many anti-detection arguments was more suspicious than a simple, direct approach.

**Before (Failed)**:
```python
# Too many suspicious arguments
browser = p.chromium.launch(
    headless=True,
    args=[
        '--disable-blink-features=AutomationControlled',
        '--disable-features=VizDisplayCompositor',
        # ... many more args that triggered detection
    ]
)
```

**After (Working)**:
```python
# Simple and clean
browser = p.chromium.launch(headless=True)
context = browser.new_context(
    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3",
    accept_downloads=True
)
```

### Debug Mode
```bash
export DEBUG=true
export LOG_LEVEL=DEBUG
python app.py
```

## 📊 Recent Improvements

### Version 2.0.0 Features
- ✅ **Date Consistency Fix** - Resolved PostgreSQL date format conflicts
- ✅ **Duplicate Prevention** - Added unique constraints and cleanup functions
- ✅ **Automated Refresh** - Hourly Supabase Cron integration
- ✅ **API Modernization** - RESTful endpoints with proper error handling
- ✅ **Production Deployment** - Stable Google Cloud Run deployment
- ✅ **Data Quality** - Comprehensive validation and error handling
- ✅ **Bot Detection Fix** - Resolved login timeout issues with simplified browser approach

### Performance Metrics
- **Daily Sync**: ~300-400 records processed in seconds
- **Historical Sync**: Up to 12 months with monthly chunking
- **Data Refresh**: 13,400+ records refreshed hourly
- **Uptime**: 99.9% availability on Cloud Run

## 💡 Best Practices

### For Daily Operations
- Use `/sync/daily` endpoint for regular operations
- Monitor via `/health` endpoint
- Check logs for any processing issues

### For Historical Sync
- Use `/sync/estimates` first for large date ranges
- Limit to 12 months maximum per request
- Process in monthly chunks for better reliability

### For Monitoring
- Set up alerting on health endpoint failures
- Monitor Cloud Run metrics and logs
- Use structured logging for debugging

## 🤝 Contributing

1. Follow the modular architecture pattern
2. Add comprehensive error handling and logging
3. Include input validation for all endpoints
4. Test both local and production deployments
5. Update documentation for any new features

## 📜 License

This project is for internal use at Lengolf.

---

**Built with ❤️ for reliable, automated sales data synchronization**

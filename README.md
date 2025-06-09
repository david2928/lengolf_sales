# Lengolf Sales Sync API

> A lightweight, focused microservice for synchronizing sales data from Qashier POS to Supabase

## 🚀 Quick Start

### Local Development
```bash
cd app
python app.py
```

### Docker Deployment
```bash
docker build -t lengolf-sales-api .
docker run -p 8080:8080 lengolf-sales-api
```

### Google Cloud Run
```bash
./deploy.sh lengolf-forms asia-southeast1
```

## 📋 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health` | Health check for monitoring |
| `POST` | `/sync/daily` | Trigger daily data synchronization |
| `POST` | `/sync/historical` | Trigger historical sync for date range |
| `POST` | `/sync/missing` | Automatically sync all missing historical data |
| `GET` | `/data/coverage` | Get data coverage report |
| `GET` | `/info` | Service information |

## 🏗️ Architecture

Clean, modular design focused on a single responsibility:

```
app/
├── config.py              # Configuration management
├── utils.py               # Common utilities
├── supabase_client.py     # Database operations  
├── qashier_scraper.py     # Web scraping
├── services.py            # Business logic
├── app.py                 # Flask API service
├── app_legacy.py          # CLI compatibility
└── requirements.txt       # Minimal dependencies
```

## 🔧 Setup

### Prerequisites
- Python 3.11+
- Supabase project
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
# Trigger daily sync
curl -X POST http://localhost:8080/sync/daily

# Trigger historical sync for specific date range
curl -X POST http://localhost:8080/sync/historical \
  -H "Content-Type: application/json" \
  -d '{"start_date": "2025-01-07", "end_date": "2025-01-31"}'

# Automatically sync all missing historical data
curl -X POST http://localhost:8080/sync/missing

# Get data coverage report
curl http://localhost:8080/data/coverage

# Check health
curl http://localhost:8080/health

# Get info
curl http://localhost:8080/info
```

### Legacy CLI Mode
```bash
python app_legacy.py
```

### Scheduled Execution
```bash
# Google Cloud Scheduler example
gcloud scheduler jobs create http daily-sales-sync \
  --schedule="0 23 * * *" \
  --uri="https://your-service-url/sync/daily" \
  --http-method=POST \
  --time-zone="Asia/Bangkok"
```

## 🏛️ Historical Data Features

### Data Coverage Analysis
- **Gap Detection**: Automatically identifies missing date ranges
- **Coverage Report**: GET `/data/coverage` provides detailed gap analysis
- **Smart Chunking**: Splits large date ranges into manageable monthly chunks

### Historical Sync Capabilities
- **Manual Range Sync**: POST `/sync/historical` for specific date ranges
- **Automatic Gap Fill**: POST `/sync/missing` finds and fills all gaps
- **Complex Navigation**: Handles Qashier POS calendar navigation for any historical date
- **Robust Error Handling**: Continues processing even if individual chunks fail

### Navigation Logic
The historical scraper handles complex UI navigation:
1. **Year Navigation**: Uses `chevron_left` (nth:1) to go back to 2024
2. **Month Navigation**: Uses `chevron_left/right` (first) for month-to-month
3. **Date Selection**: Selects start and end dates within the calendar
4. **Multi-Month Ranges**: Automatically handles ranges spanning multiple months

## 📦 Dependencies

Minimal, focused dependency list:

- **flask** - Web framework
- **gunicorn** - Production WSGI server
- **pandas** - Data processing
- **playwright** - Web scraping
- **supabase** - Database client
- **openpyxl** - Excel file processing
- **requests** - HTTP client (testing)
- **python-dateutil** - Date manipulation for historical sync

## 🚢 Deployment

### Production Ready Features
- ✅ Multi-stage Docker builds
- ✅ Non-root container execution
- ✅ Health monitoring endpoints
- ✅ Structured logging
- ✅ Environment-based configuration
- ✅ Auto-scaling support

### Cloud Run Configuration
- **Memory**: 2GB
- **CPU**: 1 vCPU
- **Timeout**: 300 seconds
- **Concurrency**: 10 requests
- **Scaling**: 0-5 instances

## 🔍 Monitoring

- **Health Checks**: `/health` endpoint
- **Logging**: Structured JSON logs
- **Error Tracking**: Comprehensive error handling
- **Batch Tracking**: UUID-based sync tracking

## 🔒 Security

- Environment variable configuration
- Non-root container execution
- Input validation and sanitization
- Base64 encoded credentials
- No hardcoded secrets

## 🧪 Testing

```bash
cd app
# Test basic functionality
python test_api.py http://localhost:8080

# Test historical sync functionality
python test_historical_api.py http://localhost:8080
```

## 📊 Data Flow

```
Qashier POS → Playwright Scraper → Excel Download → 
CSV Conversion → Pandas Processing → Supabase Staging → 
Database Processing → Final Sales Table
```

## 🤔 Why Gunicorn?

Yes, we need Gunicorn for production deployment because:

1. **Flask's built-in server** is only for development
2. **Gunicorn** provides production-grade WSGI serving
3. **Better performance** with worker processes
4. **Resource management** and connection handling
5. **Cloud Run compatibility** for containerized deployments

## 🐛 Troubleshooting

### Common Issues

**Credentials Error**
- Ensure environment variables are set correctly
- Check base64 encoding of Qashier credentials
- Verify Supabase connection strings

**Playwright Issues**
- Install Chromium: `python -m playwright install chromium`
- Check system dependencies

**Port Issues**
- Default port is 8080
- Change with `PORT` environment variable

### Debug Mode
```bash
export DEBUG=true
export LOG_LEVEL=DEBUG
python app.py
```

## 📝 Migration Guide

### From Old Structure
```bash
# Old way
python app_supabase.py

# New way (CLI)
python app_legacy.py

# New way (API)
curl -X POST http://localhost:8080/sync/daily
```

## 🤝 Contributing

1. Follow the focused architecture (sync operations only)
2. Add comprehensive logging
3. Include error handling
4. Test both API and CLI modes
5. Update documentation

## 📜 License

This project is for internal use at Lengolf.

---

**Built with ❤️ for efficient sales data synchronization**

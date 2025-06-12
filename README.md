# Lengolf Sales Data Integration System

> **Enterprise-grade microservice for automated POS data synchronization from Qashier to Supabase with comprehensive sales analytics**

## 🎯 Overview

The Lengolf Sales Data Integration System is a robust, production-ready solution that automatically extracts, transforms, and loads (ETL) sales data from the Qashier Point-of-Sale system into a Supabase PostgreSQL database. The system provides real-time daily synchronization and historical data backfill capabilities with comprehensive error handling, monitoring, and data validation.

## 🏗️ System Architecture

### Core Components

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Qashier POS   │───▶│  Flask API       │───▶│   Supabase      │
│   (Source)      │    │  Microservice    │    │   Database      │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                              │
                              ▼
                       ┌──────────────────┐
                       │   Playwright     │
                       │   Web Scraper    │
                       └──────────────────┘
```

### Data Flow Pipeline

```
Qashier POS → Playwright Automation → Excel Download → 
CSV Processing → Data Validation → Staging Table → 
Business Logic Processing → Final Sales Table → Analytics Views
```

## 📊 Database Schema

### Core Tables Overview

| Table | Purpose | Records | Schema |
|-------|---------|---------|--------|
| `pos.lengolf_sales_staging` | Raw CSV data ingestion | ~13K+ | `pos` |
| `pos.lengolf_sales` | Processed sales transactions | ~62K+ | `pos` |
| `pos.dim_product` | Product catalog dimension | ~183 | `pos` |
| `pos.sales_sync_logs` | ETL process monitoring | ~194 | `pos` |

### Staging Table Schema

The staging table captures **ALL** CSV columns from Qashier Transaction Details:

```sql
-- Core transaction identifiers
date                    TEXT,    -- Transaction date/time
receipt_number          TEXT,    -- Receipt identifier  
order_number           TEXT,    -- Order identifier
invoice_no             TEXT,    -- Invoice number

-- Payment information
invoice_payment_type            TEXT,    -- Payment method at invoice level
total_invoice_amount           TEXT,    -- Total invoice amount
transaction_total_amount       TEXT,    -- Transaction total
transaction_level_percentage_discount TEXT, -- % discount
transaction_level_dollar_discount     TEXT, -- $ discount  
transaction_total_vat          TEXT,    -- VAT amount
transaction_payment_method     TEXT,    -- Payment method
payment_note                   TEXT,    -- Payment notes
transaction_note               TEXT,    -- Transaction notes

-- Order and staff details
order_type                     TEXT,    -- Order type (dine-in, takeaway, etc.)
staff_name                     TEXT,    -- Staff member name

-- Customer information  
customer_name                  TEXT,    -- Customer name
customer_phone_number          TEXT,    -- Customer phone

-- Transaction status
voided                         TEXT,    -- Void status
void_reason                    TEXT,    -- Void reason

-- Product information
combo_name                     TEXT,    -- Combo name if applicable
transaction_item               TEXT,    -- Product/service name
sku_number                     TEXT,    -- SKU identifier
transaction_item_quantity      TEXT,    -- Quantity
transaction_item_notes         TEXT,    -- Item notes
transaction_item_discount      TEXT,    -- Item discount

-- Pricing information
amount_before_subsidy          TEXT,    -- Amount before subsidy
total_subsidy                  TEXT,    -- Subsidy amount
transaction_item_final_amount  TEXT,    -- Final amount

-- Store information  
store_name                     TEXT,    -- Store name

-- System fields
update_time                    TEXT,    -- Update timestamp
import_batch_id                TEXT     -- Batch tracking ID
```

### Final Sales Table Schema

Processed and normalized transaction data:

```sql
CREATE TABLE pos.lengolf_sales (
    id                      SERIAL PRIMARY KEY,
    date                    DATE NOT NULL,
    receipt_number          TEXT NOT NULL,
    payment_method          TEXT,
    payment_details         TEXT,
    customer_name           TEXT,
    customer_phone_number   TEXT,
    product_name            TEXT,
    tab                     TEXT,
    category                TEXT,
    parent_category         TEXT,
    quantity                INTEGER,
    unit_price              NUMERIC,
    total_price             NUMERIC,
    is_sim_usage            BOOLEAN DEFAULT FALSE,
    gross_amount            NUMERIC,
    discount_amount         NUMERIC,
    net_sales_amount        NUMERIC,
    tax_amount              NUMERIC,
    total_amount            NUMERIC,
    gross_profit            NUMERIC,
    sales_timestamp         TIMESTAMPTZ NOT NULL,
    created_at              TIMESTAMPTZ DEFAULT NOW(),
    updated_at              TIMESTAMPTZ DEFAULT NOW(),
    update_time             TIMESTAMPTZ DEFAULT NOW()
);
```

### Product Dimension Table

```sql
CREATE TABLE pos.dim_product (
    id              SERIAL PRIMARY KEY,
    product_name    TEXT NOT NULL UNIQUE,
    tab             TEXT,
    category        TEXT,
    parent_category TEXT,
    barcode         TEXT,
    sku_number      TEXT,
    unit_price      NUMERIC,
    unit_cost       NUMERIC,
    is_sim_usage    BOOLEAN DEFAULT FALSE,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);
```

## 🔄 Data Processing Workflow

### 1. Data Extraction
- **Source**: Qashier POS Transaction Details
- **Method**: Playwright web automation
- **Format**: Excel (.xlsx) → CSV conversion
- **Authentication**: Base64 encoded credentials

### 2. Data Transformation
- **Date Standardization**: DD/MM/YYYY HH:MM:SS → YYYY-MM-DD HH:MM:SS
- **Field Mapping**: 30+ CSV columns mapped to staging table
- **Data Validation**: Type checking, null handling, format validation
- **Duplicate Detection**: Receipt-based deduplication

### 3. Data Loading
- **Staging**: Raw CSV data loaded into `lengolf_sales_staging`
- **Processing**: Database function `process_staging_batch_v2()` transforms data
- **Final Storage**: Processed data in `lengolf_sales` table
- **Product Catalog**: Automatic product dimension updates

### 4. Data Quality Assurance
- **Truncate & Replace**: Prevents duplicates by date range replacement
- **Batch Tracking**: UUID-based batch identification
- **Error Logging**: Comprehensive error capture and reporting
- **Data Validation**: Multi-level validation checks

## 🚀 API Endpoints

### Core Endpoints

| Method | Endpoint | Description | Use Case |
|--------|----------|-------------|----------|
| `GET` | `/health` | Health monitoring | System status checks |
| `GET` | `/info` | Service information | API documentation |
| `POST` | `/sync/daily` | Daily synchronization | Automated daily runs |
| `POST` | `/sync/historical` | Historical data sync | Backfill missing data |
| `POST` | `/sync/estimates` | Sync estimation | Planning historical syncs |

### Daily Sync Endpoint

```bash
curl -X POST https://lengolf-sales-api-1071951248692.asia-southeast1.run.app/sync/daily \
  -H "Content-Length: 0"
```

**Response:**
```json
{
  "success": true,
  "message": "Successfully processed 487 records",
  "batch_id": "uuid-string",
  "records_scraped": 487,
  "records_inserted": 487,
  "records_processed": 487
}
```

### Historical Sync Endpoint

```bash
curl -X POST https://lengolf-sales-api-1071951248692.asia-southeast1.run.app/sync/historical \
  -H "Content-Type: application/json" \
  -d '{
    "start_date": "2024-03-01",
    "end_date": "2024-03-31"
  }'
```

**Features:**
- Automatic monthly chunking for large date ranges
- Progress tracking per chunk
- Error handling with partial success
- Comprehensive logging and monitoring

## ⚙️ Configuration & Setup

### Environment Variables

```bash
# Supabase Configuration
SUPABASE_URL="https://your-project.supabase.co"
SUPABASE_SERVICE_KEY="your-service-role-key"

# Qashier POS Credentials (Base64 encoded)
QASHIER_USERNAME="base64-encoded-username"
QASHIER_PASSWORD="base64-encoded-password"

# Application Configuration
PORT=8080
HOST=0.0.0.0
DEBUG=false
LOG_LEVEL=INFO
PYTHONPATH=/app
```

### Local Development Setup

```bash
# 1. Clone repository
git clone https://github.com/your-org/lengolf-sales.git
cd lengolf-sales

# 2. Install dependencies
cd app
pip install -r requirements.txt
python -m playwright install chromium

# 3. Configure environment variables
cp .env.example .env
# Edit .env with your credentials

# 4. Run locally
python app.py
```

### Production Deployment

```bash
# Deploy to Google Cloud Run
./deploy.sh your-project-id asia-southeast1
```

**Cloud Run Configuration:**
- **Memory**: 2GB
- **CPU**: 1 vCPU
- **Timeout**: 600 seconds (10 minutes)
- **Concurrency**: 10 requests
- **Auto-scaling**: 0-5 instances
- **Region**: Asia Southeast 1 (Singapore)

## 📅 Scheduling & Automation

### Option 1: Supabase Cron (Recommended)

```sql
-- Create automated daily sync function
CREATE OR REPLACE FUNCTION automated_daily_sync()
RETURNS void AS $$
BEGIN
    -- Call API endpoint using http extension
    PERFORM net.http_post(
        url := 'https://lengolf-sales-api-1071951248692.asia-southeast1.run.app/sync/daily',
        headers := '{"Content-Type": "application/json"}'::jsonb,
        body := '{}'::jsonb
    );
END;
$$ LANGUAGE plpgsql;

-- Schedule daily at 11:30 PM Bangkok time
SELECT cron.schedule(
    'daily-sales-sync',
    '30 16 * * *',  -- 11:30 PM Bangkok = 4:30 PM UTC
    'SELECT automated_daily_sync();'
);
```

### Option 2: Google Cloud Scheduler

```bash
gcloud scheduler jobs create http daily-sales-sync \
  --schedule="30 16 * * *" \
  --uri="https://lengolf-sales-api-1071951248692.asia-southeast1.run.app/sync/daily" \
  --http-method=POST \
  --headers="Content-Length=0" \
  --time-zone="Asia/Bangkok" \
  --description="Daily Lengolf sales data synchronization"
```

### Option 3: GitHub Actions

```yaml
name: Daily Sales Sync
on:
  schedule:
    - cron: '30 16 * * *'  # 11:30 PM Bangkok time
  workflow_dispatch:

jobs:
  sync:
    runs-on: ubuntu-latest
    steps:
      - name: Trigger daily sync
        run: |
          curl -X POST \
            -H "Content-Length: 0" \
            ${{ secrets.API_ENDPOINT }}/sync/daily
```

## 📈 Monitoring & Analytics

### Sync Logs Monitoring

```sql
-- View recent sync operations
SELECT 
    batch_id,
    process_type,
    status,
    records_processed,
    start_time,
    end_time,
    EXTRACT(EPOCH FROM (end_time - start_time)) as duration_seconds,
    error_message
FROM pos.sales_sync_logs 
ORDER BY start_time DESC 
LIMIT 10;
```

### Data Coverage Analysis

```sql
-- Check data coverage by month
SELECT 
    DATE_TRUNC('month', date) as month,
    COUNT(*) as total_transactions,
    SUM(total_amount) as total_revenue,
    COUNT(DISTINCT receipt_number) as unique_receipts,
    COUNT(DISTINCT customer_name) as unique_customers
FROM pos.lengolf_sales 
GROUP BY DATE_TRUNC('month', date)
ORDER BY month DESC;
```

### Performance Metrics

```sql
-- Sync performance metrics
SELECT 
    process_type,
    AVG(records_processed) as avg_records,
    AVG(EXTRACT(EPOCH FROM (end_time - start_time))) as avg_duration_seconds,
    COUNT(*) as total_syncs,
    SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as successful_syncs
FROM pos.sales_sync_logs 
WHERE start_time >= NOW() - INTERVAL '30 days'
GROUP BY process_type;
```

## 🛠️ Advanced Features

### Historical Data Backfill

The system supports comprehensive historical data synchronization:

```bash
# Estimate sync requirements
curl -X POST https://your-api/sync/estimates \
  -H "Content-Type: application/json" \
  -d '{"start_date": "2024-03-01", "end_date": "2025-01-31"}'

# Response includes:
# - Total days to sync
# - Monthly chunks created  
# - Estimated processing time
# - Validation warnings
```

### Data Validation & Quality

- **Date Range Validation**: Automatic validation against valid ranges
- **Monthly Chunking**: Large ranges split automatically (max 12 months)
- **Duplicate Prevention**: Receipt-based duplicate detection
- **Error Recovery**: Partial success handling for historical syncs
- **Data Integrity**: Comprehensive validation at multiple stages

### Extensibility

- **Modular Design**: Clean separation of concerns
- **Configuration Driven**: Environment-based configuration
- **Error Handling**: Comprehensive error capture and reporting
- **Logging**: Structured logging with batch tracking
- **Monitoring**: Built-in health checks and metrics

## 🔧 Troubleshooting

### Common Issues

**1. Authentication Errors**
```bash
# Verify base64 encoded credentials
echo "aW5mb0BsZW4uZ29sZg==" | base64 -d  # Should output username
```

**2. Date Format Issues**
```sql
-- Check for invalid dates in staging
SELECT date, COUNT(*) 
FROM pos.lengolf_sales_staging 
WHERE date !~ '^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$'
GROUP BY date;
```

**3. Missing Data**
```sql
-- Find missing date ranges
WITH date_series AS (
  SELECT generate_series('2024-03-01'::date, CURRENT_DATE, '1 day'::interval)::date AS expected_date
),
existing_dates AS (
  SELECT DISTINCT date FROM pos.lengolf_sales
)
SELECT ds.expected_date as missing_date
FROM date_series ds
LEFT JOIN existing_dates ed ON ds.expected_date = ed.date
WHERE ed.date IS NULL
ORDER BY missing_date;
```

### Performance Optimization

**Database Indexes:**
```sql
-- Recommended indexes for performance
CREATE INDEX idx_lengolf_sales_date ON pos.lengolf_sales(date);
CREATE INDEX idx_lengolf_sales_receipt ON pos.lengolf_sales(receipt_number);
CREATE INDEX idx_lengolf_sales_customer ON pos.lengolf_sales(customer_name);
CREATE INDEX idx_sync_logs_batch_id ON pos.sales_sync_logs(batch_id);
```

## 📄 License

This project is proprietary software developed for Lengolf operations.

## 🤝 Support

For technical support or feature requests, contact the development team or submit an issue through the project repository.

---

**Production URL**: https://lengolf-sales-api-1071951248692.asia-southeast1.run.app

**Last Updated**: June 2025  
**Version**: 2.0.0

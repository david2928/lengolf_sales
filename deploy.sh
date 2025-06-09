#!/bin/bash

# Lengolf Sales API - Google Cloud Run Deployment Script
# Usage: ./deploy.sh [PROJECT_ID] [REGION]

set -e

# Configuration
PROJECT_ID=${1:-"your-project-id"}
REGION=${2:-"asia-southeast1"}
SERVICE_NAME="lengolf-sales-api"
IMAGE_NAME="gcr.io/$PROJECT_ID/$SERVICE_NAME"

echo "🚀 Deploying Lengolf Sales API to Google Cloud Run"
echo "================================================="
echo "Project ID: $PROJECT_ID"
echo "Region: $REGION"
echo "Service: $SERVICE_NAME"
echo "Image: $IMAGE_NAME"
echo ""

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo "❌ gcloud CLI is not installed. Please install it first."
    exit 1
fi

# Check if logged in to gcloud
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | head -n 1 > /dev/null; then
    echo "❌ Not logged in to gcloud. Please run 'gcloud auth login' first."
    exit 1
fi

# Set the project
echo "📋 Setting project..."
gcloud config set project $PROJECT_ID

# Enable required APIs
echo "🔧 Enabling required APIs..."
gcloud services enable cloudbuild.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable containerregistry.googleapis.com

# Build and push the container image
echo "🏗️  Building container image..."
gcloud builds submit --tag $IMAGE_NAME --timeout=1200s

# Deploy to Cloud Run
echo "🚀 Deploying to Cloud Run..."
gcloud run deploy $SERVICE_NAME \
  --image $IMAGE_NAME \
  --region $REGION \
  --platform managed \
  --allow-unauthenticated \
  --port 8080 \
  --memory 2Gi \
  --cpu 1 \
  --timeout 600 \
  --concurrency 10 \
  --min-instances 0 \
  --max-instances 5 \
  --set-env-vars "PYTHONPATH=/app" \
  --set-env-vars "QASHIER_USERNAME=aW5mb0BsZW4uZ29sZg==" \
  --set-env-vars "QASHIER_PASSWORD=bGVuZ29sZjEyMw==" \
  --set-env-vars "SUPABASE_URL=https://bisimqmtxjsptehhqpeg.supabase.co" \
  --set-env-vars "SUPABASE_SERVICE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImJpc2ltcW10eGpzcHRlaGhxcGVnIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTczODM5NjkzMSwiZXhwIjoyMDUzOTcyOTMxfQ.2-7HeKrbHj--JPudQjEYJNeBTVnzRY6jxTpN7CHTQqk"

# Get the service URL
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME --region=$REGION --format='value(status.url)')

echo ""
echo "✅ Deployment completed successfully!"
echo "================================================="
echo "Service URL: $SERVICE_URL"
echo ""
echo "🧪 Test the deployment:"
echo "curl $SERVICE_URL/health"
echo "curl $SERVICE_URL/info"
echo ""
echo "📊 Monitor logs:"
echo "gcloud logging read \"resource.type=cloud_run_revision AND resource.labels.service_name=$SERVICE_NAME\" --limit 50 --format json"
echo ""
echo "🔧 Update environment variables:"
echo "gcloud run services update $SERVICE_NAME --region=$REGION --set-env-vars=\"KEY=VALUE\""
echo ""

# Optional: Run a quick health check
if command -v curl &> /dev/null; then
    echo "🏥 Running health check..."
    if curl -s "$SERVICE_URL/health" > /dev/null; then
        echo "✅ Health check passed!"
    else
        echo "⚠️  Health check failed - service may still be starting up"
    fi
fi

echo "🎉 Deployment script completed!" 
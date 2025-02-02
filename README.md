# Lengolf Sales Data Automation

Automated data extraction from Qashier POS to Google Sheets.

## Setup

1. Create a Google Cloud project (if not exists)
```bash
gcloud projects create noted-app-295904 --name="Lengolf Sales"
```

2. Enable required APIs
```bash
gcloud services enable \
    cloudbuild.googleapis.com \
    run.googleapis.com \
    artifactregistry.googleapis.com \
    iam.googleapis.com \
    iamcredentials.googleapis.com
```

3. Create Artifact Registry repository
```bash
gcloud artifacts repositories create lengolf-sales \
    --repository-format=docker \
    --location=asia-southeast1
```

4. Set up Workload Identity Federation
```bash
# Create a workload identity pool
gcloud iam workload-identity-pools create "github-pool" \
    --location="global" \
    --display-name="GitHub Actions Pool"

# Create a workload identity provider
gcloud iam workload-identity-pools providers create-oidc "github-provider" \
    --location="global" \
    --workload-identity-pool="github-pool" \
    --display-name="GitHub provider" \
    --attribute-mapping="google.subject=assertion.sub,attribute.actor=assertion.actor,attribute.repository=assertion.repository" \
    --issuer-uri="https://token.actions.githubusercontent.com"

# Get the workload identity provider resource name
gcloud iam workload-identity-pools providers describe "github-provider" \
    --location="global" \
    --workload-identity-pool="github-pool" \
    --format="value(name)"
```

5. Set up GitHub Secrets
Go to your GitHub repository settings > Secrets and variables > Actions and add:
- `WIF_PROVIDER`: The Workload Identity Provider resource name
- `WIF_SERVICE_ACCOUNT`: The service account email
- `APP_LOGIN`: Base64 encoded Qashier login
- `APP_PASSWORD`: Base64 encoded Qashier password
- `GOOGLE_KEY`: Base64 encoded Google service account JSON

## Deployment

The application will automatically deploy when you push to the main branch. You can also manually trigger the deployment from the GitHub Actions tab.

To deploy manually via command line:
```bash
gcloud builds submit --region=asia-southeast1 \
    --substitutions=_APP_LOGIN='<base64_login>',_APP_PASSWORD='<base64_password>',_GOOGLE_KEY='<base64_key>'
```

## Development

1. Install dependencies:
```bash
pip install -r app/requirenments.txt
playwright install
```

2. Run locally:
```bash
python -m app.app_temp
```

## Environment Variables

- `APP_LOGIN`: Base64 encoded Qashier login
- `APP_PASSWORD`: Base64 encoded Qashier password
- `GOOGLE_KEY`: Base64 encoded Google service account JSON
- `DEBUG`: Enable debug mode (optional)
- `HEADLESS`: Run browser in headless mode (default: True)

## Security Notes

- All sensitive data is stored in GitHub Secrets
- Workload Identity Federation is used instead of service account keys
- Environment variables are passed securely through build arguments
- The container runs with minimal permissions

# Description

This is example how we can grab data from UI via Playwright and uploas into Google Sheets

# Params

```
LOGIN           - Login to CMS - base64 encoded
PASSWORD        - Password to CMS - base64 encoded
GOOGLE_KEY      - Google service account JSON file encode - base64 encoded
```

# Prerequisites

Create service account in Cloud Console
Create key for this service account
Download key in JSON and encode via "base64"

# Building 

To build an image better to use Google Build to put it into "Artifactory Registory":
```
    gcloud builds submit --region=us-west2 --tag us-east1-docker.pkg.dev/PROJECT/test-scraper/cloud:latest
```

can be also other region

# Running

Just add an image with setting params in setting 

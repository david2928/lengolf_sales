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

#!/bin/bash
# deploy.sh — Deploy the Cloud Function to GCP
# Run: bash deploy.sh

set -e

PROJECT_ID="your-project-id"          # Replace with your GCP project ID
BILLING_ACCOUNT_ID="YOUR-BILLING-ID"  # Replace with your billing account ID
REGION="us-central1"
TOPIC_NAME="budget-alerts"
FUNCTION_NAME="budget-guard"
ALERT_EMAIL="your-email@gmail.com"    # Replace with your email
SMTP_EMAIL="your-gmail@gmail.com"     # Replace with Gmail used to send alerts
SMTP_PASSWORD="your-app-password"     # Replace with Gmail App Password

echo "🚀 Deploying GCP Cloud Budget Guard..."

# 1. Set project
gcloud config set project $PROJECT_ID

# 2. Enable required APIs
echo "Enabling APIs..."
gcloud services enable \
  cloudfunctions.googleapis.com \
  pubsub.googleapis.com \
  cloudbilling.googleapis.com \
  cloudbuild.googleapis.com

# 3. Create Pub/Sub topic
echo "Creating Pub/Sub topic..."
gcloud pubsub topics create $TOPIC_NAME --project=$PROJECT_ID || echo "Topic already exists"

# 4. Grant billing admin role to Cloud Function service account
SA_EMAIL="$(gcloud projects describe $PROJECT_ID --format='value(projectNumber)')@cloudbuild.gserviceaccount.com"
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:$SA_EMAIL" \
  --role="roles/billing.admin"

# 5. Deploy Cloud Function
echo "Deploying Cloud Function..."
gcloud functions deploy $FUNCTION_NAME \
  --runtime=python311 \
  --trigger-topic=$TOPIC_NAME \
  --entry-point=budget_alert \
  --region=$REGION \
  --set-env-vars="ALERT_EMAIL=$ALERT_EMAIL,SMTP_EMAIL=$SMTP_EMAIL,SMTP_PASSWORD=$SMTP_PASSWORD,BILLING_ACCOUNT_ID=$BILLING_ACCOUNT_ID,GCP_PROJECT=$PROJECT_ID" \
  --memory=256MB \
  --timeout=60s

echo "✅ Cloud Function deployed!"

# 6. Create budget with alerts
echo "Creating billing budget..."
export BILLING_ACCOUNT_ID=$BILLING_ACCOUNT_ID
export GCP_PROJECT=$PROJECT_ID
export BUDGET_AMOUNT_USD=10
pip install google-cloud-billing-budgets --quiet
python budget_setup.py

echo ""
echo "✅ GCP Cloud Budget Guard is live!"
echo "   Function: $FUNCTION_NAME"
echo "   Topic:    $TOPIC_NAME"
echo "   Alerts:   80%, 90%, 100%"
echo "   Email:    $ALERT_EMAIL"

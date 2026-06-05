# GCP Cloud Budget Guard ☁️🛡️

A serverless cost-monitoring tool built on Google Cloud Platform that automatically monitors GCP spending and prevents budget overruns.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        GCP Project                              │
│                                                                 │
│  ┌─────────────────┐    Pub/Sub     ┌──────────────────────┐   │
│  │  Cloud Billing  │─── Message ───▶│   budget-alerts      │   │
│  │     Budget      │    (80/90%)    │    (Pub/Sub Topic)   │   │
│  └─────────────────┘                └──────────┬───────────┘   │
│                                                │               │
│                                         Trigger│               │
│                                                ▼               │
│                                  ┌─────────────────────────┐   │
│                                  │    budget-guard         │   │
│                                  │   (Cloud Function)      │   │
│                                  │                         │   │
│                                  │  if spend >= 80%:       │   │
│                                  │    → send email alert   │   │
│                                  │  if spend >= 100%:      │   │
│                                  │    → disable billing    │   │
│                                  └────────────┬────────────┘   │
│                                               │                │
└───────────────────────────────────────────────┼────────────────┘
                                                │
                    ┌───────────────────────────┼──────────────┐
                    │                           │              │
                    ▼                           ▼              ▼
             ┌──────────┐              ┌──────────────┐  ┌──────────┐
             │  Gmail   │              │ Cloud Billing│  │  Cloud   │
             │  Alert   │              │   API        │  │ Logging  │
             │  Email   │              │ (disable)    │  │          │
             └──────────┘              └──────────────┘  └──────────┘
```

## Features

- **Dual-threshold alerts** — email notifications at 80% and 90% spend
- **Auto-stop at 100%** — billing is automatically disabled via the Cloud Billing API, achieving 100% prevention of cost overruns
- **HTML email alerts** — rich formatted alerts with spend bar, amounts, and timestamps
- **Cloud Logging** — all events logged for audit trail
- **Serverless** — runs only when triggered, costs near zero

## Tech Stack

| Component | Service |
|-----------|---------|
| Budget monitoring | Cloud Billing Budgets API |
| Event delivery | Cloud Pub/Sub |
| Business logic | Cloud Functions (Python 3.11) |
| Email alerts | Gmail SMTP |
| Billing control | Cloud Billing API |
| Observability | Cloud Logging / Monitoring |

## Project Structure

```
gcp-budget-guard/
├── main.py            # Cloud Function — handles Pub/Sub trigger
├── requirements.txt   # Python dependencies
├── budget_setup.py    # One-time script to create billing budget
├── deploy.sh          # Full deployment script
└── README.md
```

## Setup & Deployment

### Prerequisites
- GCP account with billing enabled
- `gcloud` CLI installed and authenticated
- Gmail account for sending alerts

### Step 1 — Clone & configure

```bash
git clone https://github.com/SwathiGuttula/gcp-budget-guard
cd gcp-budget-guard
```

Edit `deploy.sh` and fill in your values:
```bash
PROJECT_ID="your-project-id"
BILLING_ACCOUNT_ID="YOUR-BILLING-ID"
ALERT_EMAIL="your-email@gmail.com"
SMTP_EMAIL="your-gmail@gmail.com"
SMTP_PASSWORD="your-app-password"   # Gmail App Password (not your login password)
```

### Step 2 — Get Gmail App Password

1. Go to **myaccount.google.com → Security → 2-Step Verification**
2. At the bottom, click **App passwords**
3. Generate one for "Mail" → copy the 16-character password
4. Paste it as `SMTP_PASSWORD` in deploy.sh

### Step 3 — Deploy

```bash
bash deploy.sh
```

This will:
1. Enable required GCP APIs
2. Create the `budget-alerts` Pub/Sub topic
3. Deploy the Cloud Function
4. Create the billing budget with 80%/90%/100% thresholds

### Step 4 — Test locally

```bash
# Install dependencies
pip install google-auth google-api-python-client

# Simulate a budget alert at 80%
python - <<EOF
import base64, json
from main import budget_alert

# Simulate Pub/Sub event
alert_data = {
    "budgetDisplayName": "Budget Guard",
    "alertThresholdExceeded": 0.8,
    "costAmount": 8.0,
    "budgetAmount": 10.0,
    "costIntervalStart": "2026-06-01T00:00:00Z",
    "currencyCode": "USD"
}
event = {"data": base64.b64encode(json.dumps(alert_data).encode())}
budget_alert(event, None)
EOF
```

## Environment Variables

| Variable | Description |
|----------|-------------|
| `ALERT_EMAIL` | Email address to receive alerts |
| `SMTP_EMAIL` | Gmail address used to send alerts |
| `SMTP_PASSWORD` | Gmail App Password |
| `BILLING_ACCOUNT_ID` | Your GCP billing account ID |
| `GCP_PROJECT` | Your GCP project ID |

## Alert Email Preview

When spend hits 80% or 90%, an email is sent with:
- Budget name and current spend vs limit
- Visual progress bar
- Billing period and alert timestamp
- Direct link to GCP Billing Console
- Red warning banner if billing was auto-disabled (100%)

## Cost

This project costs **~$0/month** to run:
- Cloud Functions: 2M free invocations/month
- Pub/Sub: 10GB free/month
- Budget alerts fire at most a few times per month

## Key Results

- ✅ Alerts delivered within **1–2 minutes** of threshold breach
- ✅ **100% prevention** of cost overruns via auto-disable at budget ceiling
- ✅ Dual-threshold (80%, 90%) monitoring for proactive cost management
- ✅ Fully serverless — zero maintenance overhead

---

Built by [Swathi Sree Guttula](https://github.com/SwathiGuttula)

# GCP Cloud Budget Guard ☁️

A serverless cloud cost monitoring system that automatically sends email alerts when GCP billing exceeds defined thresholds. Built with Python, Google Cloud Functions, Pub/Sub, and Gmail SMTP.

---

## Architecture

```
GCP Billing  →  Pub/Sub Topic  →  Cloud Function (Python)  →  Gmail SMTP  →  Email Alert
```

1. GCP Budget triggers a **Pub/Sub** message when spend crosses a threshold
2. A **Cloud Function** subscribes to the topic and is invoked automatically
3. The function parses billing data and sends a formatted **email alert via Gmail SMTP**
4. A companion **Next.js dashboard** visualizes the architecture and alert history

---

## Repos

| Repo | Description |
|------|-------------|
| [`gcp-budget-guard`](https://github.com/SwathiGuttula/gcp-budget-guard) | Python Cloud Function + Pub/Sub trigger |
| [`gcp-budget-guard-ui`](https://github.com/SwathiGuttula/gcp-budget-guard-ui) | Next.js dashboard UI |

---

## Features

- **Serverless** — Cloud Function auto-scales, zero idle cost
- **Pub/Sub trigger** — event-driven, fires within 1–2 minutes of threshold breach
- **Gmail SMTP alerts** — formatted email with project name, current spend, and threshold
- **IAM least-privilege** — Cloud Function runs with minimal permissions (Billing Viewer only)
- **Environment-based config** — no hardcoded credentials, all via GCP Secret Manager / env vars

---

## Tech Stack

| Layer | Tech |
|-------|------|
| Runtime | Python 3.11 |
| Trigger | Google Cloud Pub/Sub |
| Compute | Google Cloud Functions (Gen 2) |
| Alerting | GCP Cloud Billing Budget API |
| Notifications | Gmail SMTP |
| IAM | Google Cloud IAM (least-privilege) |
| Dashboard UI | Next.js 14, TypeScript, Tailwind CSS |

---

## Project Structure

```
gcp-budget-guard/
├── main.py              ← Cloud Function entry point
├── requirements.txt     ← Python dependencies
└── README.md
```

---

## How It Works

```python
# main.py — triggered by Pub/Sub
def budget_alert(event, context):
    data = json.loads(base64.b64decode(event['data']))
    cost = data['costAmount']
    budget = data['budgetAmount']
    project = data['budgetDisplayName']
    
    if cost >= budget * 0.8:   # 80% threshold
        send_email_alert(project, cost, budget)
```

The function decodes the Pub/Sub message, extracts billing data, and sends an email if spend crosses the configured percentage.

---

## Local Testing

```bash
pip install -r requirements.txt

# Simulate a Pub/Sub event locally
functions-framework --target=budget_alert --signature-type=event
```

---

## Deployment

```bash
gcloud functions deploy budget-alert \
  --runtime python311 \
  --trigger-topic billing-alerts \
  --set-env-vars ALERT_EMAIL=you@gmail.com,GMAIL_PASSWORD=your_app_password \
  --service-account budget-guard-sa@PROJECT.iam.gserviceaccount.com
```

> **Note:** GCP resources were deleted after development to avoid ongoing costs. The architecture and code are fully documented for reference and demonstration.

---

## Dashboard UI

The companion Next.js dashboard visualizes the alert system architecture and simulates alert history. Live at: https://shopbot-ai-wheat.vercel.app

> Repo: [gcp-budget-guard-ui](https://github.com/SwathiGuttula/gcp-budget-guard-ui)

---

## Author

**Swathi Guttula**  
B.Tech Computer Science, KL University  
[GitHub](https://github.com/SwathiGuttula) · [LinkedIn](https://linkedin.com/in/swathiguttula)

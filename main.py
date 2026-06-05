"""
GCP Cloud Budget Guard
----------------------
Cloud Function triggered by Pub/Sub budget alerts.
- Sends email notifications at 80% and 90% budget thresholds
- Auto-disables billing at 100% to prevent cost overruns
- Logs all events to Cloud Monitoring
"""

import base64
import json
import os
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

from googleapiclient import discovery
from googleapiclient.errors import HttpError
import google.auth

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Environment variables (set in Cloud Function config)
ALERT_EMAIL        = os.environ.get("ALERT_EMAIL", "")
SMTP_EMAIL         = os.environ.get("SMTP_EMAIL", "")
SMTP_PASSWORD      = os.environ.get("SMTP_PASSWORD", "")
BILLING_ACCOUNT_ID = os.environ.get("BILLING_ACCOUNT_ID", "")
PROJECT_ID         = os.environ.get("GCP_PROJECT", "")


def budget_alert(event, context):
    """
    Entry point: triggered by Pub/Sub message from Cloud Billing budget.

    Pub/Sub message schema (from GCP Billing):
    {
        "budgetDisplayName": "Budget Guard",
        "alertThresholdExceeded": 0.8,
        "costAmount": 8.0,
        "costIntervalStart": "2026-06-01T00:00:00Z",
        "budgetAmount": 10.0,
        "budgetAmountType": "SPECIFIED_AMOUNT",
        "currencyCode": "USD"
    }
    """
    pubsub_data = base64.b64decode(event["data"]).decode("utf-8")
    budget_data = json.loads(pubsub_data)

    logger.info(f"Budget alert received: {json.dumps(budget_data, indent=2)}")

    budget_name    = budget_data.get("budgetDisplayName", "Unknown Budget")
    cost_amount    = budget_data.get("costAmount", 0)
    budget_amount  = budget_data.get("budgetAmount", 0)
    threshold      = budget_data.get("alertThresholdExceeded", 0)
    currency       = budget_data.get("currencyCode", "USD")
    interval_start = budget_data.get("costIntervalStart", "")

    # Calculate percentage
    percentage = round(threshold * 100)

    logger.info(
        f"Budget: {budget_name} | "
        f"Spent: {currency} {cost_amount} / {budget_amount} ({percentage}%)"
    )

    # Send email alert for 80% and 90% thresholds
    if threshold >= 0.8:
        send_alert_email(
            budget_name=budget_name,
            cost_amount=cost_amount,
            budget_amount=budget_amount,
            percentage=percentage,
            currency=currency,
            interval_start=interval_start,
        )

    # Auto-disable billing at 100%
    if threshold >= 1.0:
        logger.warning("Budget 100% exceeded — disabling billing to prevent overruns.")
        disable_billing(PROJECT_ID)


def send_alert_email(
    budget_name, cost_amount, budget_amount, percentage, currency, interval_start
):
    """Send an HTML email alert via Gmail SMTP."""
    if not all([SMTP_EMAIL, SMTP_PASSWORD, ALERT_EMAIL]):
        logger.error("Email credentials not configured. Skipping email alert.")
        return

    subject = f"⚠️ GCP Budget Alert: {percentage}% threshold reached — {budget_name}"

    # Determine alert severity color
    color = "#f59e0b" if percentage < 100 else "#ef4444"  # amber for <100%, red for 100%

    html_body = f"""
    <html>
    <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
        <div style="background: {color}; padding: 20px; border-radius: 8px 8px 0 0;">
            <h2 style="color: white; margin: 0;">
                ⚠️ GCP Budget Alert: {percentage}% Threshold Reached
            </h2>
        </div>
        <div style="background: #f8fafc; padding: 24px; border-radius: 0 0 8px 8px; border: 1px solid #e2e8f0;">
            <table style="width: 100%; border-collapse: collapse;">
                <tr>
                    <td style="padding: 8px 0; color: #64748b;">Budget Name</td>
                    <td style="padding: 8px 0; font-weight: bold;">{budget_name}</td>
                </tr>
                <tr>
                    <td style="padding: 8px 0; color: #64748b;">Amount Spent</td>
                    <td style="padding: 8px 0; font-weight: bold; color: {color};">
                        {currency} {cost_amount:.2f}
                    </td>
                </tr>
                <tr>
                    <td style="padding: 8px 0; color: #64748b;">Budget Limit</td>
                    <td style="padding: 8px 0;">{currency} {budget_amount:.2f}</td>
                </tr>
                <tr>
                    <td style="padding: 8px 0; color: #64748b;">Usage</td>
                    <td style="padding: 8px 0;">
                        <div style="background: #e2e8f0; border-radius: 4px; height: 8px;">
                            <div style="background: {color}; width: {min(percentage, 100)}%;
                                        height: 8px; border-radius: 4px;"></div>
                        </div>
                        <span style="font-weight: bold;">{percentage}%</span>
                    </td>
                </tr>
                <tr>
                    <td style="padding: 8px 0; color: #64748b;">Billing Period</td>
                    <td style="padding: 8px 0;">{interval_start[:10] if interval_start else 'N/A'}</td>
                </tr>
                <tr>
                    <td style="padding: 8px 0; color: #64748b;">Alert Time</td>
                    <td style="padding: 8px 0;">{datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}</td>
                </tr>
            </table>

            {"<div style='background: #fef2f2; border: 1px solid #ef4444; border-radius: 6px; padding: 12px; margin-top: 16px;'><strong style='color: #ef4444;'>🚨 Action Taken:</strong> Billing has been automatically disabled to prevent further charges.</div>" if percentage >= 100 else ""}

            <p style="color: #64748b; font-size: 14px; margin-top: 20px;">
                Review your GCP Console: 
                <a href="https://console.cloud.google.com/billing">console.cloud.google.com/billing</a>
            </p>
        </div>
    </body>
    </html>
    """

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"]    = SMTP_EMAIL
        msg["To"]      = ALERT_EMAIL
        msg.attach(MIMEText(html_body, "html"))

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(SMTP_EMAIL, SMTP_PASSWORD)
            server.sendmail(SMTP_EMAIL, ALERT_EMAIL, msg.as_string())

        logger.info(f"Alert email sent to {ALERT_EMAIL} ({percentage}% threshold)")

    except Exception as e:
        logger.error(f"Failed to send email: {e}")


def disable_billing(project_id: str):
    """
    Disable billing on the GCP project to hard-stop all charges.
    Uses the Cloud Billing API with Application Default Credentials.
    """
    if not project_id:
        logger.error("PROJECT_ID not set. Cannot disable billing.")
        return

    try:
        credentials, _ = google.auth.default(
            scopes=["https://www.googleapis.com/auth/cloud-billing"]
        )
        billing_service = discovery.build(
            "cloudbilling", "v1", credentials=credentials
        )

        billing_info = (
            billing_service.projects()
            .getBillingInfo(name=f"projects/{project_id}")
            .execute()
        )

        if billing_info.get("billingEnabled"):
            billing_service.projects().updateBillingInfo(
                name=f"projects/{project_id}",
                body={"billingAccountName": ""}  # Empty = disable billing
            ).execute()
            logger.info(f"✅ Billing disabled for project: {project_id}")
        else:
            logger.info(f"Billing already disabled for project: {project_id}")

    except HttpError as e:
        logger.error(f"Billing API error: {e}")
    except Exception as e:
        logger.error(f"Unexpected error disabling billing: {e}")

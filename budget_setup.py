"""
budget_setup.py
---------------
Run this script once to create the GCP Billing Budget
with 80% and 90% alert thresholds via the Billing Budgets API.

Usage:
    pip install google-cloud-billing-budgets
    python budget_setup.py
"""

from google.cloud import billing_budgets_v1
from google.type import money_pb2


def create_budget(
    billing_account_id: str,
    project_id: str,
    budget_amount_usd: float = 10.0,
):
    """
    Create a budget with dual threshold alerts (80% and 90%).

    Args:
        billing_account_id: e.g. "012345-6789AB-CDEF01"
        project_id:         e.g. "budget-guard-123456"
        budget_amount_usd:  Monthly budget limit in USD
    """
    client = billing_budgets_v1.BudgetServiceClient()
    parent = f"billingAccounts/{billing_account_id}"

    # Define the budget amount
    amount = billing_budgets_v1.BudgetAmount(
        specified_amount=money_pb2.Money(
            currency_code="USD",
            units=int(budget_amount_usd),
        )
    )

    # Scope budget to specific project
    budget_filter = billing_budgets_v1.Filter(
        projects=[f"projects/{project_id}"]
    )

    # Define alert thresholds: 80% and 90%
    thresholds = [
        billing_budgets_v1.ThresholdRule(
            threshold_percent=0.8,
            spend_basis=billing_budgets_v1.ThresholdRule.Basis.CURRENT_SPEND,
        ),
        billing_budgets_v1.ThresholdRule(
            threshold_percent=0.9,
            spend_basis=billing_budgets_v1.ThresholdRule.Basis.CURRENT_SPEND,
        ),
        billing_budgets_v1.ThresholdRule(
            threshold_percent=1.0,
            spend_basis=billing_budgets_v1.ThresholdRule.Basis.CURRENT_SPEND,
        ),
    ]

    # Pub/Sub topic to publish alerts to
    pubsub_topic = f"projects/{project_id}/topics/budget-alerts"
    notifications = billing_budgets_v1.NotificationsRule(
        pubsub_topic=pubsub_topic,
        disable_default_iam_recipients=False,
    )

    budget = billing_budgets_v1.Budget(
        display_name="Budget Guard",
        budget_filter=budget_filter,
        amount=amount,
        threshold_rules=thresholds,
        notifications_rule=notifications,
    )

    created = client.create_budget(parent=parent, budget=budget)
    print(f"✅ Budget created: {created.name}")
    print(f"   Amount: ${budget_amount_usd} USD")
    print(f"   Thresholds: 80%, 90%, 100%")
    print(f"   Pub/Sub topic: {pubsub_topic}")
    return created


if __name__ == "__main__":
    import os

    BILLING_ACCOUNT_ID = os.environ.get("BILLING_ACCOUNT_ID", "YOUR_BILLING_ACCOUNT_ID")
    PROJECT_ID         = os.environ.get("GCP_PROJECT", "YOUR_PROJECT_ID")
    BUDGET_AMOUNT      = float(os.environ.get("BUDGET_AMOUNT_USD", "10.0"))

    create_budget(
        billing_account_id=BILLING_ACCOUNT_ID,
        project_id=PROJECT_ID,
        budget_amount_usd=BUDGET_AMOUNT,
    )

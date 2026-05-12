#!/usr/bin/env python3
"""Budget notification and date helper.

Subcommands:
    notifications   Generate budget notification JSON (80% + 100% thresholds)
    start-date      Print budget start date (1st of current month)
    end-date        Print budget end date (1st of month, 1 year from now)
    budget-json     Generate complete AWS Budget JSON structure

Works for AWS Budgets. Uses only stdlib (no GNU date dependency).
"""
import json
import sys
from datetime import datetime, timedelta


def notifications(args):
    """Generate notification subscribers JSON for AWS Budgets."""
    email = args.email
    notifs = [
        {
            "NotificationType": "ACTUAL",
            "ComparisonOperator": "GREATER_THAN",
            "Threshold": 80.0,
            "ThresholdType": "PERCENTAGE",
            "NotificationState": "ALARM"
        },
        {
            "NotificationType": "ACTUAL",
            "ComparisonOperator": "GREATER_THAN",
            "Threshold": 100.0,
            "ThresholdType": "PERCENTAGE",
            "NotificationState": "ALARM"
        }
    ]
    subscribers = [{"SubscriptionType": "EMAIL", "Address": email}]
    result = [
        {"Notification": n, "Subscribers": subscribers}
        for n in notifs
    ]
    print(json.dumps(result, indent=2))


def start_date(_args):
    """Print first day of current month."""
    now = datetime.now()
    print(now.strftime("%Y-%m-01"))


def end_date(_args):
    """Print first day of month, one year from now."""
    now = datetime.now()
    year = now.year + 1
    print(f"{year}-{now.month:02d}-01")


def budget_json(args):
    """Generate complete AWS Budget JSON."""
    now = datetime.now()
    budget = {
        "BudgetName": args.name,
        "BudgetLimit": {
            "Amount": str(args.amount),
            "Unit": "USD"
        },
        "BudgetType": "COST",
        "TimeUnit": "MONTHLY",
        "TimePeriod": {
            "Start": now.strftime("%Y-%m-01"),
            "End": f"{now.year + 1}-{now.month:02d}-01"
        },
        "CostTypes": {
            "IncludeTax": True,
            "IncludeSubscription": True,
            "UseBlended": False,
            "IncludeRefund": False,
            "IncludeCredit": False,
            "IncludeUpfront": True,
            "IncludeRecurring": True,
            "IncludeOtherSubscription": True,
            "IncludeSupport": True,
            "IncludeDiscount": True,
            "UseAmortized": False
        }
    }
    if args.tag_key and args.tag_value:
        budget["CostFilters"] = {
            "TagKeyValue": [f"user:{args.tag_key}${args.tag_value}"]
        }
    print(json.dumps(budget, indent=2))


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command")

    p_notif = sub.add_parser("notifications", help="Generate notification JSON")
    p_notif.add_argument("--email", required=True)

    sub.add_parser("start-date", help="Budget start date")
    sub.add_parser("end-date", help="Budget end date")

    p_budget = sub.add_parser("budget-json", help="Generate full budget JSON")
    p_budget.add_argument("--name", required=True)
    p_budget.add_argument("--amount", required=True, type=int)
    p_budget.add_argument("--tag-key", default="")
    p_budget.add_argument("--tag-value", default="")

    args = parser.parse_args()
    if args.command == "notifications":
        notifications(args)
    elif args.command == "start-date":
        start_date(args)
    elif args.command == "end-date":
        end_date(args)
    elif args.command == "budget-json":
        budget_json(args)
    else:
        parser.print_help()
        sys.exit(1)

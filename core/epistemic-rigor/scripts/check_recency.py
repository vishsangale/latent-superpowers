#!/usr/bin/env python3
"""Check if a cited date is older than a specified threshold."""

import argparse
from datetime import datetime
from dateutil.relativedelta import relativedelta


def main():
    parser = argparse.ArgumentParser(description="Flag potentially outdated claims based on recency.")
    parser.add_argument("--date", required=True, help="Date of the claim or paper in YYYY-MM format")
    parser.add_argument("--months", type=int, default=12, help="Threshold in months to consider 'outdated'")
    args = parser.parse_args()

    try:
        claim_date = datetime.strptime(args.date, "%Y-%m")
    except ValueError:
        print(f"Error: Invalid date format '{args.date}'. Expected YYYY-MM.")
        return 1

    now = datetime.now()
    threshold_date = now - relativedelta(months=args.months)

    if claim_date < threshold_date:
        print(f"[RECENCY WARNING] The cited date ({args.date}) is older than {args.months} months.")
        print("Please verify if there are newer SOTA benchmarks or papers superseding this claim.")
        return 1
    else:
        print(f"[OK] The cited date ({args.date}) is within the {args.months}-month threshold.")
        return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""CLI demo for the prediction -> WhatsApp trigger flow.

Example:
    python .\demo_predict_and_trigger.py --base-url http://localhost:8000 --days-ahead 7 --auto-trigger
"""

import argparse
import json
import urllib.request


def call_json(url: str):
    with urllib.request.urlopen(url) as response:
        return json.loads(response.read().decode("utf-8"))


def main():
    parser = argparse.ArgumentParser(description="Show the prediction -> donor WhatsApp trigger flow from the CLI")
    parser.add_argument("--base-url", default="http://localhost:8000", help="Backend base URL")
    parser.add_argument("--days-ahead", type=int, default=7, help="How many days to look ahead")
    parser.add_argument("--auto-trigger", action="store_true", help="Automatically send donation requests after prediction")
    parser.add_argument("--hospital-id", default="HOSPITAL_CITY", help="Hospital id used by auto-trigger")
    parser.add_argument("--max-distance-km", type=float, default=5.0, help="Search radius for nearby donors")
    args = parser.parse_args()

    endpoint = (
        f"{args.base_url}/api/predict/patients?days_ahead={args.days_ahead}"
        f"&include_overdue=true&auto_trigger={'true' if args.auto_trigger else 'false'}"
        f"&hospital_id={args.hospital_id}&max_distance_km={args.max_distance_km}"
    )

    print("Calling:", endpoint)
    result = call_json(endpoint)
    print("\nPrediction result:")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()

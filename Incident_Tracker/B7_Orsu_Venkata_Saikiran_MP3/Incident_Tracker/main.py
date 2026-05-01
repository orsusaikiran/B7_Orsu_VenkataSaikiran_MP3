
import argparse
import json
import logging
import os
import sys

# Bootstrap: configure logging before importing project modules
from config import LOG_LEVEL, LOG_FILE, MOCK_API

logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger("main")

# Project imports

from models.incident import (
    Incident,
    NetworkIncident,
    AppIncident,
    SecurityIncident,
    IncidentIterator,
    batch_incidents,
)
from models.report import ReportGenerator
from services import create_ticket, create_issue, create_work_item
from utils.classifier import detect_type
from utils.helpers import summarise


# Factory: build the correct subclass from a raw JSON record

def incident_factory(record: dict) -> Incident:
    """
    Validate the record schema, detect the incident type and instantiate
    the appropriate Incident subclass.
    """
    Incident.validate_schema(record)

    # Detect type from title + description before instantiation

    text = f"{record['title']} {record['description']}"
    inc_type = detect_type(text)

    common = {
        "id":            record["id"],
        "title":         record["title"],
        "description":   record["description"],
        "reported_by":   record["reported_by"],
        "timestamp":     record["timestamp"],
        "assigned_team": record["assigned_team"],
    }

    if inc_type == "network":
        return NetworkIncident(
            affected_host=record.get("affected_host", ""),
            protocol=record.get("protocol", ""),
            **common,
        )
    elif inc_type == "security":
        return SecurityIncident(
            threat_type=record.get("threat_type", ""),
            source_ip=record.get("source_ip", ""),
            **common,
        )
    elif inc_type == "app":
        return AppIncident(
            app_name=record.get("app_name", ""),
            error_code=record.get("error_code", ""),
            **common,
        )
    else:
        # Fallback to AppIncident for 'general' type
        return AppIncident(**common)


# Load incidents from JSON

def load_incidents(filepath: str) -> list:
    if not os.path.exists(filepath):
        logger.error(f"Input file not found: {filepath}")
        sys.exit(1)

    with open(filepath, "r", encoding="utf-8") as fh:
        records = json.load(fh)

    incidents = []
    for rec in records:
        try:
            inc = incident_factory(rec)
            inc.classify()
            incidents.append(inc)
            logger.info(f"Loaded  {inc.id}: type={inc.incident_type}, severity={inc.severity}")
        except (ValueError, KeyError) as exc:
            logger.warning(f"Skipping malformed record: {exc}")

    return incidents


# Push to all three platforms (in batches)

def push_all(incidents: list, batch_size: int = 3) -> None:
    total = len(incidents)
    logger.info(f"Pushing {total} incidents in batches of {batch_size}…")

    for batch_num, batch in enumerate(batch_incidents(incidents, batch_size), start=1):
        logger.info(f"  ── Batch {batch_num} ({len(batch)} incidents) ──")
        for inc in batch:
            print(f"\n  Processing [{inc.id}] {inc.title}")
            create_ticket(inc)       # ServiceNow
            create_issue(inc)        # Jira
            create_work_item(inc)    # Azure Boards


# CLI argument parsing

def parse_args():
    parser = argparse.ArgumentParser(
        description="IT Incident Auto-Triage & Tracker",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--input",
        default="data/incidents.json",
        help="Path to incidents JSON file (default: data/incidents.json)",
    )
    parser.add_argument(
        "--severity",
        choices=["critical", "high", "medium", "low"],
        default=None,
        help="Only push incidents of this severity level",
    )
    parser.add_argument(
        "--no-report",
        action="store_true",
        help="Skip generating the HTML report",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=3,
        help="Number of incidents per processing batch (default: 3)",
    )
    return parser.parse_args()


# Main pipeline


def main():
    args = parse_args()

    print("=" * 60)
    print("  IT Incident Auto-Triage & Tracker")
    print(f"  Mode: {'MOCK' if MOCK_API else 'LIVE'}")
    print("=" * 60)

    # 1. Load & classify
    logger.info(f"Loading incidents from {args.input}")
    all_incidents = load_incidents(args.input)
    print(f"\n✔  Loaded and classified {len(all_incidents)} incidents.")

    # 2. Optional severity filter (stretch goal --severity flag)
    if args.severity:
        iterator = IncidentIterator(all_incidents, severity_filter=args.severity)
        incidents_to_push = list(iterator)
        print(f"   Filtered to {len(incidents_to_push)} incident(s) with severity='{args.severity}'.")
    else:
        incidents_to_push = sorted(all_incidents)   # sort critical-first

    if not incidents_to_push:
        print("   No incidents matched the filter. Exiting.")
        sys.exit(0)

    # 3. Print summary before pushing
    stats = summarise(all_incidents)
    print(f"\n📊 Summary:")
    print(f"   Total loaded    : {stats['total']}")
    print(f"   By severity     : {stats['by_severity']}")
    print(f"   By type         : {stats['by_type']}")
    print(f"   By team         : {stats['by_team']}")
    print(f"   Critical IDs    : {stats['critical_ids']}")

    # 4. Push tickets (batched, with @log_call + @retry on each service)
    print(f"\n🚀 Pushing {len(incidents_to_push)} incidents to ServiceNow, Jira, Azure Boards…")
    push_all(incidents_to_push, batch_size=args.batch_size)

    # 5. Domain-specific actions
    print("\n⚡ Running domain actions…")
    for inc in incidents_to_push:
        if isinstance(inc, NetworkIncident) and inc.severity in ("critical", "high"):
            inc.escalate()
        elif isinstance(inc, SecurityIncident):
            inc.notify_soc()
        elif isinstance(inc, AppIncident) and inc.severity in ("critical", "high"):
            inc.get_stack_trace()

    # 6. Generate report (all incidents, not just filtered)
    if not args.no_report:
        print("\n📄 Generating HTML report…")
        rg = ReportGenerator(all_incidents)
        html_path = rg.generate_html("output/report.html")
        json_path = rg.export_json("output/summary.json")
        print(f"   HTML → {html_path}")
        print(f"   JSON → {json_path}")

    print("\n✅ Pipeline complete.")
    print("=" * 60)


if __name__ == "__main__":
    main()

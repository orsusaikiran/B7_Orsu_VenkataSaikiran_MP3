

import base64
import json
import logging
import uuid

logger = logging.getLogger(__name__)

try:
    import requests
    _REQUESTS_AVAILABLE = True
except ImportError:
    _REQUESTS_AVAILABLE = False

from config import (
    MOCK_API,
    SNOW_INSTANCE,
    SNOW_USERNAME,
    SNOW_PASSWORD,
)
from utils.decorators import log_call, retry

_BASE_URL = f"https://{SNOW_INSTANCE}.service-now.com/api/now/table/incident"

_SEVERITY_TO_URGENCY = {
    "critical": 1,
    "high":     1,
    "medium":   2,
    "low":      3,
}


def _build_payload(incident) -> dict:
    return {
        "short_description": incident.title,
        "description":       incident.description,
        "urgency":           str(_SEVERITY_TO_URGENCY.get(incident.severity, 3)),
        "category":          incident.incident_type or "general",
        "assignment_group":  incident.assigned_team,
        "caller_id":         incident.reported_by,
    }


@log_call
@retry(times=3, delay=1.0)
def create_ticket(incident) -> str:
    
    payload = _build_payload(incident)

    if MOCK_API:
        mock_id = f"MOCK-SNOW-{incident.id}"
        logger.info(f"[MOCK] ServiceNow payload for {incident.id}:\n{json.dumps(payload, indent=2)}")
        print(f"  [ServiceNow MOCK] Created ticket {mock_id} for incident {incident.id}")
        incident.ticket_ids["snow"] = mock_id
        return mock_id

    if not _REQUESTS_AVAILABLE:
        raise RuntimeError("requests library not installed. Run: pip install requests")

    auth_str = base64.b64encode(f"{SNOW_USERNAME}:{SNOW_PASSWORD}".encode()).decode()
    headers = {
        "Content-Type":  "application/json",
        "Accept":        "application/json",
        "Authorization": f"Basic {auth_str}",
    }
    response = requests.post(_BASE_URL, headers=headers, json=payload, timeout=10)
    response.raise_for_status()
    sys_id = response.json()["result"]["sys_id"]
    incident.ticket_ids["snow"] = sys_id
    logger.info(f"ServiceNow ticket created: {sys_id} for incident {incident.id}")
    return sys_id


@log_call
@retry(times=3, delay=1.0)
def update_status(incident, status: str = "resolved") -> bool:
    """Patch the status field of an existing ServiceNow ticket."""
    sys_id = incident.ticket_ids.get("snow")
    if not sys_id:
        logger.warning(f"No ServiceNow ticket ID on incident {incident.id}; skipping update.")
        return False

    payload = {"state": status}

    if MOCK_API:
        print(f"  [ServiceNow MOCK] Updated {sys_id} → status={status}")
        return True

    if not _REQUESTS_AVAILABLE:
        raise RuntimeError("requests library not installed.")

    auth_str = base64.b64encode(f"{SNOW_USERNAME}:{SNOW_PASSWORD}".encode()).decode()
    headers = {
        "Content-Type":  "application/json",
        "Accept":        "application/json",
        "Authorization": f"Basic {auth_str}",
    }
    url = f"{_BASE_URL}/{sys_id}"
    response = requests.patch(url, headers=headers, json=payload, timeout=10)
    response.raise_for_status()
    return True

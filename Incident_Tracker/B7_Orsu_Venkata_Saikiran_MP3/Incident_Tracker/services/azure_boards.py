

import base64
import json
import logging

logger = logging.getLogger(__name__)

try:
    import requests
    _REQUESTS_AVAILABLE = True
except ImportError:
    _REQUESTS_AVAILABLE = False

from config import (
    MOCK_API,
    AZURE_ORG,
    AZURE_PROJECT,
    AZURE_PAT,
)
from utils.decorators import log_call, retry

_BASE_URL = (
    f"https://dev.azure.com/{AZURE_ORG}/{AZURE_PROJECT}/"
    f"_apis/wit/workitems/$Bug?api-version=7.1"
)

_SEVERITY_TO_PRIORITY = {
    "critical": 1,
    "high":     2,
    "medium":   3,
    "low":      4,
}


def _build_auth_header() -> str:
    # Azure DevOps expects Basic auth with an empty username and the PAT as password
    token = base64.b64encode(f":{AZURE_PAT}".encode()).decode()
    return f"Basic {token}"


def _build_patch_payload(incident) -> list:
    """Build the JSON Patch array required by Azure Boards."""
    return [
        {
            "op":    "add",
            "path":  "/fields/System.Title",
            "value": incident.title,
        },
        {
            "op":    "add",
            "path":  "/fields/System.Description",
            "value": incident.description,
        },
        {
            "op":    "add",
            "path":  "/fields/Microsoft.VSTS.Common.Priority",
            "value": _SEVERITY_TO_PRIORITY.get(incident.severity, 4),
        },
        {
            "op":    "add",
            "path":  "/fields/System.AssignedTo",
            "value": incident.assigned_team,
        },
        {
            "op":    "add",
            "path":  "/fields/System.Tags",
            "value": f"{incident.incident_type}; {incident.severity}",
        },
    ]


@log_call
@retry(times=3, delay=1.0)
def create_work_item(incident) -> str:
   
    payload = _build_patch_payload(incident)

    if MOCK_API:
        mock_id = str(abs(hash(incident.id)) % 90000 + 10000)
        logger.info(f"[MOCK] Azure Boards payload for {incident.id}:\n{json.dumps(payload, indent=2)}")
        print(f"  [Azure Boards MOCK] Created work item #{mock_id} for incident {incident.id}")
        incident.ticket_ids["azure"] = f"AB-{mock_id}"
        return mock_id

    if not _REQUESTS_AVAILABLE:
        raise RuntimeError("requests library not installed. Run: pip install requests")

    headers = {
        "Content-Type":  "application/json-patch+json",
        "Accept":        "application/json",
        "Authorization": _build_auth_header(),
    }
    response = requests.post(_BASE_URL, headers=headers, json=payload, timeout=10)
    response.raise_for_status()
    work_item_id = str(response.json()["id"])
    incident.ticket_ids["azure"] = work_item_id
    logger.info(f"Azure Boards work item created: #{work_item_id} for incident {incident.id}")
    return work_item_id

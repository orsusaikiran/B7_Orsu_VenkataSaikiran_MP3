

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
    JIRA_DOMAIN,
    JIRA_EMAIL,
    JIRA_API_TOKEN,
    JIRA_PROJECT_KEY,
)
from utils.decorators import log_call, retry

_BASE_URL = f"https://{JIRA_DOMAIN}.atlassian.net/rest/api/3/issue"

_SEVERITY_TO_PRIORITY = {
    "critical": "Highest",
    "high":     "High",
    "medium":   "Medium",
    "low":      "Low",
}


def _build_auth_header() -> str:
    token = base64.b64encode(f"{JIRA_EMAIL}:{JIRA_API_TOKEN}".encode()).decode()
    return f"Basic {token}"


def _build_payload(incident) -> dict:
    return {
        "fields": {
            "project":     {"key": JIRA_PROJECT_KEY},
            "summary":     incident.title,
            "description": {
                "type":    "doc",
                "version": 1,
                "content": [
                    {
                        "type":    "paragraph",
                        "content": [{"type": "text", "text": incident.description}],
                    }
                ],
            },
            "issuetype": {"name": "Bug"},
            "priority":  {"name": _SEVERITY_TO_PRIORITY.get(incident.severity, "Low")},
            "labels":    [incident.incident_type or "general", incident.assigned_team],
        }
    }


@log_call
@retry(times=3, delay=1.0)
def create_issue(incident) -> str:
    
    payload = _build_payload(incident)

    if MOCK_API:
        counter = abs(hash(incident.id)) % 900 + 100   # deterministic fake number
        mock_key = f"{JIRA_PROJECT_KEY}-{counter}"
        logger.info(f"[MOCK] Jira payload for {incident.id}:\n{json.dumps(payload, indent=2)}")
        print(f"  [Jira MOCK] Created issue {mock_key} for incident {incident.id}")
        incident.ticket_ids["jira"] = mock_key
        return mock_key

    if not _REQUESTS_AVAILABLE:
        raise RuntimeError("requests library not installed. Run: pip install requests")

    headers = {
        "Content-Type":  "application/json",
        "Accept":        "application/json",
        "Authorization": _build_auth_header(),
    }
    response = requests.post(_BASE_URL, headers=headers, json=payload, timeout=10)
    response.raise_for_status()
    key = response.json()["key"]
    incident.ticket_ids["jira"] = key
    logger.info(f"Jira issue created: {key} for incident {incident.id}")
    return key


@log_call
@retry(times=3, delay=1.0)
def update_priority(incident, priority: str = "Low") -> bool:
    """Update the priority of an existing Jira issue."""
    jira_key = incident.ticket_ids.get("jira")
    if not jira_key:
        logger.warning(f"No Jira key on incident {incident.id}; skipping update.")
        return False

    if MOCK_API:
        print(f"  [Jira MOCK] Updated {jira_key} → priority={priority}")
        return True

    if not _REQUESTS_AVAILABLE:
        raise RuntimeError("requests library not installed.")

    url = f"{_BASE_URL}/{jira_key}"
    payload = {"fields": {"priority": {"name": priority}}}
    headers = {
        "Content-Type":  "application/json",
        "Accept":        "application/json",
        "Authorization": _build_auth_header(),
    }
    response = requests.put(url, headers=headers, json=payload, timeout=10)
    response.raise_for_status()
    return True

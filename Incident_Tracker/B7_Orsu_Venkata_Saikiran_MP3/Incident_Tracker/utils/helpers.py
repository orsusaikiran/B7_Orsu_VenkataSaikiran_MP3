

from functools import reduce


def get_critical_incidents(incidents: list) -> list:
    """Return only incidents whose severity is 'critical' (uses filter)."""
    return list(filter(lambda i: i.severity == "critical", incidents))


def get_incidents_by_severity(incidents: list, severity: str) -> list:
    """Return incidents matching a specific severity level (uses filter)."""
    return list(filter(lambda i: i.severity == severity.lower(), incidents))


def build_jira_payloads(incidents: list) -> list:
    """Return a list of to_dict() representations suitable for Jira (uses map)."""
    return list(map(lambda i: i.to_dict(), incidents))


def count_by_team(incidents: list) -> dict:
    """
    Return a dict mapping each team name to the number of incidents assigned.
    Uses reduce so the entire aggregation is a single expression.
    """
    return reduce(
        lambda acc, i: {**acc, i.assigned_team: acc.get(i.assigned_team, 0) + 1},
        incidents,
        {},
    )


def count_by_type(incidents: list) -> dict:
    """Return a dict mapping each incident type to its count (uses reduce)."""
    return reduce(
        lambda acc, i: {**acc, (i.incident_type or "general"): acc.get(i.incident_type or "general", 0) + 1},
        incidents,
        {},
    )


def count_by_severity(incidents: list) -> dict:
    """Return a dict mapping each severity level to its count (uses reduce)."""
    return reduce(
        lambda acc, i: {**acc, (i.severity or "low"): acc.get(i.severity or "low", 0) + 1},
        incidents,
        {},
    )


def get_incident_titles(incidents: list) -> list:
    """Return a list of all incident titles (uses map)."""
    return list(map(lambda i: i.title, incidents))


def summarise(incidents: list) -> dict:
    """Return a high-level statistics dict for the processed incident set."""
    return {
        "total":          len(incidents),
        "by_team":        count_by_team(incidents),
        "by_type":        count_by_type(incidents),
        "by_severity":    count_by_severity(incidents),
        "critical_ids":   [i.id for i in get_critical_incidents(incidents)],
    }

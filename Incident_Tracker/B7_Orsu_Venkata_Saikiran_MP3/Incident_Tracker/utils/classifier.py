
import re

# Pre-compiled patterns

# Incident TYPE patterns
_PATTERN_NETWORK = re.compile(
    r"""
    \b(
        \d{1,3}(?:\.\d{1,3}){3}     # IPv4 address (e.g. 192.168.1.45)
      | TCP | UDP | ICMP             # protocol names
      | VLAN                         # virtual LAN
      | switch | firewall            # network devices
      | router | gateway | bandwidth
      | packet\s*loss | latency
      | DNS | BGP | OSPF
      | network | ethernet
    )\b
    """,
    re.IGNORECASE | re.VERBOSE,
)

_PATTERN_SECURITY = re.compile(
    r"""
    \b(
        breach | ransomware | brute[\-\s]?force
      | malware | phishing | unauthorized
      | exploit | intrusion | vulnerability
      | trojan | virus | spyware | credential
      | suspicious\s+login | data\s+leak | SOC
      | threat | attack
    )\b
    """,
    re.IGNORECASE | re.VERBOSE,
)

_PATTERN_APP = re.compile(
    r"""
    \b(
        NullPointerException | StackOverflowError
      | OutOfMemoryError | RuntimeException
      | HTTP[\-\s]?\d{3}               # HTTP-503, HTTP503, HTTP 503
      | error\s*code | exception
      | stack\s*trace | timeout
      | deploy | build | CI | pipeline
      | app | application | service | API
      | 5\d{2} | 4\d{2}               # 5xx / 4xx HTTP codes standalone
    )\b
    """,
    re.IGNORECASE | re.VERBOSE,
)

# Incident SEVERITY patterns
_PATTERN_CRITICAL = re.compile(
    r"\b(outage|down|breach|ransomware|production|prod\b|critical|emergency|offline)\b",
    re.IGNORECASE,
)

_PATTERN_HIGH = re.compile(
    r"\b(timeout|failing|unavailable|unreachable|high|severe|major|crashed|brute[\-\s]?force|unauthorized)\b",
    re.IGNORECASE,
)

_PATTERN_MEDIUM = re.compile(
    r"\b(slow|degraded|warning|intermittent|medium|moderate|partial|delayed)\b",
    re.IGNORECASE,
)

# ---------------------------------------------------------------------------
# Public functions
# ---------------------------------------------------------------------------

def detect_type(text: str) -> str:
    """
    Return the most likely incident type based on keyword density.
    Priority order if multiple patterns match: security > network > app > general.

    Parameters
    ----------
    text : str
        Combined title + description of the incident.

    Returns
    -------
    str  — one of 'network', 'security', 'app', 'general'
    """
    security_hits = len(_PATTERN_SECURITY.findall(text))
    network_hits  = len(_PATTERN_NETWORK.findall(text))
    app_hits      = len(_PATTERN_APP.findall(text))

    scores = {
        "security": security_hits,
        "network":  network_hits,
        "app":      app_hits,
    }
    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else "general"


def detect_severity(text: str) -> str:
    """
    Return the severity level of an incident based on keyword matching.
    Evaluated in order: critical → high → medium → low.

    Parameters
    ----------
    text : str
        Combined title + description of the incident.

    Returns
    -------
    str  — one of 'critical', 'high', 'medium', 'low'
    """
    if _PATTERN_CRITICAL.search(text):
        return "critical"
    if _PATTERN_HIGH.search(text):
        return "high"
    if _PATTERN_MEDIUM.search(text):
        return "medium"
    return "low"

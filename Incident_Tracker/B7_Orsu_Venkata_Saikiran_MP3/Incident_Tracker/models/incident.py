
from datetime import datetime, timezone
from utils.classifier import detect_type, detect_severity


# ---------------------------------------------------------------------------
# Severity ordering helper (lower int = higher priority)
# ---------------------------------------------------------------------------
_SEVERITY_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3}


class Incident:
    """Base class for all IT incidents."""

    # JSON schema required fields  used by the static validator
    _REQUIRED_FIELDS = {"id", "title", "description", "reported_by", "timestamp", "assigned_team"}

    def __init__(self, id, title, description, reported_by, timestamp, assigned_team):
        self.id            = id
        self.title         = title
        self.description   = description
        self.reported_by   = reported_by
        self.timestamp     = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        self.assigned_team = assigned_team
        self._severity     = None   # private — set by classify()
        self._type         = None   # private — set by classify()
        self.ticket_ids    = {}     # populated after API calls: {'snow': ..., 'jira': ..., 'azure': ...}

    # Properties
    @property
    def severity(self):
        return self._severity

    @property
    def incident_type(self):
        return self._type

    # Abstract method — every subclass MUST override this
    def classify(self):
        raise NotImplementedError("Subclasses must implement classify()")

    # Serialisation helpers
    def to_dict(self):
        return {
            "id":            self.id,
            "title":         self.title,
            "description":   self.description,
            "reported_by":   self.reported_by,
            "timestamp":     self.timestamp.isoformat(),
            "assigned_team": self.assigned_team,
            "severity":      self._severity,
            "type":          self._type,
            "ticket_ids":    self.ticket_ids,
        }

    def __str__(self):
        return (
            f"[{self.id}] {self.title} | "
            f"type={self._type} | severity={self._severity} | "
            f"team={self.assigned_team}"
        )

    def __repr__(self):
        return f"{self.__class__.__name__}(id={self.id!r}, severity={self._severity!r})"

    def __lt__(self, other):
        """Enables sorting by severity: critical < high < medium < low."""
        return _SEVERITY_ORDER.get(self._severity, 99) < _SEVERITY_ORDER.get(other._severity, 99)

    
    # Static schema validator (stretch goal)
    @staticmethod
    def validate_schema(record: dict) -> bool:
        """Return True if a raw JSON record has all required fields."""
        missing = Incident._REQUIRED_FIELDS - record.keys()
        if missing:
            raise ValueError(f"Incident record {record.get('id', '?')} missing fields: {missing}")
        return True



# NetworkIncident
class NetworkIncident(Incident):
    """Represents a network-layer incident (IP, VLAN, switch, protocol faults)."""

    def __init__(self, affected_host="", protocol="", **kwargs):
        super().__init__(**kwargs)
        self.affected_host = affected_host
        self.protocol      = protocol

    def classify(self):
        text = f"{self.title} {self.description}"
        self._type     = detect_type(text)      # should resolve to 'network'
        self._severity = detect_severity(text)
        return self

    def escalate(self):
        """Simulate paging the on-call network team."""
        msg = (
            f"[ESCALATE] NetworkIncident {self.id} — severity={self._severity} — "
            f"host={self.affected_host}, protocol={self.protocol} — "
            f"On-call network team notified."
        )
        print(msg)
        return msg


# AppIncident
class AppIncident(Incident):
    """Represents an application-layer incident (errors, exceptions, HTTP faults)."""

    def __init__(self, app_name="", error_code="", **kwargs):
        super().__init__(**kwargs)
        self.app_name   = app_name
        self.error_code = error_code

    def classify(self):
        text = f"{self.title} {self.description}"
        self._type     = detect_type(text)
        self._severity = detect_severity(text)
        return self

    def get_stack_trace(self):
        """Return a simulated log snippet for the incident."""
        snippet = (
            f"[LOG SNIPPET] AppIncident {self.id} — app={self.app_name} "
            f"error_code={self.error_code}\n"
            f"  java.lang.NullPointerException at com.example.{self.app_name}.Service.process(Service.java:42)"
        )
        print(snippet)
        return snippet


# SecurityIncident
class SecurityIncident(Incident):
    """Represents a security incident (breach, ransomware, phishing, etc.)."""

    def __init__(self, threat_type="", source_ip="", **kwargs):
        super().__init__(**kwargs)
        self.threat_type = threat_type
        self.source_ip   = source_ip

    def classify(self):
        text = f"{self.title} {self.description}"
        self._type     = detect_type(text)
        self._severity = detect_severity(text)
        return self

    def notify_soc(self):
        """Simulate sending an alert to the Security Operations Centre."""
        msg = (
            f"[SOC ALERT] SecurityIncident {self.id} — threat={self.threat_type} "
            f"source_ip={self.source_ip} — severity={self._severity} — "
            f"SOC team alerted immediately."
        )
        print(msg)
        return msg


# IncidentIterator
class IncidentIterator:
   
    def __init__(self, incidents: list, severity_filter: str = None):
        self._incidents      = incidents
        self._severity_filter = severity_filter.lower() if severity_filter else None
        self._index          = 0

        # Pre-filter once so __next__ is O(1)
        if self._severity_filter:
            self._items = [i for i in incidents if i.severity == self._severity_filter]
        else:
            self._items = list(incidents)

    def __iter__(self):
        return self

    def __next__(self):
        if self._index >= len(self._items):
            raise StopIteration
        item = self._items[self._index]
        self._index += 1
        return item

    def __len__(self):
        return len(self._items)


# Batch generator
def batch_incidents(incidents, batch_size=3):
    """Yield incidents in batches of batch_size."""
    for i in range(0, len(incidents), batch_size):
        yield incidents[i: i + batch_size]

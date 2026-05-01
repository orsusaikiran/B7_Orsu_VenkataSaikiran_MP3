

import json
import os
from datetime import datetime, timezone


# Severity badge colours matching the sample screenshot
_SEVERITY_COLOURS = {
    "critical": ("#c0392b", "#fff"),
    "high":     ("#e67e22", "#fff"),
    "medium":   ("#f1c40f", "#333"),
    "low":      ("#27ae60", "#fff"),
}

_TYPE_ICONS = {
    "network":  "🌐",
    "security": "🔒",
    "app":      "⚙️",
    "general":  "📋",
}


class ReportGenerator:
    """Generates an HTML and JSON report from processed incidents."""

    def __init__(self, incidents: list):
        self._incidents = incidents

    # ------------------------------------------------------------------
    # HTML report
    # ------------------------------------------------------------------
    def generate_html(self, output_path: str = "output/report.html") -> str:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        now_str       = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        total         = len(self._incidents)
        critical_count = sum(1 for i in self._incidents if i.severity == "critical")
        high_count     = sum(1 for i in self._incidents if i.severity == "high")
        security_count = sum(1 for i in self._incidents if i.incident_type == "security")

        # --- breakdown by type ---
        type_counts = {}
        for inc in self._incidents:
            t = inc.incident_type or "general"
            type_counts[t] = type_counts.get(t, 0) + 1

        # --- breakdown by severity ---
        sev_counts = {}
        for inc in self._incidents:
            s = inc.severity or "low"
            sev_counts[s] = sev_counts.get(s, 0) + 1

        # --- breakdown by team ---
        team_counts = {}
        for inc in self._incidents:
            team_counts[inc.assigned_team] = team_counts.get(inc.assigned_team, 0) + 1

        # --- sorted incidents (critical first) ---
        sorted_incidents = sorted(self._incidents)

        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>IT Incident Auto-Triage Report</title>
  <style>
    *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      font-family: 'Segoe UI', Arial, sans-serif;
      background: #f0f2f5;
      color: #222;
      font-size: 13px;
    }}
    header {{
      background: #1a2332;
      color: #fff;
      padding: 16px 28px;
      display: flex;
      align-items: center;
      gap: 12px;
    }}
    header h1 {{ font-size: 18px; font-weight: 600; }}
    header span {{ font-size: 12px; color: #8fa3c0; margin-left: auto; }}
    .container {{ max-width: 1200px; margin: 24px auto; padding: 0 20px; }}

    /* Summary cards */
    .summary {{
      display: flex;
      gap: 16px;
      margin-bottom: 24px;
      flex-wrap: wrap;
    }}
    .card {{
      background: #fff;
      border-radius: 8px;
      padding: 18px 24px;
      box-shadow: 0 1px 4px rgba(0,0,0,.08);
      min-width: 120px;
      text-align: center;
    }}
    .card .num {{ font-size: 32px; font-weight: 700; color: #1a2332; line-height: 1; }}
    .card .lbl {{ font-size: 11px; color: #6b7a8d; margin-top: 4px; text-transform: uppercase; letter-spacing: .5px; }}

    /* Breakdown panels */
    .panels {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
      gap: 16px;
      margin-bottom: 24px;
    }}
    .panel {{
      background: #fff;
      border-radius: 8px;
      padding: 16px 20px;
      box-shadow: 0 1px 4px rgba(0,0,0,.08);
    }}
    .panel h3 {{ font-size: 12px; text-transform: uppercase; letter-spacing: .6px; color: #6b7a8d; margin-bottom: 12px; }}
    .tag {{
      display: inline-block;
      padding: 3px 10px;
      border-radius: 12px;
      font-size: 11px;
      font-weight: 600;
      margin: 3px;
      background: #e8edf5;
      color: #1a2332;
    }}

    /* Table */
    .table-wrap {{
      background: #fff;
      border-radius: 8px;
      box-shadow: 0 1px 4px rgba(0,0,0,.08);
      overflow-x: auto;
    }}
    .table-wrap h3 {{
      padding: 14px 20px;
      font-size: 13px;
      border-bottom: 1px solid #eaedf2;
      color: #1a2332;
    }}
    table {{ width: 100%; border-collapse: collapse; }}
    th {{
      background: #1a2332;
      color: #c8d6e8;
      font-size: 11px;
      text-transform: uppercase;
      letter-spacing: .5px;
      padding: 10px 14px;
      text-align: left;
      position: sticky;
      top: 0;
    }}
    td {{ padding: 9px 14px; border-bottom: 1px solid #f0f2f5; vertical-align: middle; }}
    tr:last-child td {{ border-bottom: none; }}
    tr:hover td {{ background: #f7f9fc; }}

    /* Severity badge */
    .badge {{
      display: inline-block;
      padding: 2px 9px;
      border-radius: 10px;
      font-size: 10px;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: .4px;
    }}
    .ticket-id {{
      font-size: 10px;
      font-family: monospace;
      color: #2980b9;
      display: block;
      white-space: nowrap;
    }}
    footer {{
      text-align: center;
      padding: 20px;
      color: #aaa;
      font-size: 11px;
    }}
  </style>
</head>
<body>
<header>
  <div>🖥</div>
  <div>
    <h1>IT Incident Auto-Triage Report</h1>
    <div style="font-size:11px;color:#8fa3c0;">Total Incidents: {total} &nbsp;</div>
  </div>
</header>

<div class="container">
  <!-- Summary cards -->
  <div class="summary">
    <div class="card"><div class="num">{total}</div><div class="lbl">Total Incidents</div></div>
    <div class="card"><div class="num" style="color:#c0392b">{critical_count}</div><div class="lbl">Critical</div></div>
    <div class="card"><div class="num" style="color:#e67e22">{high_count}</div><div class="lbl">High</div></div>
    <div class="card"><div class="num" style="color:#8e44ad">{security_count}</div><div class="lbl">Security Threats</div></div>
  </div>

  <!-- Breakdown panels -->
  <div class="panels">
    <div class="panel">
      <h3>Breakdown by Type</h3>
      {''.join(f'<span class="tag">{_TYPE_ICONS.get(t,"📋")} {t.capitalize()} {c}</span>' for t, c in sorted(type_counts.items()))}
    </div>
    <div class="panel">
      <h3>Breakdown by Severity</h3>
      {''.join(f'<span class="badge" style="background:{_SEVERITY_COLOURS.get(s,("#aaa","#fff"))[0]};color:{_SEVERITY_COLOURS.get(s,("#aaa","#fff"))[1]};margin:3px">{s.upper()} {c}</span>' for s, c in sorted(sev_counts.items(), key=lambda x: _SEVERITY_COLOURS.get(x[0], ("z",""))[0]))}
    </div>
    <div class="panel">
      <h3>Breakdown by Team</h3>
      {''.join(f'<span class="tag">👥 {team} — {cnt}</span>' for team, cnt in sorted(team_counts.items()))}
    </div>
  </div>

  <!-- Incident table -->
  <div class="table-wrap">
    <h3>Incident Detail</h3>
    <table>
      <thead>
        <tr>
          <th>ID</th>
          <th>Title</th>
          <th>Severity</th>
          <th>Type</th>
          <th>Team</th>
          <th>Timestamp</th>
          <th>Tickets</th>
        </tr>
      </thead>
      <tbody>
        {self._build_table_rows(sorted_incidents)}
      </tbody>
    </table>
  </div>
</div>

<footer>Produced by Incident Tracker — Mini Project 3</footer>
</body>
</html>"""

        with open(output_path, "w", encoding="utf-8") as fh:
            fh.write(html)

        print(f"[ReportGenerator] HTML report written → {output_path}")
        return output_path

    def _build_table_rows(self, incidents) -> str:
        rows = []
        for inc in incidents:
            sev   = inc.severity or "low"
            bg, fg = _SEVERITY_COLOURS.get(sev, ("#aaa", "#fff"))
            icon  = _TYPE_ICONS.get(inc.incident_type or "general", "📋")
            tids  = inc.ticket_ids or {}
            tickets_html = "".join(
                f'<span class="ticket-id">{k.upper()}: {v}</span>'
                for k, v in tids.items()
            ) or '<span style="color:#aaa">—</span>'

            rows.append(f"""
        <tr>
          <td><b>{inc.id}</b></td>
          <td>{icon} {inc.title}</td>
          <td><span class="badge" style="background:{bg};color:{fg}">{sev.upper()}</span></td>
          <td>{(inc.incident_type or "general").capitalize()}</td>
          <td>{inc.assigned_team}</td>
          <td style="white-space:nowrap">{inc.timestamp.strftime('%Y-%m-%d %H:%M')}</td>
          <td>{tickets_html}</td>
        </tr>""")
        return "\n".join(rows)

    # ------------------------------------------------------------------
    # JSON summary
    # ------------------------------------------------------------------
    def export_json(self, output_path: str = "output/summary.json") -> str:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        summary = {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "total": len(self._incidents),
            "incidents": [inc.to_dict() for inc in self._incidents],
        }
        with open(output_path, "w", encoding="utf-8") as fh:
            json.dump(summary, fh, indent=2, default=str)
        print(f"[ReportGenerator] JSON summary written → {output_path}")
        return output_path

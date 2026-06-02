"""Multi-format calendar export."""

from __future__ import annotations

import csv
import json
import os
from datetime import date, datetime
from io import StringIO
from typing import Optional

from content_calendar.models import ContentCalendar

try:
    from icalendar import Calendar, Event

    HAS_ICAL = True
except ImportError:
    HAS_ICAL = False

try:
    from jinja2 import Template

    HAS_JINJA = True

    HTML_TEMPLATE = Template("""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ calendar.name }} — Content Calendar</title>
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 2rem; }
        h1 { color: #333; }
        table { border-collapse: collapse; width: 100%; margin-top: 1rem; }
        th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
        th { background: #f5f5f5; }
        tr:nth-child(even) { background: #f9f9f9; }
        .status-scheduled { color: #2196F3; }
        .status-published { color: #4CAF50; }
        .status-draft { color: #FF9800; }
        .badge { display: inline-block; padding: 2px 6px; border-radius: 4px; font-size: 0.85em; }
    </style>
</head>
<body>
    <h1>{{ calendar.name }}</h1>
    <p>Generated: {{ generated_at }}</p>
    <p>Total items: {{ calendar.items|length }}</p>
    <table>
        <thead>
            <tr>
                <th>Date</th>
                <th>Title</th>
                <th>Type</th>
                <th>Platform</th>
                <th>Status</th>
            </tr>
        </thead>
        <tbody>
        {% for item in calendar.items %}
            <tr>
                <td>{{ item.scheduled_date or '—' }}</td>
                <td>{{ item.title }}</td>
                <td>{{ item.content_type.value }}</td>
                <td>{{ item.platform.value }}</td>
                <td><span class="badge status-{{ item.status.value }}">{{ item.status.value }}</span></td>
            </tr>
        {% endfor %}
        </tbody>
    </table>
</body>
</html>""")
except ImportError:
    HAS_JINJA = False
    HTML_TEMPLATE = None


class Exporter:
    """Export content calendars in various formats."""

    SUPPORTED_FORMATS = ["csv", "json", "markdown", "icalendar", "html"]

    def __init__(self, calendar: ContentCalendar) -> None:
        self.calendar = calendar

    def export(self, fmt: str, output_path: Optional[str] = None) -> str:
        """Export calendar in the specified format."""
        exporters = {
            "csv": self._export_csv,
            "json": self._export_json,
            "markdown": self._export_markdown,
            "icalendar": self._export_ical,
            "html": self._export_html,
        }

        if fmt not in exporters:
            msg = f"Unsupported format: {fmt!r}. Choose from: {', '.join(self.SUPPORTED_FORMATS)}"
            raise ValueError(msg)

        content = exporters[fmt]()

        if output_path:
            os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
            with open(output_path, "w") as f:
                f.write(content)

        return content

    def _export_csv(self) -> str:
        """Export as CSV."""
        output = StringIO()
        writer = csv.writer(output)
        writer.writerow(["ID", "Title", "Type", "Platform", "Status", "Date", "Time", "Tags", "Author"])

        for item in self.calendar.items:
            writer.writerow(
                [
                    item.id,
                    item.title,
                    item.content_type.value,
                    item.platform.value,
                    item.status.value,
                    item.scheduled_date.isoformat() if item.scheduled_date else "",
                    item.scheduled_time or "",
                    ", ".join(item.tags),
                    item.author or "",
                ]
            )

        return output.getvalue()

    def _export_json(self) -> str:
        """Export as JSON."""
        return json.dumps(self.calendar.to_dict(), indent=2, default=str)

    def _export_markdown(self) -> str:
        """Export as Markdown."""
        lines = [
            f"# {self.calendar.name}",
            "",
            f"_Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}_",
            "",
            f"Total items: **{len(self.calendar.items)}**",
            "",
            "## Content Schedule",
            "",
            "| Date | Title | Type | Platform | Status |",
            "|------|-------|------|----------|--------|",
        ]

        for item in self.calendar.items:
            date_str = item.scheduled_date.isoformat() if item.scheduled_date else "—"
            lines.append(
                f"| {date_str} | {item.title} | {item.content_type.value} "
                f"| {item.platform.value} | {item.status.value} |"
            )

        lines.extend(["", "---", "", "*Exported from Content Calendar*"])
        return "\n".join(lines)

    def _export_ical(self) -> str:
        """Export as iCalendar."""
        if not HAS_ICAL:
            msg = "icalendar package is required. Install with: pip install content-calendar[export] or pip install icalendar"
            raise ImportError(msg)

        cal = Calendar()
        cal.add("prodid", "-//Content Calendar//content-calendar//")
        cal.add("version", "2.0")
        cal.add("x-wr-calname", self.calendar.name)

        for item in self.calendar.items:
            if not item.scheduled_date:
                continue

            event = Event()
            event.add("uid", item.id)
            event.add("summary", item.title)
            event.add("dtstart", item.scheduled_date)
            event.add("description", item.description or "")

            if item.scheduled_time:
                event.add("dtstart", item.scheduled_date)
                event.add("dtend", item.scheduled_date)

            cal.add_component(event)

        return cal.to_ical().decode("utf-8")

    def _export_html(self) -> str:
        """Export as HTML."""
        if not HAS_JINJA or HTML_TEMPLATE is None:
            msg = "jinja2 package is required. Install with: pip install content-calendar[export] or pip install jinja2"
            raise ImportError(msg)

        return HTML_TEMPLATE.render(
            calendar=self.calendar,
            generated_at=datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC"),
        )

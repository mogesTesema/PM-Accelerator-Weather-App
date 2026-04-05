"""
Data export engine — renders weather records into JSON, CSV, or PDF.
"""

import csv
import io
import json
import logging

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

logger = logging.getLogger(__name__)


def export_json(records: list[dict]) -> str:
    """Export weather records as a JSON string."""
    return json.dumps(records, indent=2, default=str)


def export_xml(records: list[dict]) -> str:
    """Export weather records as an XML string."""
    import xml.etree.ElementTree as ET

    root = ET.Element("WeatherRecords")
    for record in records:
        record_elem = ET.SubElement(root, "WeatherRecord")
        for key, value in record.items():
            child = ET.SubElement(record_elem, key)
            child.text = str(value) if value is not None else ""

    # Pretty print if possible, else return string
    import xml.dom.minidom

    xmlstr = xml.dom.minidom.parseString(ET.tostring(root)).toprettyxml(indent="  ")
    return xmlstr


def export_md(records: list[dict]) -> str:
    """Export weather records as a Markdown string (table format)."""
    if not records:
        return "# Weather Data Export\n\nNo records found."

    lines = ["# Weather Data Export\n"]

    # Extract headers
    headers = list(records[0].keys())

    # Create Markdown table header and separator
    lines.append("| " + " | ".join(headers) + " |")
    lines.append("|" + "|".join(["---"] * len(headers)) + "|")

    # Add rows
    for record in records:
        row = [str(record.get(h, "")) for h in headers]
        lines.append("| " + " | ".join(row) + " |")

    return "\n".join(lines)


def export_csv(records: list[dict]) -> str:
    """Export weather records as a CSV string."""
    if not records:
        return ""

    output = io.StringIO()
    fieldnames = records[0].keys()
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(records)
    return output.getvalue()


def export_pdf(records: list[dict]) -> bytes:
    """Export weather records as a PDF byte stream."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    elements = []

    # Title
    elements.append(Paragraph("Weather Data Export", styles["Title"]))
    elements.append(Spacer(1, 0.25 * inch))

    if not records:
        elements.append(Paragraph("No data to export.", styles["Normal"]))
        doc.build(elements)
        return buffer.getvalue()

    # Table header
    headers = list(records[0].keys())
    # Truncate to key fields for readability
    display_fields = [
        "location",
        "date",
        "temperature",
        "humidity",
        "wind_speed",
        "description",
    ]
    headers = [h for h in display_fields if h in headers] or headers[:6]

    table_data = [headers]
    for record in records:
        row = [str(record.get(h, "")) for h in headers]
        table_data.append(row)

    table = Table(table_data, repeatRows=1)
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2c3e50")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, 0), 9),
                ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
                ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#ecf0f1")),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("FONTSIZE", (0, 1), (-1, -1), 8),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ]
        )
    )

    elements.append(table)
    doc.build(elements)
    return buffer.getvalue()


def records_to_dicts(queryset) -> list[dict]:
    """Convert a WeatherRecord queryset to a list of flat dicts."""
    return list(stream_records_to_dicts(queryset))


def stream_records_to_dicts(queryset):
    """Generator that yields one flat dict at a time suitable for streaming."""
    for wr in queryset:
        yield {
            "location": wr.location.name,
            "latitude": wr.location.latitude,
            "longitude": wr.location.longitude,
            "date": wr.date.isoformat(),
            "temperature": wr.temperature,
            "feels_like": wr.feels_like,
            "humidity": wr.humidity,
            "wind_speed": wr.wind_speed,
            "description": wr.description,
        }


def stream_csv(records_generator):
    """Yields CSV rows."""

    class Echo:
        def write(self, value):
            return value

    try:
        first = next(records_generator)
    except StopIteration:
        return

    writer = csv.DictWriter(Echo(), fieldnames=first.keys())
    yield writer.writeheader()
    yield writer.writerow(first)

    for record in records_generator:
        yield writer.writerow(record)


def stream_json(records_generator):
    """Yields a JSON array incrementally."""
    yield "[\n"
    first = True
    for record in records_generator:
        if not first:
            yield ",\n"
        yield "  " + json.dumps(record, default=str)
        first = False
    yield "\n]"

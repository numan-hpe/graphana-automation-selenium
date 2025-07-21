from reportlab.lib.pagesizes import portrait, A4
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import (
    Table,
    TableStyle,
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    ListFlowable,
    Image,
    HRFlowable,
)
import os
from config import HEADINGS, REGION_DATA
import json

# def create_table(data, column_headers):
#     """Helper function to create a table from the given data."""
#     table_data = [column_headers]  # Add headers at the top
#     for entry in data:
#         row = [value for value in entry.values()]
#         table_data.append(row)
#     return table_data


# def prepare_table_data(cpu, memory, pod_counts):
#     output = []
#     SERVICES.sort()
#     for service in SERVICES:
#         svc_cpu = next((x for x in cpu if x["name"] == service), None)
#         svc_memory = next((x for x in memory if x["name"] == service), None)
#         svc_pod_count = next((x for x in pod_counts if x["name"] == service), None)
#         output.append(
#             {
#                 "name": service,
#                 "cpu": svc_cpu["value"],
#                 "memory": svc_memory["value"],
#                 "pod_count": f"{svc_pod_count['value']}  ({svc_pod_count['max']})",
#             }
#         )
#     # output.sort(key=lambda x: x["name"])
#     return output


def prepare_basic_data(data, styles, elements):
    # Add basic key-value data (sli, websockets, etc.)
    for key, header in HEADINGS.items():
        if key in data:
            text = data[key]
            elements.append(Paragraph(f"<b>{header}:</b> {text}", styles["Normal"]))
            elements.append(Spacer(0, 2))


def display_images_and_table(region, table, elements):
    styles = getSampleStyleSheet()
    styles["Normal"].textColor = colors.purple
    styles["Normal"].fontSize = 12
    width = 3.8 * inch
    height = width / 2
    elements.append(
        Image(f"{region}/websockets.png", width, height - 10, hAlign="LEFT")
    )
    elements.append(Spacer(0, -(height - 10)))
    elements.append(table)
    elements.append(Spacer(0, 8))
    elements.append(
        Paragraph(
            f"<b>CPU Utilization{'&nbsp;'*57}Memory Utilization</b>",
            style=styles["Normal"],
        )
    )
    elements.append(Spacer(0, height - 7))
    elements.append(
        Paragraph(
            f"""
            <img src='{region}/cpu.png' width='{width}' height='{height}' /> 
            <img src='{region}/memory.png' width='{width}' height='{height}' />
            """
        )
    )
    return


def generate_pdf(output_dir, output_file="service_monitoring.pdf"):
    """
    Generates a PDF report for the Grafana dashboard data.
    :param output_dir: Directory containing region subdirectories with JSON files.
    :param output_file: Name of the generated PDF file.
    """
    pdf_filename = os.path.join(output_dir, output_file)
    margin = 0.25 * inch
    doc = SimpleDocTemplate(
        pdf_filename,
        pagesize=portrait(A4),
        leftMargin=margin,
        topMargin=margin - 10,
        rightMargin=margin,
        bottomMargin=margin,
    )
    styles = getSampleStyleSheet()
    elements = []

    # Title
    title = Paragraph("<b>Service Monitoring Report</b>", styles["Title"])
    elements.append(title)

    # Process each region
    for region in REGION_DATA.keys():
        elements.append(
            HRFlowable(width="100%", color=colors.lightgrey, spaceBefore=10)
        )

        json_file = f"{region}/data.json"

        if os.path.isfile(json_file):
            with open(json_file, "r") as f:
                data = json.load(f)

            # Add region header
            region_title = Paragraph(f"<b>Region: {region}</b>", styles["Heading2"])
            elements.append(region_title)

            prepare_basic_data(data, styles, elements)

    # Build the PDF document
    doc.build(elements)
    print(f"PDF successfully generated: {pdf_filename}")

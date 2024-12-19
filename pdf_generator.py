from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Table, TableStyle, SimpleDocTemplate, Paragraph, Spacer
from reportlab.pdfgen import canvas
import os
import json


def create_table(data, column_headers):
    """ Helper function to create a table from the given data. """
    table_data = [column_headers]  # Add headers at the top
    for entry in data:
        row = [entry.get("name", "N/A"), entry.get("value", "N/A"), entry.get("max", "N/A")]
        table_data.append(row)
    return table_data


def draw_image(c, image_path, x, y, width, height):
    """ Helper function to draw an image on the canvas. """
    if os.path.exists(image_path):
        c.drawImage(image_path, x, y, width, height, preserveAspectRatio=True)


def generate_pdf(output_dir, output_file="grafana_dashboard_report.pdf"):
    """
    Generates a PDF report for the Grafana dashboard data.
    :param output_dir: Directory containing region subdirectories with JSON files.
    :param output_file: Name of the generated PDF file.
    """
    pdf_filename = os.path.join(output_dir, output_file)
    doc = SimpleDocTemplate(pdf_filename, pagesize=landscape(letter))
    styles = getSampleStyleSheet()
    elements = []

    # Title
    title = Paragraph("<b>Grafana Dashboard Report</b>", styles['Title'])
    elements.append(title)
    elements.append(Spacer(1, 12))

    # Process each region
    for region in os.listdir(output_dir):
        region_dir = os.path.join(output_dir, region)
        json_file = os.path.join(region_dir, "data.json")

        if os.path.isfile(json_file):
            with open(json_file, "r") as f:
                data = json.load(f)

            # Add region header
            region_title = Paragraph(f"<b>Region: {region}</b>", styles['Heading2'])
            elements.append(region_title)
            elements.append(Spacer(1, 12))

            # Add basic key-value data (sli, websockets, etc.)
            for key in ['sli', 'websockets', 'duration_over_500ms', 'duration_over_500ms_special', 'http_5x', 'pod_restarts']:
                if key in data and data[key]:
                    elements.append(Paragraph(f"<b>{key.replace('_', ' ').title()}:</b> {data[key]}", styles['BodyText']))
                    elements.append(Spacer(1, 6))

            # Pod counts table
            if "pod_counts" in data:
                elements.append(Paragraph("<b>Pod Counts</b>", styles['Heading3']))
                pod_counts_table = create_table(data["pod_counts"], ["Service", "Value", "Max"])
                table = Table(pod_counts_table)
                table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
                    ('FONTSIZE', (0, 0), (-1, -1), 10),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ]))
                elements.append(table)
                elements.append(Spacer(1, 12))

            # Add images and tables for memory usage
            if "memory" in data:
                elements.append(Spacer(1, 12))
                elements.append(Paragraph("<b>Memory Usage</b>", styles['Heading3']))
                memory_table = create_table(data["memory"], ["Service", "Value", "Max"])
                memory_table_data = Table(memory_table)
                memory_table_data.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.blue),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
                    ('FONTSIZE', (0, 0), (-1, -1), 10),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ]))
                elements.append(memory_table_data)

                # Draw memory image using canvas
                c = canvas.Canvas(pdf_filename, pagesize=landscape(letter))
                draw_image(c, os.path.join(region_dir, "memory.png"), 40, 350, 5*inch, 2.5*inch)
                c.showPage()

            # Add images and tables for CPU usage
            if "cpu" in data:
                elements.append(Spacer(1, 12))
                elements.append(Paragraph("<b>CPU Usage</b>", styles['Heading3']))
                cpu_table = create_table(data["cpu"], ["Service", "Value", "Max"])
                cpu_table_data = Table(cpu_table)
                cpu_table_data.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.green),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
                    ('FONTSIZE', (0, 0), (-1, -1), 10),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ]))
                elements.append(cpu_table_data)

                # Draw CPU image using canvas
                c = canvas.Canvas(pdf_filename, pagesize=landscape(letter))
                draw_image(c, os.path.join(region_dir, "cpu.png"), 40, 200, 5*inch, 2.5*inch)
                c.showPage()

            elements.append(Spacer(1, 12))
            elements.append(Paragraph("<hr />", styles['BodyText']))

    # Build the PDF document
    doc.build(elements)
    print(f"PDF successfully generated: {pdf_filename}")


# Run the function
output_dir = "./"  # Directory containing region subdirectories with JSON files
generate_pdf(output_dir)

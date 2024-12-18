from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet
import os


def generate_pdf(data, output_filename, screenshots=None):
    """
    Generates a PDF using ReportLab from the provided data.

    Args:
        data (dict): Dictionary containing report data.
        output_filename (str): Output PDF file name.
        screenshots (list): List of screenshot image file paths.
    """
    # Define document and styles
    doc = SimpleDocTemplate(output_filename, pagesize=A4)
    elements = []  # PDF elements
    styles = getSampleStyleSheet()
    title_style = styles["Title"]
    body_style = styles["BodyText"]
    space = Spacer(1, 12)

    # Title
    title = Paragraph("Service Report", title_style)
    elements.append(title)
    elements.append(space)

    # Add key-value pairs
    for key, value in data.items():
        if isinstance(value, list):  # Handle tables
            elements.append(Paragraph(f"<b>{key.replace('_', ' ').title()}</b>", body_style))
            table_data = [["Name", "Value", "Max"]] if "max" in str(value) else [["Name", "Value"]]
            for item in value:
                row = [item.get("name", ""), item.get("value", "")]
                if "max" in item:
                    row.append(item.get("max", ""))
                table_data.append(row)

            table = Table(table_data)
            table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("GRID", (0, 0), (-1, -1), 1, colors.black),
            ]))
            elements.append(table)
            elements.append(space)
        else:  # Handle single values
            elements.append(Paragraph(f"<b>{key.replace('_', ' ').title()}:</b> {value}", body_style))
            elements.append(space)

    # Add screenshots
    if screenshots:
        elements.append(Paragraph("<b>Screenshots</b>", title_style))
        elements.append(space)
        for image_path in screenshots:
            if os.path.exists(image_path):
                img = Image(image_path, width=400, height=200)
                elements.append(img)
                elements.append(space)
            else:
                elements.append(Paragraph(f"Image not found: {image_path}", body_style))

    # Generate PDF
    doc.build(elements)
    print(f"PDF successfully generated: {output_filename}")

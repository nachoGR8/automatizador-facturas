import io

from reportlab.pdfgen import canvas


def make_pdf(lines: list[str]) -> bytes:
    """PDF de una página con una línea de texto por elemento de `lines`."""
    buffer = io.BytesIO()
    pdf = canvas.Canvas(buffer)
    y = 800
    for line in lines:
        pdf.drawString(50, y, line)
        y -= 20
    pdf.save()
    return buffer.getvalue()

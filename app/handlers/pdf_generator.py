import io

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm as mm_unit
from reportlab.pdfgen import canvas

from app.services.fayda import FaydaProfile

# Standard ID-1 card size (like a bank card): 85.6mm x 53.98mm
CARD_WIDTH = 85.6 * mm_unit
CARD_HEIGHT = 53.98 * mm_unit


def _draw_card(c: canvas.Canvas, profile: FaydaProfile, x: float, y: float) -> None:
    c.setFont("Helvetica-Bold", 8)
    c.drawString(x + 4 * mm_unit, y + CARD_HEIGHT - 8 * mm_unit, "FAYDA - Ethiopian National ID")

    c.setFont("Helvetica", 7)
    c.drawString(x + 4 * mm_unit, y + CARD_HEIGHT - 16 * mm_unit, f"Name: {profile.full_name}")
    c.drawString(x + 4 * mm_unit, y + CARD_HEIGHT - 22 * mm_unit, f"DOB: {profile.date_of_birth}")
    c.drawString(x + 4 * mm_unit, y + CARD_HEIGHT - 28 * mm_unit, f"FAN: {profile.fan}")
    c.rect(x, y, CARD_WIDTH, CARD_HEIGHT)


def build_card_pdf(profile: FaydaProfile) -> bytes:
    """Single card, sized exactly to the card - used for the digital PDF download."""
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=(CARD_WIDTH, CARD_HEIGHT))
    _draw_card(c, profile, 0, 0)
    c.showPage()
    c.save()
    return buffer.getvalue()


def build_print_sheet_pdf(profile: FaydaProfile) -> bytes:
    """A4 sheet with front/back card layout, ready to send to a printer."""
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    page_width, page_height = A4
    x = (page_width - CARD_WIDTH) / 2
    y = page_height - 40 * mm_unit - CARD_HEIGHT

    c.setFont("Helvetica", 9)
    c.drawString(x, page_height - 20 * mm_unit, "Cut along the border below:")
    _draw_card(c, profile, x, y)

    c.showPage()
    c.save()
    return buffer.getvalue()

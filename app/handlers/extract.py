import io
import re

from PIL import Image
from PyPDF2 import PdfReader

from app.services.fayda import FaydaProfile

_NAME_RE = re.compile(r"Name:\s*(.+)")
_DOB_RE = re.compile(r"DOB:\s*(.+)")
_FAN_RE = re.compile(r"FAN:\s*([\d\- ]+)")


def _parse_fields(text: str) -> FaydaProfile:
    name_match = _NAME_RE.search(text)
    dob_match = _DOB_RE.search(text)
    fan_match = _FAN_RE.search(text)

    return FaydaProfile(
        fan=fan_match.group(1).strip() if fan_match else "UNKNOWN",
        full_name=name_match.group(1).strip() if name_match else "UNKNOWN",
        date_of_birth=dob_match.group(1).strip() if dob_match else "UNKNOWN",
        photo_url=None,
    )


def extract_from_pdf(pdf_bytes: bytes) -> FaydaProfile:
    reader = PdfReader(io.BytesIO(pdf_bytes))
    text = "\n".join(page.extract_text() or "" for page in reader.pages)
    return _parse_fields(text)


def extract_from_image(image_bytes: bytes) -> FaydaProfile:
    import pytesseract

    image = Image.open(io.BytesIO(image_bytes))
    text = pytesseract.image_to_string(image)
    return _parse_fields(text)

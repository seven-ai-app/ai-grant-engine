"""Generate Hebrew RTL Word document for grant application."""

import logging
from pathlib import Path
from docx import Document
from docx.shared import Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn

from ..graph.state import GrantState
from ..tools.hebrew_utils import SECTION_HEADERS_HE, format_currency

logger = logging.getLogger(__name__)


def generate_application_docx(state: GrantState, output_dir: Path) -> Path:
    """Generate the full grant application as a Hebrew RTL Word document."""
    doc = Document()

    # Set RTL for the entire document
    _set_document_rtl(doc)

    # Title page
    _add_title_page(doc, state)

    # Table of contents placeholder
    doc.add_page_break()
    _add_heading(doc, "תוכן עניינים", level=1)
    for section in state.get("sections", []):
        _add_paragraph(doc, f"• {section['title_he']}", size=11)

    # Application sections
    doc.add_page_break()
    for section in state.get("sections", []):
        _add_heading(doc, section["title_he"], level=1)
        _add_paragraph(doc, section["content_he"], size=11)
        doc.add_paragraph()  # spacing

    # Budget summary section
    if state.get("budget_lines"):
        doc.add_page_break()
        _add_heading(doc, "סיכום תקציבי", level=1)
        _add_budget_table(doc, state)

    # Save
    filename = f"בקשת_מענק_{state['startup_name'].replace(' ', '_')}.docx"
    output_path = output_dir / filename
    doc.save(str(output_path))
    logger.info(f"Generated DOCX: {output_path}")
    return output_path


def _set_document_rtl(doc: Document):
    """Set document-level RTL direction."""
    for section in doc.sections:
        section.left_margin = Cm(2)
        section.right_margin = Cm(2.5)
        section.top_margin = Cm(2)
        section.bottom_margin = Cm(2)


def _add_title_page(doc: Document, state: GrantState):
    """Add a title page to the document."""
    doc.add_paragraph()
    doc.add_paragraph()

    title = _add_paragraph(doc, "בקשה לתמיכה במסלול תנופה", size=22, bold=True)
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER

    doc.add_paragraph()
    subtitle = _add_paragraph(doc, "רשות החדשנות הישראלית", size=16)
    subtitle.alignment = WD_ALIGN_PARAGRAPH.CENTER

    doc.add_paragraph()
    doc.add_paragraph()

    _add_paragraph(doc, f"שם המיזם: {state['startup_name']}", size=14, bold=True)
    _add_paragraph(doc, f"תיאור: {state['startup_description'][:200]}", size=12)

    if state.get("total_budget"):
        _add_paragraph(doc, f"תקציב מבוקש: {format_currency(state['total_budget'])}", size=12)
        _add_paragraph(doc, f"מענק מבוקש: {format_currency(state['grant_amount'])}", size=12)

    doc.add_paragraph()
    entity_he = "יזם פרטי" if state.get("entity_type") == "private_entrepreneur" else "חברה חדשה"
    _add_paragraph(doc, f"סוג מגיש: {entity_he}", size=11)


def _add_heading(doc: Document, text: str, level: int = 1):
    """Add an RTL heading."""
    heading = doc.add_heading(text, level=level)
    # Set RTL for heading
    pPr = heading._element.get_or_add_pPr()
    bidi = pPr.makeelement(qn("w:bidi"), {})
    pPr.append(bidi)
    heading.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    return heading


def _add_paragraph(
    doc: Document, text: str, size: int = 11, bold: bool = False
):
    """Add an RTL paragraph with specified formatting."""
    para = doc.add_paragraph()
    run = para.add_run(text)
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.name = "David"

    # Set RTL
    pPr = para._element.get_or_add_pPr()
    bidi = pPr.makeelement(qn("w:bidi"), {})
    pPr.append(bidi)
    para.alignment = WD_ALIGN_PARAGRAPH.RIGHT

    return para


def _add_budget_table(doc: Document, state: GrantState):
    """Add a budget summary table."""
    budget_lines = state.get("budget_lines", [])
    if not budget_lines:
        return

    # Create table
    table = doc.add_table(rows=1, cols=4)
    table.style = "Table Grid"

    # Headers
    headers = ["תיאור", "קטגוריה", "סכום (ש\"ח)", "נימוק"]
    for i, header in enumerate(headers):
        cell = table.rows[0].cells[i]
        cell.text = header
        run = cell.paragraphs[0].runs[0] if cell.paragraphs[0].runs else cell.paragraphs[0].add_run(header)
        run.bold = True

    # Data rows
    for line in budget_lines:
        row = table.add_row()
        row.cells[0].text = line.get("description_he", "")
        row.cells[1].text = line.get("category", "")
        row.cells[2].text = f"{line.get('amount', 0):,.0f}"
        row.cells[3].text = line.get("justification_he", "")[:50]

    # Total row
    total_row = table.add_row()
    total_row.cells[0].text = "סה\"כ"
    total_row.cells[2].text = f"{state.get('total_budget', 0):,.0f}"
    for cell in total_row.cells:
        for paragraph in cell.paragraphs:
            for run in paragraph.runs:
                run.bold = True

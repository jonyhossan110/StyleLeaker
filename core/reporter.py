"""
StyleLeaker — Professional PDF Report Generator
Author: Md. Jony Hassain | HexaCyberLab
Replace core/reporter.py with this upgraded version.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
import html
from typing import Any, Dict, List, Optional

REPORTLAB_AVAILABLE = True
try:
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import mm
    from reportlab.platypus import (
        HRFlowable,
        PageBreak,
        Paragraph,
        SimpleDocTemplate,
        Spacer,
        Table,
        TableStyle,
    )
except ImportError:
    REPORTLAB_AVAILABLE = False
    colors = None  # type: ignore
    TA_CENTER = TA_LEFT = TA_RIGHT = None
    A4 = None
    ParagraphStyle = lambda *args, **kwargs: None  # type: ignore
    getSampleStyleSheet = lambda: {}  # type: ignore
    mm = 1  # type: ignore
    HRFlowable = PageBreak = Paragraph = SimpleDocTemplate = Spacer = Table = TableStyle = object  # type: ignore

# ── Brand Colors ──────────────────────────────────────────────────────────────
if REPORTLAB_AVAILABLE:
    C_BG = colors.HexColor("#0D0D0D")
    C_ACCENT = colors.HexColor("#00FF88")   # neon green
    C_ACCENT2 = colors.HexColor("#00BFFF")   # cyber blue
    C_DANGER = colors.HexColor("#FF4444")   # red
    C_WARNING = colors.HexColor("#FFB700")   # amber
    C_HEADER_BG = colors.HexColor("#111827")
    C_ROW_ALT = colors.HexColor("#1A2333")
    C_ROW_MAIN = colors.HexColor("#0F172A")
    C_TEXT = colors.HexColor("#E2E8F0")
    C_MUTED = colors.HexColor("#64748B")
    C_WHITE = colors.white
    C_DARK = colors.HexColor("#020617")
else:
    C_BG = C_ACCENT = C_ACCENT2 = C_DANGER = C_WARNING = None
    C_HEADER_BG = C_ROW_ALT = C_ROW_MAIN = C_TEXT = C_MUTED = C_WHITE = C_DARK = None


def _styles() -> Dict[str, ParagraphStyle]:
    base = getSampleStyleSheet()
    s: Dict[str, ParagraphStyle] = {}

    s["cover_title"] = ParagraphStyle(
        "cover_title",
        fontName="Helvetica-Bold",
        fontSize=32,
        textColor=C_ACCENT,
        alignment=TA_CENTER,
        spaceAfter=4,
        leading=38,
    )
    s["cover_sub"] = ParagraphStyle(
        "cover_sub",
        fontName="Helvetica",
        fontSize=13,
        textColor=C_ACCENT2,
        alignment=TA_CENTER,
        spaceAfter=2,
    )
    s["cover_meta"] = ParagraphStyle(
        "cover_meta",
        fontName="Helvetica",
        fontSize=9,
        textColor=C_MUTED,
        alignment=TA_CENTER,
        spaceAfter=2,
    )
    s["section_title"] = ParagraphStyle(
        "section_title",
        fontName="Helvetica-Bold",
        fontSize=14,
        textColor=C_ACCENT,
        spaceBefore=12,
        spaceAfter=6,
        leading=18,
    )
    s["body"] = ParagraphStyle(
        "body",
        fontName="Helvetica",
        fontSize=9,
        textColor=C_TEXT,
        spaceAfter=3,
        leading=14,
    )
    s["body_mono"] = ParagraphStyle(
        "body_mono",
        fontName="Courier",
        fontSize=8,
        textColor=C_ACCENT2,
        spaceAfter=2,
        leading=12,
    )
    s["finding_high"] = ParagraphStyle(
        "finding_high",
        fontName="Helvetica-Bold",
        fontSize=9,
        textColor=C_DANGER,
        spaceAfter=2,
        leading=13,
    )
    s["finding_med"] = ParagraphStyle(
        "finding_med",
        fontName="Helvetica-Bold",
        fontSize=9,
        textColor=C_WARNING,
        spaceAfter=2,
        leading=13,
    )
    s["label"] = ParagraphStyle(
        "label",
        fontName="Helvetica-Bold",
        fontSize=9,
        textColor=C_ACCENT2,
        spaceAfter=1,
    )
    s["toc_item"] = ParagraphStyle(
        "toc_item",
        fontName="Helvetica",
        fontSize=10,
        textColor=C_TEXT,
        spaceAfter=4,
        leftIndent=10,
    )
    return s


def _escape_for_paragraph(value: Any) -> str:
    return html.escape(str(value if value is not None else ""), quote=True).replace("\n", "<br/>")


# ── Page Templates ─────────────────────────────────────────────────────────────

def _on_first_page(canvas, doc):
    """Dark full-bleed cover page background."""
    canvas.saveState()
    canvas.setFillColor(C_DARK)
    canvas.rect(0, 0, A4[0], A4[1], fill=1, stroke=0)

    # Decorative top bar
    canvas.setFillColor(C_ACCENT)
    canvas.rect(0, A4[1] - 8 * mm, A4[0], 3 * mm, fill=1, stroke=0)

    # Decorative bottom bar
    canvas.setFillColor(C_ACCENT2)
    canvas.rect(0, 0, A4[0], 2 * mm, fill=1, stroke=0)

    # Watermark diagonal text
    canvas.setFont("Helvetica-Bold", 60)
    canvas.setFillColor(colors.HexColor("#0A1628"))
    canvas.saveState()
    canvas.translate(A4[0] / 2, A4[1] / 2)
    canvas.rotate(30)
    canvas.drawCentredString(0, 0, "CONFIDENTIAL")
    canvas.restoreState()

    canvas.restoreState()


def _on_later_pages(canvas, doc):
    """Dark background + header/footer on every non-cover page."""
    canvas.saveState()
    canvas.setFillColor(C_DARK)
    canvas.rect(0, 0, A4[0], A4[1], fill=1, stroke=0)

    # Top accent line
    canvas.setFillColor(C_ACCENT)
    canvas.rect(0, A4[1] - 4 * mm, A4[0], 1.5 * mm, fill=1, stroke=0)

    # Header text
    canvas.setFont("Helvetica-Bold", 8)
    canvas.setFillColor(C_ACCENT)
    canvas.drawString(15 * mm, A4[1] - 10 * mm, "StyleLeaker")
    canvas.setFillColor(C_MUTED)
    canvas.setFont("Helvetica", 7)
    canvas.drawRightString(A4[0] - 15 * mm, A4[1] - 10 * mm, "HexaCyberLab | Confidential")

    # Bottom footer
    canvas.setFillColor(C_MUTED)
    canvas.setFont("Helvetica", 7)
    canvas.drawString(15 * mm, 8 * mm, "github.com/jonyhossan110")
    canvas.drawCentredString(A4[0] / 2, 8 * mm, f"Page {doc.page - 1}")
    canvas.drawRightString(A4[0] - 15 * mm, 8 * mm, "Web Security Assessment Report")

    # Bottom accent line
    canvas.setFillColor(C_ACCENT2)
    canvas.rect(0, 4 * mm, A4[0], 1.2 * mm, fill=1, stroke=0)

    canvas.restoreState()


# ── Table helpers ──────────────────────────────────────────────────────────────

def _dark_table(data: List[List[Any]], col_widths: List[float]) -> Table:
    tbl = Table(data, colWidths=col_widths, repeatRows=1)
    tbl.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, 0),  C_HEADER_BG),
        ("TEXTCOLOR",     (0, 0), (-1, 0),  C_ACCENT),
        ("FONTNAME",      (0, 0), (-1, 0),  "Helvetica-Bold"),
        ("FONTSIZE",      (0, 0), (-1, 0),  9),
        ("ALIGN",         (0, 0), (-1, -1), "LEFT"),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
        ("ROWBACKGROUNDS",(0, 1), (-1, -1), [C_ROW_MAIN, C_ROW_ALT]),
        ("TEXTCOLOR",     (0, 1), (-1, -1), C_TEXT),
        ("FONTNAME",      (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE",      (0, 1), (-1, -1), 8),
        ("GRID",          (0, 0), (-1, -1), 0.3, C_MUTED),
        ("TOPPADDING",    (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING",   (0, 0), (-1, -1), 8),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 8),
    ]))
    return tbl


def _severity_badge(text: str, high: bool = True) -> Paragraph:
    color = "#FF4444" if high else "#FFB700"
    label = "HIGH" if high else "MEDIUM"
    safe_text = _escape_for_paragraph(text)
    html = (
        f'<font color="{color}"><b>[{label}]</b></font> '
        f'<font color="#E2E8F0">{safe_text}</font>'
    )
    return Paragraph(html, ParagraphStyle(
        "badge",
        fontName="Helvetica",
        fontSize=8.5,
        textColor=C_TEXT,
        spaceAfter=3,
        leading=13,
    ))


def _hr(color=C_ACCENT, thickness=0.8):
    return HRFlowable(
        width="100%",
        thickness=thickness,
        color=color,
        spaceAfter=6,
        spaceBefore=4,
    )


# ── Cover Page ─────────────────────────────────────────────────────────────────

def _build_cover(story: List, target_url: str, timestamp: str, s: Dict) -> None:
    story.append(Spacer(1, 40 * mm))
    story.append(Paragraph("StyleLeaker", s["cover_title"]))
    story.append(Paragraph("HTML &amp; CSS Security Assessment Report", s["cover_sub"]))
    story.append(Spacer(1, 8 * mm))
    story.append(_hr(C_ACCENT, 1.5))
    story.append(Spacer(1, 6 * mm))

    story.append(Paragraph(f"Target: <b>{target_url}</b>", ParagraphStyle(
        "t", fontName="Helvetica", fontSize=11, textColor=C_ACCENT2,
        alignment=TA_CENTER, spaceAfter=4)))
    story.append(Paragraph(f"Scanned: {timestamp}", s["cover_meta"]))
    story.append(Paragraph("Classification: CONFIDENTIAL", ParagraphStyle(
        "c", fontName="Helvetica-Bold", fontSize=9, textColor=C_DANGER,
        alignment=TA_CENTER, spaceAfter=2)))

    story.append(Spacer(1, 20 * mm))
    story.append(_hr(C_ACCENT2, 0.8))
    story.append(Spacer(1, 6 * mm))
    story.append(Paragraph("Prepared by: Md. Jony Hassain", s["cover_meta"]))
    story.append(Paragraph("HexaCyberLab | Web Cybersecurity Expert", s["cover_meta"]))
    story.append(Paragraph("github.com/jonyhossan110", s["cover_meta"]))
    story.append(PageBreak())


def _build_header_analysis(story: List, recon_data: Dict[str, Any], s: Dict[str, Any]) -> None:
    story.append(Paragraph("0. HTTP Security Headers Analysis", s["section_title"]))
    story.append(_hr())
    if not recon_data or not recon_data.get('headers'):
        story.append(Paragraph('Reconnaissance data unavailable or skipped.', s['body']))
        story.append(PageBreak())
        return

    rows = [["Header", "Value", "Status"]]
    findings = recon_data.get('headers', {}).get('findings', {})
    for header, details in findings.items():
        rows.append([header, details.get('value', 'MISSING'), details.get('status', 'MISSING')])

    tbl = _dark_table(rows, [60 * mm, 80 * mm, 30 * mm])
    story.append(tbl)
    story.append(PageBreak())


def _build_severity_dashboard(story: List, severity_data: Dict[str, Any], s: Dict[str, Any]) -> None:
    story.append(Paragraph("1.5 Severity Score Dashboard", s["section_title"]))
    story.append(_hr())
    if not severity_data:
        story.append(Paragraph('Severity scoring data unavailable.', s['body']))
        story.append(Spacer(1, 5 * mm))
        return

    story.append(Paragraph(f"Overall Score: <b>{severity_data.get('overall_score', 0)}</b>", s['body']))
    story.append(Paragraph(f"Risk Level: <b>{severity_data.get('risk_level', 'INFO')}</b>", s['body']))
    story.append(Spacer(1, 4 * mm))

    rows = [["Finding", "Severity", "Count"]]
    for item in severity_data.get('findings_list', []):
        rows.append([item.get('finding', ''), item.get('severity', ''), str(item.get('count', 0))])

    if len(rows) > 1:
        tbl = _dark_table(rows, [90 * mm, 40 * mm, 40 * mm])
        story.append(tbl)
    else:
        story.append(Paragraph('No severity findings to display.', s['body']))
    story.append(Spacer(1, 5 * mm))


def _build_robots_paths(story: List, recon_data: Dict[str, Any], s: Dict[str, Any]) -> None:
    story.append(Paragraph("3.5 robots.txt Disallowed Paths", s["section_title"]))
    story.append(_hr())
    if not recon_data or not recon_data.get('robots'):
        story.append(Paragraph('No robots.txt data available.', s['body']))
        story.append(Spacer(1, 5 * mm))
        return

    paths = recon_data.get('robots', {}).get('disallowed_paths', [])
    if not paths:
        story.append(Paragraph('No disallowed paths were found in robots.txt.', s['body']))
    else:
        rows = [["Disallowed Path"]]
        for path in paths:
            rows.append([path])
        tbl = _dark_table(rows, [170 * mm])
        story.append(tbl)
    story.append(Spacer(1, 5 * mm))


def _build_response_headers(story: List, recon_data: Dict[str, Any], s: Dict[str, Any]) -> None:
    story.append(Paragraph("3.6 HTTP Response Headers", s["section_title"]))
    story.append(_hr())
    if not recon_data or not recon_data.get('headers'):
        story.append(Paragraph('No HTTP header data available.', s['body']))
        story.append(Spacer(1, 5 * mm))
        return

    raw_headers = recon_data.get('headers', {}).get('raw_headers', {})
    if not raw_headers:
        story.append(Paragraph('No raw headers were captured.', s['body']))
        story.append(Spacer(1, 5 * mm))
        return

    rows = [["Header", "Value"]]
    for header, value in sorted(raw_headers.items()):
        rows.append([header, str(value)])
    tbl = _dark_table(rows, [60 * mm, 110 * mm])
    story.append(tbl)
    story.append(Spacer(1, 5 * mm))


# ── TOC Page ───────────────────────────────────────────────────────────────────

def _build_toc(story: List, s: Dict) -> None:
    story.append(Paragraph("Table of Contents", s["section_title"]))
    story.append(_hr())
    toc_items = [
        "0.  HTTP Security Headers Analysis",
        "1.  Executive Summary",
        "1.5 Severity Score Dashboard",
        "2.  Scan Statistics",
        "3.  Framework & Technology Fingerprinting",
        "3.5 robots.txt Disallowed Paths",
        "3.6 HTTP Response Headers",
        "4.  Sensitive Pattern Analysis",
        "5.  Hidden Form Fields (Critical Findings)",
        "6.  Developer Comments & Notes",
        "7.  IP Addresses & Internal URLs",
        "8.  CSS Variables",
        "9.  Media Query Breakpoints",
        "10. HTML Comments",
        "11. CSS Comments",
        "12. Disclaimer & Legal Notice",
    ]
    for item in toc_items:
        story.append(Paragraph(item, s["toc_item"]))
        story.append(Spacer(1, 1))
    story.append(PageBreak())


# ── Executive Summary ──────────────────────────────────────────────────────────

def _build_summary(story: List, analysis: Dict[str, Any], s: Dict) -> None:
    story.append(Paragraph("1. Executive Summary", s["section_title"]))
    story.append(_hr())

    total_css     = analysis.get("total_css_files", 0)
    total_inline  = analysis.get("total_inline_styles", 0)
    sensitives    = analysis.get("sensitive_matches", [])
    hidden        = analysis.get("hidden_fields", [])
    dev_notes     = analysis.get("developer_notes", {})
    ips           = dev_notes.get("ip_addresses", [])
    internal_urls = dev_notes.get("internal_urls", [])
    frameworks    = analysis.get("frameworks", [])

    risk = "LOW"
    risk_color = "#00FF88"
    if sensitives or hidden:
        risk = "HIGH"
        risk_color = "#FF4444"
    elif ips or internal_urls or dev_notes.get("notes"):
        risk = "MEDIUM"
        risk_color = "#FFB700"

    risk_html = (
        f'Overall Risk Rating: <font color="{risk_color}"><b>{risk}</b></font>'
    )
    story.append(Paragraph(risk_html, ParagraphStyle(
        "risk", fontName="Helvetica-Bold", fontSize=12,
        textColor=C_TEXT, spaceAfter=8, leading=16)))

    summary_text = (
        f"StyleLeaker performed an automated HTML/CSS security reconnaissance scan against the target. "
        f"The scan retrieved <b>{total_css}</b> external CSS file(s) and "
        f"<b>{total_inline}</b> inline style block(s). "
        f"A total of <b>{len(sensitives)}</b> sensitive class/ID pattern(s) were detected, "
        f"and <b>{len(hidden)}</b> hidden form field(s) were identified. "
        f"Technology fingerprinting revealed <b>{len(frameworks)}</b> framework(s). "
        f"This report contains all findings, recommendations, and raw data for review."
    )
    story.append(Paragraph(summary_text, s["body"]))
    story.append(Spacer(1, 5 * mm))


# ── Stats Table ────────────────────────────────────────────────────────────────

def _build_stats(story: List, analysis: Dict[str, Any], s: Dict) -> None:
    story.append(Paragraph("2. Scan Statistics", s["section_title"]))
    story.append(_hr())

    dev_notes = analysis.get("developer_notes", {})
    rows = [
        ["Metric", "Count"],
        ["External CSS Files Downloaded",    str(analysis.get("total_css_files", 0))],
        ["Inline Style Blocks",              str(analysis.get("total_inline_styles", 0))],
        ["Sensitive Class/ID Patterns",      str(len(analysis.get("sensitive_matches", [])))],
        ["Hidden Form Fields",               str(len(analysis.get("hidden_fields", [])))],
        ["HTML Comments",                    str(len(analysis.get("html_comments", [])))],
        ["CSS Comments",                     str(len(analysis.get("css_comments", [])))],
        ["Developer Notes (TODO/FIXME)",     str(len(dev_notes.get("notes", [])))],
        ["Internal IP Addresses Found",      str(len(dev_notes.get("ip_addresses", [])))],
        ["Internal URLs Found",              str(len(dev_notes.get("internal_urls", [])))],
        ["CSS Variables Extracted",          str(len(analysis.get("css_variables", [])))],
        ["Media Query Breakpoints",          str(len(analysis.get("media_queries", [])))],
        ["Frameworks Detected",              str(len(analysis.get("frameworks", [])))],
        ["CDNs Detected",                    str(len(analysis.get("cdns", [])))],
    ]

    W = 170 * mm
    tbl = _dark_table(rows, [W * 0.7, W * 0.3])
    story.append(tbl)
    story.append(Spacer(1, 6 * mm))


# ── Framework Detection ────────────────────────────────────────────────────────

def _build_frameworks(story: List, analysis: Dict[str, Any], s: Dict) -> None:
    story.append(Paragraph("3. Framework &amp; Technology Fingerprinting", s["section_title"]))
    story.append(_hr())

    frameworks = analysis.get("frameworks", [])
    versions   = analysis.get("versions", {})
    cdns       = analysis.get("cdns", [])

    if frameworks:
        rows = [["Framework / CMS", "Version Detected"]]
        for fw in frameworks:
            rows.append([fw, versions.get(fw, "Unknown")])
        tbl = _dark_table(rows, [100 * mm, 70 * mm])
        story.append(tbl)
    else:
        story.append(Paragraph("No frameworks detected.", s["body"]))

    story.append(Spacer(1, 4 * mm))
    story.append(Paragraph("CDNs in Use", s["label"]))
    if cdns:
        for cdn in cdns:
            story.append(Paragraph(f"• {cdn}", s["body_mono"]))
    else:
        story.append(Paragraph("None detected.", s["body"]))
    story.append(Spacer(1, 5 * mm))


# ── Sensitive Patterns ─────────────────────────────────────────────────────────

def _build_sensitive(story: List, analysis: Dict[str, Any], s: Dict) -> None:
    story.append(Paragraph("4. Sensitive Pattern Analysis", s["section_title"]))
    story.append(_hr())
    story.append(Paragraph(
        "The following HTML class names and element IDs contain keywords that may indicate "
        "admin panels, authentication flows, internal APIs, payment pages, or other sensitive "
        "application areas.",
        s["body"]
    ))
    story.append(Spacer(1, 3 * mm))

    matches = analysis.get("sensitive_matches", [])
    if matches:
        rows = [["#", "Selector / Identifier", "Risk Indicator"]]
        for i, match in enumerate(matches, 1):
            lower = match.lower()
            risk_keywords = ["admin", "password", "token", "auth", "secret", "api", "config", "payment"]
            is_high = any(k in lower for k in risk_keywords)
            risk_label = "HIGH" if is_high else "MEDIUM"
            rows.append([str(i), match, risk_label])
        W = 170 * mm
        tbl = _dark_table(rows, [W * 0.07, W * 0.65, W * 0.28])
        # Color risk column
        for row_idx, row in enumerate(rows[1:], 1):
            risk_val = row[2]
            clr = C_DANGER if risk_val == "HIGH" else C_WARNING
            tbl.setStyle(TableStyle([
                ("TEXTCOLOR", (2, row_idx), (2, row_idx), clr),
                ("FONTNAME",  (2, row_idx), (2, row_idx), "Helvetica-Bold"),
            ]))
        story.append(tbl)
    else:
        story.append(Paragraph("No sensitive patterns found.", s["body"]))
    story.append(Spacer(1, 5 * mm))


# ── Hidden Fields ──────────────────────────────────────────────────────────────

def _build_hidden_fields(story: List, analysis: Dict[str, Any], s: Dict) -> None:
    story.append(Paragraph("5. Hidden Form Fields — Critical Findings", s["section_title"]))
    story.append(_hr(C_DANGER))
    story.append(Paragraph(
        "Hidden form fields often contain CSRF tokens, session identifiers, internal redirects, "
        "or debugging flags. These are high-value targets in web penetration testing.",
        s["body"]
    ))
    story.append(Spacer(1, 3 * mm))

    hidden = analysis.get("hidden_fields", [])
    if hidden:
        rows = [["Form Action", "Field Name", "Value"]]
        for field in hidden:
            action = field.get("action", "")
            name   = field.get("name", "—")
            value  = field.get("value", "") or "(empty)"
            rows.append([action, name, value])
        W = 170 * mm
        tbl = _dark_table(rows, [W * 0.45, W * 0.3, W * 0.25])
        story.append(tbl)
    else:
        story.append(Paragraph("No hidden form fields found.", s["body"]))
    story.append(Spacer(1, 5 * mm))


# ── Developer Comments ─────────────────────────────────────────────────────────

def _build_dev_notes(story: List, analysis: Dict[str, Any], s: Dict) -> None:
    story.append(Paragraph("6. Developer Comments &amp; Notes", s["section_title"]))
    story.append(_hr(C_WARNING))
    story.append(Paragraph(
        "Developer annotations such as TODO, FIXME, credential references, or API key mentions "
        "found within HTML or CSS source code.",
        s["body"]
    ))
    story.append(Spacer(1, 3 * mm))

    notes = analysis.get("developer_notes", {}).get("notes", [])
    if notes:
        for note in notes:
            story.append(_severity_badge(note, high=False))
    else:
        story.append(Paragraph("No developer notes found.", s["body"]))
    story.append(Spacer(1, 5 * mm))


# ── IPs & Internal URLs ────────────────────────────────────────────────────────

def _build_ips(story: List, analysis: Dict[str, Any], s: Dict) -> None:
    story.append(Paragraph("7. IP Addresses &amp; Internal URLs", s["section_title"]))
    story.append(_hr(C_DANGER))
    story.append(Paragraph(
        "Internal IP addresses and private network URLs discovered inside HTML/CSS comments. "
        "These may reveal backend server topology.",
        s["body"]
    ))
    story.append(Spacer(1, 3 * mm))

    dev = analysis.get("developer_notes", {})
    ips   = dev.get("ip_addresses", [])
    urls  = dev.get("internal_urls", [])

    story.append(Paragraph("IP Addresses", s["label"]))
    if ips:
        for ip in ips:
            story.append(_severity_badge(ip, high=True))
    else:
        story.append(Paragraph("None found.", s["body"]))

    story.append(Spacer(1, 3 * mm))
    story.append(Paragraph("Internal URLs", s["label"]))
    if urls:
        for url in urls:
            story.append(_severity_badge(url, high=True))
    else:
        story.append(Paragraph("None found.", s["body"]))
    story.append(Spacer(1, 5 * mm))


# ── CSS Variables ──────────────────────────────────────────────────────────────

def _build_css_vars(story: List, analysis: Dict[str, Any], s: Dict) -> None:
    story.append(Paragraph("8. CSS Variables", s["section_title"]))
    story.append(_hr())
    story.append(Paragraph(
        "CSS custom properties extracted from all stylesheets. Useful for understanding "
        "design system, color tokens, and theme structure.",
        s["body"]
    ))
    story.append(Spacer(1, 3 * mm))

    variables = analysis.get("css_variables", [])
    if variables:
        rows = [["CSS Variable", "Value"]]
        for var in variables:
            if ":" in var:
                name, value = var.split(":", 1)
                rows.append([name.strip(), value.strip()])
            else:
                rows.append([var, ""])
        W = 170 * mm
        tbl = _dark_table(rows, [W * 0.45, W * 0.55])
        story.append(tbl)
    else:
        story.append(Paragraph("No CSS variables found.", s["body"]))
    story.append(Spacer(1, 5 * mm))


# ── Media Queries ──────────────────────────────────────────────────────────────

def _build_media(story: List, analysis: Dict[str, Any], s: Dict) -> None:
    story.append(Paragraph("9. Media Query Breakpoints", s["section_title"]))
    story.append(_hr())
    story.append(Paragraph(
        "Responsive design breakpoints extracted from all CSS files. "
        "Useful for understanding target layout behavior and screen adaptations.",
        s["body"]
    ))
    story.append(Spacer(1, 3 * mm))

    mqs = analysis.get("media_queries", [])
    if mqs:
        rows = [["#", "Media Query"]]
        for i, mq in enumerate(mqs, 1):
            rows.append([str(i), mq])
        W = 170 * mm
        tbl = _dark_table(rows, [W * 0.08, W * 0.92])
        story.append(tbl)
    else:
        story.append(Paragraph("No media queries found.", s["body"]))
    story.append(Spacer(1, 5 * mm))


# ── HTML Comments ──────────────────────────────────────────────────────────────

def _build_html_comments(story: List, analysis: Dict[str, Any], s: Dict) -> None:
    story.append(Paragraph("10. HTML Comments", s["section_title"]))
    story.append(_hr())
    story.append(Paragraph(
        "All HTML comment blocks extracted from the page source. "
        "Developer comments may contain sensitive notes, disabled code, or internal references.",
        s["body"]
    ))
    story.append(Spacer(1, 3 * mm))

    comments = analysis.get("html_comments", [])
    if comments:
        for i, comment in enumerate(comments, 1):
            story.append(Paragraph(
                f'<font color="#64748B">#{i}</font> '
                f'<font color="#00BFFF">{_escape_for_paragraph(comment[:300])}</font>',
                ParagraphStyle("c", fontName="Courier", fontSize=7.5,
                               textColor=C_ACCENT2, spaceAfter=4, leading=11)))
    else:
        story.append(Paragraph("No HTML comments found.", s["body"]))
    story.append(Spacer(1, 5 * mm))


# ── CSS Comments ───────────────────────────────────────────────────────────────

def _build_css_comments(story: List, analysis: Dict[str, Any], s: Dict) -> None:
    story.append(Paragraph("11. CSS Comments", s["section_title"]))
    story.append(_hr())
    story.append(Paragraph(
        "Comments extracted from downloaded CSS files. "
        "These often contain author info, version tags, license blocks, or developer notes.",
        s["body"]
    ))
    story.append(Spacer(1, 3 * mm))

    comments = analysis.get("css_comments", [])
    if comments:
        for i, comment in enumerate(comments[:40], 1):  # Cap at 40 to keep PDF sane
            story.append(Paragraph(
                f'<font color="#64748B">#{i}</font> '
                f'<font color="#94A3B8">{_escape_for_paragraph(comment[:300])}</font>',
                ParagraphStyle("cc", fontName="Courier", fontSize=7.5,
                               textColor=C_TEXT, spaceAfter=4, leading=11)))
        if len(comments) > 40:
            story.append(Paragraph(
                f"... and {len(comments) - 40} more CSS comments (see report.txt for full list).",
                s["body"]))
    else:
        story.append(Paragraph("No CSS comments found.", s["body"]))
    story.append(Spacer(1, 5 * mm))


# ── Disclaimer ─────────────────────────────────────────────────────────────────

def _build_disclaimer(story: List, s: Dict) -> None:
    story.append(PageBreak())
    story.append(Paragraph("12. Disclaimer &amp; Legal Notice", s["section_title"]))
    story.append(_hr(C_DANGER))
    text = (
        "This report was generated by StyleLeaker, a web security reconnaissance tool developed "
        "by Md. Jony Hassain (HexaCyberLab). This tool and its output are intended EXCLUSIVELY "
        "for authorized security assessments, bug bounty programs, and ethical penetration testing "
        "engagements where explicit written permission has been obtained from the system owner. "
        "<br/><br/>"
        "Unauthorized use of this tool against systems you do not own or have permission to test "
        "is ILLEGAL and may violate computer fraud and cybercrime laws in your jurisdiction. "
        "The author accepts no liability for misuse of this tool or its findings."
        "<br/><br/>"
        "HexaCyberLab | github.com/jonyhossan110 | Web Penetration Testing Services"
    )
    story.append(Paragraph(text, ParagraphStyle(
        "disc", fontName="Helvetica", fontSize=9, textColor=C_MUTED,
        leading=15, spaceAfter=6)))


# ── Main Entry ─────────────────────────────────────────────────────────────────

class Reporter:
    """Professional PDF + Text report generator for StyleLeaker."""

    def __init__(self, logger: Any) -> None:
        self.logger = logger

    def generate_report(
        self,
        target_url: str,
        output_root: Path,
        analysis: Dict[str, Any],
        recon_data: Optional[Dict[str, Any]] = None,
        js_data: Optional[Dict[str, Any]] = None,
        severity_data: Optional[Dict[str, Any]] = None,
        output_format: str = 'both',
        severity_only: bool = False,
    ) -> Path:
        timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")

        # ── 1. Plain text report (kept for CLI quick-view) ──────────────────
        txt_path = output_root / "report.txt"
        if output_format in ('txt', 'both') or (output_format == 'pdf' and not REPORTLAB_AVAILABLE):
            if severity_only and severity_data:
                txt_lines = [
                    "StyleLeaker Severity Report",
                    "=" * 60,
                    f"Target  : {target_url}",
                    f"Scanned : {timestamp}",
                    "",
                    f"Overall Score : {severity_data.get('overall_score', 0)}",
                    f"Risk Level    : {severity_data.get('risk_level', 'INFO')}",
                    "",
                    "High / Critical Findings:",
                ]
                for finding in severity_data.get('findings_list', []):
                    if finding.get('severity') in {'CRITICAL', 'HIGH'}:
                        txt_lines.append(
                            f"- {finding.get('finding')} [{finding.get('severity')}] x{finding.get('count')}"
                        )
            else:
                txt_lines = [
                    "StyleLeaker Scan Report",
                    "=" * 60,
                    f"Target  : {target_url}",
                    f"Scanned : {timestamp}",
                    "",
                    f"CSS Files       : {analysis.get('total_css_files', 0)}",
                    f"Inline Styles   : {analysis.get('total_inline_styles', 0)}",
                    f"Frameworks      : {', '.join(analysis.get('frameworks', [])) or 'None'}",
                    f"CDNs            : {', '.join(analysis.get('cdns', [])) or 'None'}",
                    f"Sensitive Hits  : {len(analysis.get('sensitive_matches', []))}",
                    f"Hidden Fields   : {len(analysis.get('hidden_fields', []))}",
                    f"HTML Comments   : {len(analysis.get('html_comments', []))}",
                    f"CSS Comments    : {len(analysis.get('css_comments', []))}",
                    "",
                ]
                if severity_data:
                    txt_lines.extend([
                        f"Overall Score : {severity_data.get('overall_score', 0)}",
                        f"Risk Level    : {severity_data.get('risk_level', 'INFO')}",
                        "",
                    ])
                if recon_data:
                    headers = recon_data.get('headers', {}).get('findings', {})
                    txt_lines.append("HTTP Security Headers:")
                    for header, details in headers.items():
                        txt_lines.append(f"- {header}: {details.get('value')} ({details.get('status')})")
                    txt_lines.append("")
                    paths = recon_data.get('robots', {}).get('disallowed_paths', [])
                    txt_lines.append("robots.txt Disallowed Paths:")
                    if paths:
                        for path in paths:
                            txt_lines.append(f"- {path}")
                    else:
                        txt_lines.append("- None found")
                    txt_lines.append("")
                txt_lines.append("[ See report.pdf for the full professional report ]")
            from utils.file_handler import save_text_file
            save_text_file(txt_path, "\n".join(txt_lines))
            self.logger.success(f"TXT report saved -> {txt_path}")

        pdf_path = output_root / "report.pdf"
        if output_format in ('pdf', 'both') and REPORTLAB_AVAILABLE:
            doc = SimpleDocTemplate(
                str(pdf_path),
                pagesize=A4,
                leftMargin=15 * mm,
                rightMargin=15 * mm,
                topMargin=18 * mm,
                bottomMargin=18 * mm,
                title=f"StyleLeaker Report — {target_url}",
                author="Md. Jony Hassain | HexaCyberLab",
                subject="Web Security CSS/HTML Reconnaissance Report",
            )

            s = _styles()
            story: List = []

            # Cover
            _build_cover(story, target_url, timestamp, s)
            _build_header_analysis(story, recon_data or {}, s)
            # TOC
            _build_toc(story, s)
            # Sections
            _build_summary(story, analysis, s)
            _build_severity_dashboard(story, severity_data or {}, s)
            _build_stats(story, analysis, s)
            _build_frameworks(story, analysis, s)
            _build_robots_paths(story, recon_data or {}, s)
            _build_response_headers(story, recon_data or {}, s)
            _build_sensitive(story, analysis, s)
            _build_hidden_fields(story, analysis, s)
            _build_dev_notes(story, analysis, s)
            _build_ips(story, analysis, s)
            _build_css_vars(story, analysis, s)
            _build_media(story, analysis, s)
            _build_html_comments(story, analysis, s)
            _build_css_comments(story, analysis, s)
            _build_disclaimer(story, s)

            doc.build(
                story,
                onFirstPage=_on_first_page,
                onLaterPages=_on_later_pages,
            )

            self.logger.success(f"PDF report saved -> {pdf_path}")
            if output_format == 'pdf':
                return pdf_path
        elif output_format in ('pdf', 'both') and not REPORTLAB_AVAILABLE:
            self.logger.warning('ReportLab is not installed; skipping PDF output.')
            if output_format == 'pdf':
                return txt_path
        return txt_path

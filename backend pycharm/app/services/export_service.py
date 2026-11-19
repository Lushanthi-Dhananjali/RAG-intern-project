"""
Export Service for LEARN / NIE Lesson Plans.
Generates publication-quality Microsoft Word (.docx) and Adobe PDF (.pdf) documents
with complete styling, table formatting, colors, and pagination.
"""

from io import BytesIO
import re
from typing import Dict, Any, List, Union, Optional

import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, KeepTogether, HRFlowable, PageBreak
)
from reportlab.pdfgen import canvas


def _clean_str(val: Any) -> str:
    """Helper to convert any value or list to clean text."""
    if val is None:
        return ""
    if isinstance(val, (list, tuple)):
        return "\n".join(str(x) for x in val if x)
    return str(val).strip()


def _set_cell_background(cell, hex_color: str):
    """Sets cell background shading in docx."""
    shading_xml = f'<w:shd {nsdecls("w")} w:fill="{hex_color}"/>'
    cell._tc.get_or_add_tcPr().append(parse_xml(shading_xml))


def _set_cell_margins(cell, top: int = 100, bottom: int = 100, left: int = 150, right: int = 150):
    """Sets padding inside table cells in docx (values in twips, 20 twips = 1 pt)."""
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = OxmlElement('w:tcMar')
    for m, val in [('top', top), ('bottom', bottom), ('left', left), ('right', right)]:
        node = OxmlElement(f'w:{m}')
        node.set(qn('w:w'), str(val))
        node.set(qn('w:type'), 'dxa')
        tcMar.append(node)
    tcPr.append(tcMar)


def generate_docx_stream(plan_data: Union[Dict[str, Any], List[Dict[str, Any]]]) -> BytesIO:
    """
    Generates a professionally styled Microsoft Word (.docx) file
    from a single lesson plan dictionary or a list of multi-period plans.
    """
    if isinstance(plan_data, dict):
        if "lesson_plans" in plan_data and isinstance(plan_data["lesson_plans"], list) and plan_data["lesson_plans"]:
            plans = plan_data["lesson_plans"]
        else:
            plans = [plan_data]
    elif isinstance(plan_data, list):
        plans = plan_data
    else:
        plans = [{}]

    doc = docx.Document()

    # Set 0.75-inch margins for clean printable layout
    for section in doc.sections:
        section.top_margin = Inches(0.75)
        section.bottom_margin = Inches(0.75)
        section.left_margin = Inches(0.75)
        section.right_margin = Inches(0.75)

    PRIMARY_COLOR = RGBColor(30, 58, 138)     # Deep Navy #1E3A8A
    SECONDARY_COLOR = RGBColor(37, 99, 235)  # Royal Blue #2563EB
    MUTED_COLOR = RGBColor(100, 116, 139)    # Slate #64748B
    TEXT_COLOR = RGBColor(15, 23, 42)        # Slate Dark #0F172A

    for idx, plan in enumerate(plans):
        if idx > 0:
            doc.add_page_break()

        # -------------------------------------------------------------
        # 1. Header Banner
        # -------------------------------------------------------------
        title_p = doc.add_paragraph()
        title_p.paragraph_format.space_before = Pt(0)
        title_p.paragraph_format.space_after = Pt(2)
        title_p.alignment = WD_ALIGN_PARAGRAPH.CENTER

        r_inst = title_p.add_run("NATIONAL INSTITUTE OF EDUCATION (NIE) - SRI LANKA\n")
        r_inst.font.name = "Calibri"
        r_inst.font.size = Pt(10)
        r_inst.font.bold = True
        r_inst.font.color.rgb = MUTED_COLOR

        r_title = title_p.add_run("PRACTICE TEACHING LESSON PLAN")
        r_title.font.name = "Calibri"
        r_title.font.size = Pt(16)
        r_title.font.bold = True
        r_title.font.color.rgb = PRIMARY_COLOR

        period_num = plan.get("period_number")
        total_p = plan.get("total_periods")
        if period_num:
            period_str = f"Period {period_num}" + (f" of {total_p}" if total_p else "")
            r_period = title_p.add_run(f" ({period_str})")
            r_period.font.name = "Calibri"
            r_period.font.size = Pt(13)
            r_period.font.bold = True
            r_period.font.color.rgb = SECONDARY_COLOR

        # Decorative line under title
        p_hr = doc.add_paragraph()
        p_hr.paragraph_format.space_before = Pt(0)
        p_hr.paragraph_format.space_after = Pt(8)
        p_hr_border = parse_xml(f'<w:pBdr {nsdecls("w")}><w:bottom w:val="single" w:sz="12" w:space="1" w:color="2563EB"/></w:pBdr>')
        p_hr._p.get_or_add_pPr().append(p_hr_border)

        # -------------------------------------------------------------
        # 2. Metadata Table
        # -------------------------------------------------------------
        meta_table = doc.add_table(rows=4, cols=2)
        meta_table.alignment = WD_TABLE_ALIGNMENT.CENTER
        meta_table.autofit = False

        col_widths = [Inches(1.8), Inches(5.2)]
        for row in meta_table.rows:
            for i, w in enumerate(col_widths):
                row.cells[i].width = w

        meta_rows_data = [
            ("Subject & Grade:", f"{plan.get('subject', 'Civic Education')}  |  {plan.get('grade', 'Grade 8')}"),
            ("Lesson / Topic:", plan.get("lesson", "") or "General Lesson Plan"),
            ("Competency Standard:", plan.get("competence", "")),
            ("Competency Level:", f"{plan.get('competence_level', '')}  (Time: {plan.get('time_allocation', '40 Minutes')})"),
        ]

        for r_idx, (label, val) in enumerate(meta_rows_data):
            cell_lbl = meta_table.cell(r_idx, 0)
            cell_val = meta_table.cell(r_idx, 1)

            _set_cell_background(cell_lbl, "F1F5F9")
            _set_cell_background(cell_val, "FFFFFF")
            _set_cell_margins(cell_lbl, top=80, bottom=80, left=120, right=100)
            _set_cell_margins(cell_val, top=80, bottom=80, left=120, right=100)

            p_l = cell_lbl.paragraphs[0]
            p_l.paragraph_format.space_before = Pt(0)
            p_l.paragraph_format.space_after = Pt(0)
            r = p_l.add_run(label)
            r.font.name = "Calibri"
            r.font.size = Pt(9.5)
            r.font.bold = True
            r.font.color.rgb = PRIMARY_COLOR

            p_v = cell_val.paragraphs[0]
            p_v.paragraph_format.space_before = Pt(0)
            p_v.paragraph_format.space_after = Pt(0)
            r2 = p_v.add_run(_clean_str(val))
            r2.font.name = "Calibri"
            r2.font.size = Pt(9.5)
            r2.font.color.rgb = TEXT_COLOR

        doc.add_paragraph().paragraph_format.space_after = Pt(4)

        # -------------------------------------------------------------
        # 3. Selected Pedagogical Activity Box (If available)
        # -------------------------------------------------------------
        act_title = plan.get("selected_activity_title") or plan.get("selected_activity")
        if act_title:
            p_act = doc.add_paragraph()
            p_act.paragraph_format.space_before = Pt(2)
            p_act.paragraph_format.space_after = Pt(6)
            shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="EFF6FF"/>')
            bdr = parse_xml(f'<w:pBdr {nsdecls("w")}><w:left w:val="single" w:sz="24" w:space="8" w:color="2563EB"/></w:pBdr>')
            p_act._p.get_or_add_pPr().append(shd)
            p_act._p.get_or_add_pPr().append(bdr)

            r_act_lbl = p_act.add_run("   Selected Pedagogical Activity: ")
            r_act_lbl.font.name = "Calibri"
            r_act_lbl.font.size = Pt(10)
            r_act_lbl.font.bold = True
            r_act_lbl.font.color.rgb = SECONDARY_COLOR

            r_act_val = p_act.add_run(f"{act_title}\n")
            r_act_val.font.name = "Calibri"
            r_act_val.font.size = Pt(10.5)
            r_act_val.font.bold = True
            r_act_val.font.color.rgb = PRIMARY_COLOR

        # -------------------------------------------------------------
        # 4. Learning Outcomes
        # -------------------------------------------------------------
        outcomes = plan.get("unique_learning_outcome") or []
        if isinstance(outcomes, str):
            outcomes = [outcomes]

        h_out = doc.add_heading(level=2)
        h_out.paragraph_format.space_before = Pt(6)
        h_out.paragraph_format.space_after = Pt(3)
        r_h = h_out.add_run("1. Learning Outcomes Targeted in this Period")
        r_h.font.name = "Calibri"
        r_h.font.size = Pt(11)
        r_h.font.bold = True
        r_h.font.color.rgb = PRIMARY_COLOR

        if outcomes:
            for o in outcomes:
                p_o = doc.add_paragraph(style='List Bullet')
                p_o.paragraph_format.space_before = Pt(1)
                p_o.paragraph_format.space_after = Pt(2)
                r_o = p_o.add_run(_clean_str(o))
                r_o.font.name = "Calibri"
                r_o.font.size = Pt(9.5)
                r_o.font.color.rgb = TEXT_COLOR
        else:
            p_o = doc.add_paragraph("No specific learning outcomes specified.")
            p_o.runs[0].font.name = "Calibri"
            p_o.runs[0].font.size = Pt(9.5)

        # -------------------------------------------------------------
        # 5. Entrance / Engagement
        # -------------------------------------------------------------
        h_ent = doc.add_heading(level=2)
        h_ent.paragraph_format.space_before = Pt(6)
        h_ent.paragraph_format.space_after = Pt(3)
        r_ent = h_ent.add_run("2. The Entrance / Engagement (5 Minutes)")
        r_ent.font.name = "Calibri"
        r_ent.font.size = Pt(11)
        r_ent.font.bold = True
        r_ent.font.color.rgb = PRIMARY_COLOR

        p_ent = doc.add_paragraph()
        p_ent.paragraph_format.space_before = Pt(1)
        p_ent.paragraph_format.space_after = Pt(6)
        r_ent_txt = p_ent.add_run(_clean_str(plan.get("the_entrance", "Teacher initiates session with relevant hook or inquiry question.")))
        r_ent_txt.font.name = "Calibri"
        r_ent_txt.font.size = Pt(9.5)
        r_ent_txt.font.color.rgb = TEXT_COLOR

        # -------------------------------------------------------------
        # 6. Lesson Development Steps (Table)
        # -------------------------------------------------------------
        h_steps = doc.add_heading(level=2)
        h_steps.paragraph_format.space_before = Pt(6)
        h_steps.paragraph_format.space_after = Pt(4)
        r_steps = h_steps.add_run("3. Lesson Development Steps (30 Minutes)")
        r_steps.font.name = "Calibri"
        r_steps.font.size = Pt(11)
        r_steps.font.bold = True
        r_steps.font.color.rgb = PRIMARY_COLOR

        steps = plan.get("lesson_development_steps") or []
        if steps and isinstance(steps, list):
            table = doc.add_table(rows=1 + len(steps), cols=6)
            table.alignment = WD_TABLE_ALIGNMENT.CENTER
            table.autofit = False

            headers = [
                ("Step & Time", Inches(0.9)),
                ("Teaching Method", Inches(1.1)),
                ("Teaching Aids", Inches(1.0)),
                ("Teacher Activities", Inches(1.5)),
                ("Student Activities", Inches(1.5)),
                ("Formative Assessment", Inches(1.0))
            ]

            hdr_cells = table.rows[0].cells
            for c_idx, (hdr_text, width) in enumerate(headers):
                hdr_cells[c_idx].width = width
                _set_cell_background(hdr_cells[c_idx], "1E3A8A")
                _set_cell_margins(hdr_cells[c_idx], top=100, bottom=100, left=80, right=80)
                p = hdr_cells[c_idx].paragraphs[0]
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                p.paragraph_format.space_before = Pt(0)
                p.paragraph_format.space_after = Pt(0)
                r = p.add_run(hdr_text)
                r.font.name = "Calibri"
                r.font.size = Pt(9)
                r.font.bold = True
                r.font.color.rgb = RGBColor(255, 255, 255)

            for s_idx, step in enumerate(steps, start=1):
                row_cells = table.rows[s_idx].cells
                bg_color = "F8FAFC" if (s_idx % 2 == 1) else "FFFFFF"

                step_num = step.get("step_number", s_idx)
                step_time = step.get("time_minutes", 15)
                method = step.get("learning_teaching_method", "")
                aids = step.get("learning_teaching_aids", "")
                t_act = step.get("teacher_activities", "")
                s_act = step.get("student_activities", "")
                assess = step.get("assessment_and_feedback", "")

                col_values = [
                    f"Step {step_num}\n({step_time} min)",
                    _clean_str(method),
                    _clean_str(aids),
                    _clean_str(t_act),
                    _clean_str(s_act),
                    _clean_str(assess)
                ]

                for col_i, text_val in enumerate(col_values):
                    cell = row_cells[col_i]
                    cell.width = headers[col_i][1]
                    _set_cell_background(cell, bg_color)
                    _set_cell_margins(cell, top=80, bottom=80, left=80, right=80)
                    cell.vertical_alignment = WD_ALIGN_VERTICAL.TOP

                    p = cell.paragraphs[0]
                    p.paragraph_format.space_before = Pt(0)
                    p.paragraph_format.space_after = Pt(0)
                    if col_i == 0:
                        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                    else:
                        p.alignment = WD_ALIGN_PARAGRAPH.LEFT

                    r_v = p.add_run(text_val)
                    r_v.font.name = "Calibri"
                    r_v.font.size = Pt(8.5)
                    r_v.font.color.rgb = TEXT_COLOR
                    if col_i == 0:
                        r_v.font.bold = True

            doc.add_paragraph().paragraph_format.space_after = Pt(4)

        # -------------------------------------------------------------
        # 7. Summary & Whole-Lesson Assessment
        # -------------------------------------------------------------
        summary_txt = _clean_str(plan.get("summary", ""))
        assess_txt = _clean_str(plan.get("assessment_and_feedback_whole_lesson", ""))
        post_txt = _clean_str(plan.get("post_activity", ""))

        h_close = doc.add_heading(level=2)
        h_close.paragraph_format.space_before = Pt(6)
        h_close.paragraph_format.space_after = Pt(3)
        r_close = h_close.add_run("4. Summary, Closure & Whole-Lesson Assessment (5 Minutes)")
        r_close.font.name = "Calibri"
        r_close.font.size = Pt(11)
        r_close.font.bold = True
        r_close.font.color.rgb = PRIMARY_COLOR

        if summary_txt:
            p_sum = doc.add_paragraph()
            p_sum.paragraph_format.space_before = Pt(1)
            p_sum.paragraph_format.space_after = Pt(2)
            r_sum_l = p_sum.add_run("Summary / Consolidation: ")
            r_sum_l.font.name = "Calibri"
            r_sum_l.font.size = Pt(9.5)
            r_sum_l.font.bold = True
            r_sum_l.font.color.rgb = PRIMARY_COLOR
            r_sum_v = p_sum.add_run(summary_txt)
            r_sum_v.font.name = "Calibri"
            r_sum_v.font.size = Pt(9.5)
            r_sum_v.font.color.rgb = TEXT_COLOR

        if assess_txt:
            p_ass = doc.add_paragraph()
            p_ass.paragraph_format.space_before = Pt(1)
            p_ass.paragraph_format.space_after = Pt(2)
            r_ass_l = p_ass.add_run("Formative Assessment & Criteria: ")
            r_ass_l.font.name = "Calibri"
            r_ass_l.font.size = Pt(9.5)
            r_ass_l.font.bold = True
            r_ass_l.font.color.rgb = PRIMARY_COLOR
            r_ass_v = p_ass.add_run(assess_txt)
            r_ass_v.font.name = "Calibri"
            r_ass_v.font.size = Pt(9.5)
            r_ass_v.font.color.rgb = TEXT_COLOR

        # -------------------------------------------------------------
        # 8. Post-Activity / Homework Assignment
        # -------------------------------------------------------------
        if post_txt:
            h_post = doc.add_heading(level=2)
            h_post.paragraph_format.space_before = Pt(6)
            h_post.paragraph_format.space_after = Pt(3)
            r_post = h_post.add_run("5. Concluding Assignment / Post-Activity")
            r_post.font.name = "Calibri"
            r_post.font.size = Pt(11)
            r_post.font.bold = True
            r_post.font.color.rgb = PRIMARY_COLOR

            p_post = doc.add_paragraph()
            p_post.paragraph_format.space_before = Pt(1)
            p_post.paragraph_format.space_after = Pt(4)
            r_post_v = p_post.add_run(post_txt)
            r_post_v.font.name = "Calibri"
            r_post_v.font.size = Pt(9.5)
            r_post_v.font.color.rgb = TEXT_COLOR

        # -------------------------------------------------------------
        # 9. Information Sources & Attachments (Footer Notes)
        # -------------------------------------------------------------
        sources = plan.get("information_sources") or []
        attachments = plan.get("attachments") or []
        if sources or attachments:
            p_meta_extra = doc.add_paragraph()
            p_meta_extra.paragraph_format.space_before = Pt(6)
            p_meta_extra.paragraph_format.space_after = Pt(2)

            if sources:
                r_s_l = p_meta_extra.add_run("Sources: ")
                r_s_l.font.name = "Calibri"
                r_s_l.font.size = Pt(8.5)
                r_s_l.font.bold = True
                r_s_l.font.color.rgb = MUTED_COLOR
                r_s_v = p_meta_extra.add_run(", ".join(str(s) for s in sources if s) + "   |   ")
                r_s_v.font.name = "Calibri"
                r_s_v.font.size = Pt(8.5)
                r_s_v.font.color.rgb = MUTED_COLOR

            if attachments:
                r_a_l = p_meta_extra.add_run("Attachments / Worksheets: ")
                r_a_l.font.name = "Calibri"
                r_a_l.font.size = Pt(8.5)
                r_a_l.font.bold = True
                r_a_l.font.color.rgb = MUTED_COLOR
                r_a_v = p_meta_extra.add_run(", ".join(str(a) for a in attachments if a))
                r_a_v.font.name = "Calibri"
                r_a_v.font.size = Pt(8.5)
                r_a_v.font.color.rgb = MUTED_COLOR

    buffer = BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer


class NumberedCanvas(canvas.Canvas):
    """
    Two-pass canvas that adds running headers and 'Page X of Y' footers to every PDF page.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, page_count: int):
        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#64748B"))
        self.setStrokeColor(colors.HexColor("#CBD5E1"))
        self.setLineWidth(0.5)

        # Footer divider line and text
        self.line(36, 30, 559, 30)
        self.drawString(36, 20, "National Institute of Education (NIE) Sri Lanka — Practice Teaching Lesson Plan")
        page_str = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(559, 20, page_str)
        self.restoreState()


def generate_pdf_stream(plan_data: Union[Dict[str, Any], List[Dict[str, Any]]]) -> BytesIO:
    """
    Generates a pixel-perfect, beautifully laid out Adobe PDF document
    from a single lesson plan dictionary or a list of multi-period plans.
    """
    if isinstance(plan_data, dict):
        if "lesson_plans" in plan_data and isinstance(plan_data["lesson_plans"], list) and plan_data["lesson_plans"]:
            plans = plan_data["lesson_plans"]
        else:
            plans = [plan_data]
    elif isinstance(plan_data, list):
        plans = plan_data
    else:
        plans = [{}]

    buffer = BytesIO()
    # A4: 595.27 x 841.89 points, 0.5-inch margins (36 pt)
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=36,
        rightMargin=36,
        topMargin=42,
        bottomMargin=42
    )

    styles = getSampleStyleSheet()

    style_inst = ParagraphStyle(
        'InstTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8.5,
        leading=10,
        alignment=1, # Center
        textColor=colors.HexColor("#64748B"),
    )

    style_title = ParagraphStyle(
        'PlanTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=14,
        leading=16,
        alignment=1, # Center
        textColor=colors.HexColor("#1E3A8A"),
    )

    style_sec_heading = ParagraphStyle(
        'SecHeading',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=10,
        leading=13,
        textColor=colors.HexColor("#1E3A8A"),
        spaceBefore=7,
        spaceAfter=3,
    )

    style_meta_label = ParagraphStyle(
        'MetaLabel',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8.5,
        leading=11,
        textColor=colors.HexColor("#1E3A8A"),
    )

    style_meta_val = ParagraphStyle(
        'MetaVal',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=11,
        textColor=colors.HexColor("#0F172A"),
    )

    style_body = ParagraphStyle(
        'PlanBody',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=11.5,
        textColor=colors.HexColor("#0F172A"),
        spaceAfter=3,
    )

    style_bullet = ParagraphStyle(
        'PlanBullet',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=11,
        textColor=colors.HexColor("#0F172A"),
        leftIndent=14,
        firstLineIndent=-10,
        spaceAfter=2,
    )

    style_tbl_hdr = ParagraphStyle(
        'TblHdr',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=7.5,
        leading=9,
        alignment=1,
        textColor=colors.white,
    )

    style_tbl_cell = ParagraphStyle(
        'TblCell',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=7.5,
        leading=9.5,
        textColor=colors.HexColor("#0F172A"),
    )

    style_tbl_cell_center = ParagraphStyle(
        'TblCellCenter',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=7.5,
        leading=9.5,
        alignment=1,
        textColor=colors.HexColor("#0F172A"),
    )

    story = []
    TOTAL_WIDTH = 523.27  # 595.27 - 72

    for p_idx, plan in enumerate(plans):
        if p_idx > 0:
            story.append(PageBreak())

        # 1. Header
        story.append(Paragraph("NATIONAL INSTITUTE OF EDUCATION (NIE) SRI LANKA", style_inst))
        
        period_num = plan.get("period_number")
        total_p = plan.get("total_periods")
        period_str = ""
        if period_num:
            period_str = f" (Period {period_num}" + (f" of {total_p}" if total_p else "") + ")"
        
        story.append(Paragraph(f"PRACTICE TEACHING LESSON PLAN{period_str}", style_title))
        story.append(Spacer(1, 4))
        story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#2563EB"), spaceBefore=2, spaceAfter=6))

        # 2. Metadata Grid Table
        meta_data = [
            [
                Paragraph("Subject & Grade:", style_meta_label),
                Paragraph(f"{plan.get('subject', 'Civic Education')} | {plan.get('grade', 'Grade 8')}", style_meta_val)
            ],
            [
                Paragraph("Lesson / Topic:", style_meta_label),
                Paragraph(_clean_str(plan.get("lesson", "") or "General Lesson Plan"), style_meta_val)
            ],
            [
                Paragraph("Competency:", style_meta_label),
                Paragraph(_clean_str(plan.get("competence", "")), style_meta_val)
            ],
            [
                Paragraph("Competency Level:", style_meta_label),
                Paragraph(f"{plan.get('competence_level', '')} &nbsp;&nbsp;|&nbsp;&nbsp; <b>Time:</b> {plan.get('time_allocation', '40 Minutes')}", style_meta_val)
            ]
        ]
        meta_table = Table(meta_data, colWidths=[120, TOTAL_WIDTH - 120])
        meta_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor("#F1F5F9")),
            ('BACKGROUND', (1, 0), (1, -1), colors.white),
            ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
            ('TOPPADDING', (0, 0), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        story.append(meta_table)
        story.append(Spacer(1, 4))

        # 3. Selected Pedagogical Activity Box
        act_title = plan.get("selected_activity_title") or plan.get("selected_activity")
        if act_title:
            act_data = [[
                Paragraph(f"<b>Selected Pedagogical Activity:</b> {act_title}", style_meta_val)
            ]]
            act_tbl = Table(act_data, colWidths=[TOTAL_WIDTH])
            act_tbl.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#EFF6FF")),
                ('BOX', (0, 0), (-1, -1), 1.0, colors.HexColor("#2563EB")),
                ('LEFTPADDING', (0, 0), (-1, -1), 8),
                ('RIGHTPADDING', (0, 0), (-1, -1), 8),
                ('TOPPADDING', (0, 0), (-1, -1), 4),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ]))
            story.append(act_tbl)
            story.append(Spacer(1, 5))

        # 4. Learning Outcomes
        outcomes = plan.get("unique_learning_outcome") or []
        if isinstance(outcomes, str):
            outcomes = [outcomes]

        story.append(Paragraph("1. Learning Outcomes Targeted in this Period", style_sec_heading))
        if outcomes:
            for o in outcomes:
                story.append(Paragraph(f"&bull;&nbsp;&nbsp;{_clean_str(o)}", style_bullet))
        else:
            story.append(Paragraph("No specific learning outcomes specified.", style_body))

        # 5. The Entrance
        story.append(Paragraph("2. The Entrance / Engagement (5 Minutes)", style_sec_heading))
        story.append(Paragraph(_clean_str(plan.get("the_entrance", "Teacher initiates session with relevant hook.")), style_body))

        # 6. Development Steps (Table)
        story.append(Paragraph("3. Lesson Development Steps (30 Minutes)", style_sec_heading))
        steps = plan.get("lesson_development_steps") or []
        if steps and isinstance(steps, list):
            col_widths = [48, 72, 68, 145, 145, 45]
            step_table_data = [[
                Paragraph("Step & Time", style_tbl_hdr),
                Paragraph("Method", style_tbl_hdr),
                Paragraph("Teaching Aids", style_tbl_hdr),
                Paragraph("Teacher Activities", style_tbl_hdr),
                Paragraph("Student Activities", style_tbl_hdr),
                Paragraph("Formative Check", style_tbl_hdr),
            ]]

            for s_idx, s in enumerate(steps, start=1):
                s_num = s.get("step_number", s_idx)
                s_time = s.get("time_minutes", 15)
                step_table_data.append([
                    Paragraph(f"<b>Step {s_num}</b><br/>({s_time} min)", style_tbl_cell_center),
                    Paragraph(_clean_str(s.get("learning_teaching_method", "")), style_tbl_cell),
                    Paragraph(_clean_str(s.get("learning_teaching_aids", "")), style_tbl_cell),
                    Paragraph(_clean_str(s.get("teacher_activities", "")), style_tbl_cell),
                    Paragraph(_clean_str(s.get("student_activities", "")), style_tbl_cell),
                    Paragraph(_clean_str(s.get("assessment_and_feedback", "")), style_tbl_cell),
                ])

            step_tbl = Table(step_table_data, colWidths=col_widths, repeatRows=1)
            t_style = [
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#1E3A8A")),
                ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
                ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
                ('TOPPADDING', (0, 0), (-1, -1), 3),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
                ('LEFTPADDING', (0, 0), (-1, -1), 4),
                ('RIGHTPADDING', (0, 0), (-1, -1), 4),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ]
            for row_idx in range(1, len(step_table_data)):
                bg = colors.HexColor("#F8FAFC") if row_idx % 2 == 1 else colors.white
                t_style.append(('BACKGROUND', (0, row_idx), (-1, row_idx), bg))

            step_tbl.setStyle(TableStyle(t_style))
            story.append(step_tbl)
            story.append(Spacer(1, 4))

        # 7. Closure & Summary
        story.append(Paragraph("4. Summary, Closure & Whole-Lesson Assessment (5 Minutes)", style_sec_heading))
        if plan.get("summary"):
            story.append(Paragraph(f"<b>Summary / Consolidation:</b> {_clean_str(plan.get('summary'))}", style_body))
        if plan.get("assessment_and_feedback_whole_lesson"):
            story.append(Paragraph(f"<b>Formative Assessment:</b> {_clean_str(plan.get('assessment_and_feedback_whole_lesson'))}", style_body))

        # 8. Post-Activity
        if plan.get("post_activity"):
            story.append(Paragraph("5. Concluding Assignment / Post-Activity", style_sec_heading))
            story.append(Paragraph(_clean_str(plan.get("post_activity")), style_body))

        # 9. Extra info
        sources = plan.get("information_sources") or []
        attachments = plan.get("attachments") or []
        extra_bits = []
        if sources:
            extra_bits.append(f"<b>Sources:</b> {', '.join(str(s) for s in sources if s)}")
        if attachments:
            extra_bits.append(f"<b>Worksheets:</b> {', '.join(str(a) for a in attachments if a)}")
        if extra_bits:
            story.append(Spacer(1, 4))
            p_extra_style = ParagraphStyle(
                'ExtraBits',
                parent=styles['Normal'],
                fontName='Helvetica',
                fontSize=7.5,
                leading=10,
                textColor=colors.HexColor("#64748B"),
                spaceBefore=3,
            )
            story.append(Paragraph(" &nbsp;|&nbsp; ".join(extra_bits), p_extra_style))

    doc.build(story, canvasmaker=NumberedCanvas)
    buffer.seek(0)
    return buffer

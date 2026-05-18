from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import mm, cm
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, HRFlowable, Image as RLImage
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.pdfgen import canvas as rl_canvas
from datetime import datetime
import os, io

NAVY = colors.HexColor('#0d1a5e')
GOLD = colors.HexColor('#f9a825')
RED = colors.HexColor('#c62828')
LIGHT_BLUE = colors.HexColor('#e8eaf6')
WHITE = colors.white
DARK = colors.HexColor('#1a1a2e')

def get_logo_path(app):
    return os.path.join(app.root_path, 'static', 'images', 'logo.jpg')

def draw_header(c, doc, app, title, subtitle=''):
    """Draw a beautiful header on each page."""
    w, h = doc.pagesize
    # Top navy bar
    c.setFillColor(NAVY)
    c.rect(0, h - 60, w, 60, fill=1, stroke=0)
    # Gold stripe
    c.setFillColor(GOLD)
    c.rect(0, h - 65, w, 5, fill=1, stroke=0)

    # Logo
    logo_path = get_logo_path(app)
    if os.path.exists(logo_path):
        try:
            c.drawImage(logo_path, 15, h - 57, width=45, height=45, preserveAspectRatio=True)
        except Exception:
            pass

    # School name
    c.setFillColor(GOLD)
    c.setFont('Helvetica-Bold', 13)
    c.drawString(70, h - 25, 'THE FEDERAL POLYTECHNIC NASARAWA')
    c.setFillColor(WHITE)
    c.setFont('Helvetica', 9)
    c.drawString(70, h - 40, 'School of Information Technology — Department of Computer Science')
    c.setFont('Helvetica-Bold', 10)
    c.drawString(70, h - 55, title)

    if subtitle:
        c.setFont('Helvetica', 8)
        c.setFillColor(GOLD)
        c.drawRightString(w - 15, h - 55, subtitle)

    # Footer
    c.setFillColor(NAVY)
    c.rect(0, 0, w, 25, fill=1, stroke=0)
    c.setFillColor(GOLD)
    c.rect(0, 25, w, 2, fill=1, stroke=0)
    c.setFillColor(WHITE)
    c.setFont('Helvetica', 7)
    c.drawString(15, 8, f'Generated: {datetime.now().strftime("%d %B %Y, %I:%M %p")}')
    c.drawRightString(w - 15, 8, 'Federal Polytechnic Nasarawa — QR ID Verification System')
    c.drawCentredString(w / 2, 8, f'Page {doc.page}')

def generate_students_report(students, app, filters=None):
    """Generate a full student list PDF report."""
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=landscape(A4),
                            topMargin=75, bottomMargin=35,
                            leftMargin=15, rightMargin=15)

    styles = getSampleStyleSheet()
    elements = []

    # Title block
    title_style = ParagraphStyle('title', fontSize=14, textColor=NAVY,
                                 fontName='Helvetica-Bold', alignment=TA_CENTER, spaceAfter=4)
    sub_style = ParagraphStyle('sub', fontSize=9, textColor=colors.grey,
                               alignment=TA_CENTER, spaceAfter=10)

    elements.append(Paragraph('STUDENT REGISTRATION REPORT', title_style))
    filter_text = ''
    if filters:
        parts = [f"{k}: {v}" for k, v in filters.items() if v]
        filter_text = ' | '.join(parts) if parts else 'All Students'
    elements.append(Paragraph(filter_text or 'All Registered Students', sub_style))
    elements.append(HRFlowable(width='100%', thickness=2, color=NAVY))
    elements.append(Spacer(1, 8))

    # Stats row
    active = sum(1 for s in students if s.card_status == 'active')
    expired = sum(1 for s in students if s.card_status == 'expired')
    suspended = sum(1 for s in students if s.card_status == 'suspended')

    stats_data = [['Total Students', 'Active Cards', 'Expired Cards', 'Suspended']]
    stats_data.append([str(len(students)), str(active), str(expired), str(suspended)])
    stats_table = Table(stats_data, colWidths=[70*mm]*4)
    stats_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), NAVY),
        ('TEXTCOLOR', (0, 0), (-1, 0), WHITE),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('BACKGROUND', (0, 1), (-1, 1), LIGHT_BLUE),
        ('FONTNAME', (0, 1), (-1, 1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 1), (-1, 1), 14),
        ('TEXTCOLOR', (0, 1), (-1, 1), NAVY),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ROWBACKGROUNDS', (0, 1), (-1, 1), [LIGHT_BLUE]),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.white),
        ('ROUNDEDCORNERS', [5]),
    ]))
    elements.append(stats_table)
    elements.append(Spacer(1, 10))

    # Main table
    headers = ['#', 'Matric Number', 'Full Name', 'Department', 'Level', 'Session', 'Gender', 'Status', 'Registered']
    data = [headers]
    for i, s in enumerate(students, 1):
        reg_date = s.registered_at.strftime('%d/%m/%Y') if s.registered_at else '-'
        data.append([
            str(i), s.matric_number, s.full_name, s.department,
            s.level, s.academic_session, s.gender or '-',
            s.card_status.upper(), reg_date
        ])

    col_widths = [10*mm, 35*mm, 55*mm, 50*mm, 18*mm, 22*mm, 16*mm, 22*mm, 24*mm]
    table = Table(data, colWidths=col_widths, repeatRows=1)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), NAVY),
        ('TEXTCOLOR', (0, 0), (-1, 0), GOLD),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 8),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 7.5),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [WHITE, LIGHT_BLUE]),
        ('GRID', (0, 0), (-1, -1), 0.3, colors.HexColor('#cccccc')),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LEFTPADDING', (0, 0), (-1, -1), 4),
    ]))
    elements.append(table)

    def on_page(canvas_obj, doc_obj):
        canvas_obj.saveState()
        draw_header(canvas_obj, doc_obj, app, 'STUDENT REGISTRATION REPORT',
                    f'Total: {len(students)} students')
        canvas_obj.restoreState()

    doc.build(elements, onFirstPage=on_page, onLaterPages=on_page)
    buf.seek(0)
    return buf

def generate_scan_logs_report(logs, app, filters=None):
    """Generate scan logs PDF report."""
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=landscape(A4),
                            topMargin=75, bottomMargin=35,
                            leftMargin=15, rightMargin=15)
    styles = getSampleStyleSheet()
    elements = []

    title_style = ParagraphStyle('title', fontSize=14, textColor=NAVY,
                                 fontName='Helvetica-Bold', alignment=TA_CENTER, spaceAfter=4)
    sub_style = ParagraphStyle('sub', fontSize=9, textColor=colors.grey,
                               alignment=TA_CENTER, spaceAfter=10)

    elements.append(Paragraph('SCAN LOGS & VERIFICATION REPORT', title_style))
    elements.append(Paragraph(f'Total Scans: {len(logs)}', sub_style))
    elements.append(HRFlowable(width='100%', thickness=2, color=NAVY))
    elements.append(Spacer(1, 10))

    headers = ['#', 'Student Name', 'Matric No.', 'Scanned By', 'Purpose', 'Location', 'Result', 'Date & Time']
    data = [headers]
    for i, log in enumerate(logs, 1):
        scanner = log.scanned_by_user.username if log.scanned_by_user else 'Public Scan'
        data.append([
            str(i),
            log.student.full_name if log.student else 'Unknown',
            log.student.matric_number if log.student else '-',
            scanner,
            (log.purpose or '-').capitalize(),
            log.location or '-',
            log.scan_result.upper() if log.scan_result else '-',
            log.scanned_at.strftime('%d/%m/%Y %I:%M %p') if log.scanned_at else '-'
        ])

    col_widths = [10*mm, 50*mm, 32*mm, 30*mm, 25*mm, 30*mm, 22*mm, 40*mm]
    table = Table(data, colWidths=col_widths, repeatRows=1)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), NAVY),
        ('TEXTCOLOR', (0, 0), (-1, 0), GOLD),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 8),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 7.5),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [WHITE, LIGHT_BLUE]),
        ('GRID', (0, 0), (-1, -1), 0.3, colors.HexColor('#cccccc')),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
    ]))
    elements.append(table)

    def on_page(canvas_obj, doc_obj):
        canvas_obj.saveState()
        draw_header(canvas_obj, doc_obj, app, 'SCAN LOGS & VERIFICATION REPORT',
                    f'Total Scans: {len(logs)}')
        canvas_obj.restoreState()

    doc.build(elements, onFirstPage=on_page, onLaterPages=on_page)
    buf.seek(0)
    return buf

def generate_single_student_report(student, scan_logs, app):
    """Generate a detailed report for a single student."""
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4,
                            topMargin=75, bottomMargin=35,
                            leftMargin=20, rightMargin=20)
    elements = []
    styles = getSampleStyleSheet()

    label_style = ParagraphStyle('label', fontSize=9, textColor=colors.grey, fontName='Helvetica')
    value_style = ParagraphStyle('value', fontSize=11, textColor=DARK, fontName='Helvetica-Bold', spaceAfter=6)
    section_style = ParagraphStyle('section', fontSize=11, textColor=NAVY, fontName='Helvetica-Bold',
                                   spaceBefore=12, spaceAfter=4)

    elements.append(Paragraph('STUDENT PROFILE REPORT', ParagraphStyle(
        'title', fontSize=16, textColor=NAVY, fontName='Helvetica-Bold',
        alignment=TA_CENTER, spaceAfter=4)))
    elements.append(HRFlowable(width='100%', thickness=2, color=NAVY))
    elements.append(Spacer(1, 10))

    # Info table
    info_data = [
        ['Full Name', student.full_name, 'Matric Number', student.matric_number],
        ['Department', student.department, 'School', student.school],
        ['Level', student.level, 'Academic Session', student.academic_session],
        ['Gender', student.gender or '-', 'Phone', student.phone or '-'],
        ['Card Status', student.card_status.upper(), 'Valid Until',
         student.card_expiry.strftime('%B %Y') if student.card_expiry else '-'],
        ['Registered', student.registered_at.strftime('%d %B %Y') if student.registered_at else '-', '', ''],
    ]
    info_table = Table(info_data, colWidths=[40*mm, 65*mm, 40*mm, 65*mm])
    info_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (2, 0), (2, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('TEXTCOLOR', (0, 0), (0, -1), colors.grey),
        ('TEXTCOLOR', (2, 0), (2, -1), colors.grey),
        ('TEXTCOLOR', (1, 0), (1, -1), DARK),
        ('TEXTCOLOR', (3, 0), (3, -1), DARK),
        ('FONTNAME', (1, 0), (1, -1), 'Helvetica-Bold'),
        ('FONTNAME', (3, 0), (3, -1), 'Helvetica-Bold'),
        ('ROWBACKGROUNDS', (0, 0), (-1, -1), [WHITE, LIGHT_BLUE]),
        ('GRID', (0, 0), (-1, -1), 0.3, colors.HexColor('#dddddd')),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
    ]))
    elements.append(info_table)

    # Scan history
    if scan_logs:
        elements.append(Spacer(1, 14))
        elements.append(Paragraph('SCAN HISTORY', section_style))
        elements.append(HRFlowable(width='100%', thickness=1, color=GOLD))
        elements.append(Spacer(1, 6))

        scan_headers = ['#', 'Scanned By', 'Purpose', 'Location', 'Result', 'Date & Time']
        scan_data = [scan_headers]
        for i, log in enumerate(scan_logs, 1):
            scanner = log.scanned_by_user.username if log.scanned_by_user else 'Public Scan'
            scan_data.append([
                str(i), scanner,
                (log.purpose or '-').capitalize(),
                log.location or '-',
                log.scan_result.upper() if log.scan_result else '-',
                log.scanned_at.strftime('%d/%m/%Y %I:%M %p') if log.scanned_at else '-'
            ])
        scan_table = Table(scan_data, colWidths=[10*mm, 45*mm, 28*mm, 35*mm, 22*mm, 45*mm])
        scan_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), NAVY),
            ('TEXTCOLOR', (0, 0), (-1, 0), GOLD),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [WHITE, LIGHT_BLUE]),
            ('GRID', (0, 0), (-1, -1), 0.3, colors.HexColor('#cccccc')),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ]))
        elements.append(scan_table)

    def on_page(canvas_obj, doc_obj):
        canvas_obj.saveState()
        draw_header(canvas_obj, doc_obj, app, f'STUDENT PROFILE: {student.matric_number}',
                    student.full_name)
        canvas_obj.restoreState()

    doc.build(elements, onFirstPage=on_page, onLaterPages=on_page)
    buf.seek(0)
    return buf

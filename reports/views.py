import io
from datetime import datetime
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.http import HttpResponse
from django.contrib import messages

from .models import NightReport
from core.models import Team
from briefing.models import PreBriefingForm, NightBriefing, BriefingActionItem
from qa.models import QAChecklistForm, NonConformance
from monitoring.models import IncidentReport, TeamStatus, ActivityLog


def report_dashboard(request):
    reports = NightReport.objects.all()[:30]
    today = timezone.now().date()

    # Check if today's report exists
    today_report = NightReport.objects.filter(date=today).first()

    # Quick stats for today
    briefing_count = PreBriefingForm.objects.filter(shift_date=today).count()
    qa_count = QAChecklistForm.objects.filter(shift_date=today).count()
    incident_count = IncidentReport.objects.filter(reported_at__date=today).count()

    return render(request, 'reports/dashboard.html', {
        'reports': reports,
        'today': today,
        'today_report': today_report,
        'briefing_count': briefing_count,
        'qa_count': qa_count,
        'incident_count': incident_count,
    })


def report_generate(request, date_str=None):
    """Generate/view consolidated report for a given date."""
    if date_str:
        date = datetime.strptime(date_str, '%Y-%m-%d').date()
    else:
        date = timezone.now().date()

    # Get or create report
    report, created = NightReport.objects.get_or_create(date=date)

    if request.method == 'POST':
        report.manager_summary = request.POST.get('manager_summary', '')
        report.key_issues = request.POST.get('key_issues', '')
        report.handover_notes = request.POST.get('handover_notes', '')
        report.status = 'reviewed'
        report.save()
        messages.success(request, 'Report updated successfully!')
        return redirect('reports:report_view', date_str=date.strftime('%Y-%m-%d'))

    # Gather all data
    teams = Team.objects.filter(is_active=True)
    briefing_forms = PreBriefingForm.objects.filter(shift_date=date).select_related('team', 'submitted_by')
    qa_forms = QAChecklistForm.objects.filter(shift_date=date).select_related('team', 'project', 'submitted_by')
    night_briefing = NightBriefing.objects.filter(date=date).first()
    incidents = IncidentReport.objects.filter(reported_at__date=date).select_related('team', 'reported_by')
    team_statuses = TeamStatus.objects.filter(date=date).select_related('team')
    action_items = BriefingActionItem.objects.filter(
        briefing__date=date
    ).select_related('assigned_to', 'team') if night_briefing else []
    open_ncrs = NonConformance.objects.exclude(status='closed').select_related('project')

    # Calculate summary stats
    total_staff_present = sum(f.staff_present for f in briefing_forms)
    total_staff_expected = sum(f.staff_expected for f in briefing_forms)

    risk_counts = {
        'green': briefing_forms.filter(risk_rating='green').count(),
        'amber': briefing_forms.filter(risk_rating='amber').count(),
        'red': briefing_forms.filter(risk_rating='red').count(),
    }

    qa_stats = {
        'total': qa_forms.count(),
        'approved': qa_forms.filter(overall_outcome='approved').count(),
        'conditional': qa_forms.filter(overall_outcome='conditional').count(),
        'rework': qa_forms.filter(overall_outcome='rework').count(),
        'rejected': qa_forms.filter(overall_outcome='rejected').count(),
        'avg_compliance': 0,
    }
    if qa_forms.exists():
        qa_stats['avg_compliance'] = round(sum(f.compliance_percentage for f in qa_forms) / qa_forms.count())

    # Update report summary
    report.total_teams = teams.count()
    report.briefing_forms_submitted = briefing_forms.count()
    report.qa_forms_submitted = qa_forms.count()
    report.total_staff_present = total_staff_present
    report.total_staff_expected = total_staff_expected
    report.incidents_count = incidents.count()

    # Determine overall risk
    if risk_counts['red'] > 0 or incidents.filter(severity__in=['major', 'serious']).exists():
        report.overall_risk = 'red'
    elif risk_counts['amber'] > 0 or qa_stats['rework'] > 0 or qa_stats['rejected'] > 0:
        report.overall_risk = 'amber'
    else:
        report.overall_risk = 'green'

    report.status = 'generated' if report.status == 'draft' else report.status
    report.save()

    # Safety concerns
    safety_concerns = briefing_forms.exclude(safety_concerns='').values_list('team__code', 'team__name', 'safety_concerns')

    return render(request, 'reports/report_view.html', {
        'report': report,
        'date': date,
        'teams': teams,
        'briefing_forms': briefing_forms,
        'qa_forms': qa_forms,
        'night_briefing': night_briefing,
        'incidents': incidents,
        'team_statuses': team_statuses,
        'action_items': action_items,
        'open_ncrs': open_ncrs,
        'total_staff_present': total_staff_present,
        'total_staff_expected': total_staff_expected,
        'risk_counts': risk_counts,
        'qa_stats': qa_stats,
        'safety_concerns': safety_concerns,
    })


def report_pdf(request, date_str):
    """Generate PDF of consolidated night report."""
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import mm, cm
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, HRFlowable
    from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT

    date = datetime.strptime(date_str, '%Y-%m-%d').date()

    # Gather data
    report = NightReport.objects.filter(date=date).first()
    briefing_forms = PreBriefingForm.objects.filter(shift_date=date).select_related('team', 'submitted_by')
    qa_forms = QAChecklistForm.objects.filter(shift_date=date).select_related('team', 'project')
    night_briefing = NightBriefing.objects.filter(date=date).first()
    incidents = IncidentReport.objects.filter(reported_at__date=date).select_related('team', 'reported_by')
    open_ncrs = NonConformance.objects.exclude(status='closed').select_related('project')

    total_staff_present = sum(f.staff_present for f in briefing_forms)
    total_staff_expected = sum(f.staff_expected for f in briefing_forms)

    # PDF setup
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        leftMargin=1.5*cm, rightMargin=1.5*cm,
        topMargin=2*cm, bottomMargin=2*cm,
    )

    styles = getSampleStyleSheet()

    # Custom styles
    styles.add(ParagraphStyle(
        'ReportTitle', parent=styles['Title'],
        fontSize=22, spaceAfter=4*mm, textColor=colors.HexColor('#1a1a2e'),
    ))
    styles.add(ParagraphStyle(
        'SectionHeader', parent=styles['Heading1'],
        fontSize=14, spaceAfter=3*mm, spaceBefore=6*mm,
        textColor=colors.HexColor('#1a1a2e'),
        borderWidth=0, borderColor=colors.HexColor('#fbbf24'),
        borderPadding=2*mm,
    ))
    styles.add(ParagraphStyle(
        'SubHeader', parent=styles['Heading2'],
        fontSize=11, spaceAfter=2*mm, spaceBefore=4*mm,
        textColor=colors.HexColor('#374151'),
    ))
    styles.add(ParagraphStyle(
        'ReportBody', parent=styles['Normal'],
        fontSize=9, spaceAfter=2*mm, leading=13,
    ))
    styles.add(ParagraphStyle(
        'SmallText', parent=styles['Normal'],
        fontSize=8, textColor=colors.HexColor('#6b7280'),
    ))

    story = []

    # ---- HEADER ----
    story.append(Paragraph('NIGHT OPERATIONS REPORT', styles['ReportTitle']))
    story.append(Paragraph(f'AtkinsRéalis — Heathrow Infrastructure Programme', styles['ReportBody']))
    story.append(Paragraph(f'Date: {date.strftime("%A, %d %B %Y")} | Shift: Night', styles['ReportBody']))
    if report and report.generated_by:
        story.append(Paragraph(f'Prepared by: {report.generated_by.get_full_name() or report.generated_by.username}', styles['SmallText']))
    story.append(Spacer(1, 4*mm))
    story.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor('#fbbf24')))
    story.append(Spacer(1, 4*mm))

    # ---- 1. EXECUTIVE SUMMARY ----
    story.append(Paragraph('1. EXECUTIVE SUMMARY', styles['SectionHeader']))

    risk_color = {'green': '#22c55e', 'amber': '#f59e0b', 'red': '#ef4444'}.get(
        report.overall_risk if report else 'green', '#22c55e'
    )
    staff_pct = round((total_staff_present / total_staff_expected * 100)) if total_staff_expected else 0

    summary_data = [
        ['Metric', 'Value'],
        ['Overall Risk Rating', report.overall_risk.upper() if report else 'N/A'],
        ['Teams Reporting', f'{briefing_forms.count()} / {Team.objects.filter(is_active=True).count()}'],
        ['Staff Present', f'{total_staff_present} / {total_staff_expected} ({staff_pct}%)'],
        ['QA Inspections', f'{qa_forms.count()} completed'],
        ['Incidents', f'{incidents.count()} reported'],
        ['Open NCRs', f'{open_ncrs.count()}'],
    ]

    t = Table(summary_data, colWidths=[120, 350])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a1a2e')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#d1d5db')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f9fafb')]),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(t)
    story.append(Spacer(1, 3*mm))

    if report and report.manager_summary:
        story.append(Paragraph('Manager Summary:', styles['SubHeader']))
        story.append(Paragraph(report.manager_summary, styles['ReportBody']))

    # ---- 2. NIGHT BRIEFING ----
    story.append(Paragraph('2. NIGHT BRIEFING SUBMISSIONS', styles['SectionHeader']))

    if briefing_forms.exists():
        brief_data = [['Team', 'Staff', 'Equipment', 'PPE', 'Permits', 'Risk', 'Submitted']]
        for f in briefing_forms:
            equip_map = {'all_ok': 'OK', 'minor_issues': 'Minor', 'major_issues': 'MAJOR', 'critical': 'CRITICAL'}
            brief_data.append([
                f.team.code,
                f'{f.staff_present}/{f.staff_expected}',
                equip_map.get(f.equipment_status, f.equipment_status),
                'Yes' if f.ppe_check_completed else 'NO',
                'Yes' if f.permits_in_place else 'NO',
                f.risk_rating.upper(),
                f.submitted_at.strftime('%H:%M'),
            ])

        t = Table(brief_data, colWidths=[50, 55, 65, 40, 50, 50, 55])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a1a2e')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#d1d5db')),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f9fafb')]),
            ('TOPPADDING', (0, 0), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ]))
        story.append(t)
        story.append(Spacer(1, 3*mm))

        # Safety concerns
        concerns = briefing_forms.exclude(safety_concerns='')
        if concerns.exists():
            story.append(Paragraph('Safety Concerns Raised:', styles['SubHeader']))
            for f in concerns:
                story.append(Paragraph(f'<b>{f.team.code}:</b> {f.safety_concerns}', styles['ReportBody']))

        # Planned tasks
        story.append(Paragraph('Planned Tasks Tonight:', styles['SubHeader']))
        for f in briefing_forms:
            if f.planned_tasks_tonight:
                story.append(Paragraph(f'<b>{f.team.code}:</b> {f.planned_tasks_tonight}', styles['ReportBody']))

        # Blockers
        blockers = briefing_forms.exclude(blockers='')
        if blockers.exists():
            story.append(Paragraph('Blockers / Dependencies:', styles['SubHeader']))
            for f in blockers:
                story.append(Paragraph(f'<b>{f.team.code}:</b> {f.blockers}', styles['ReportBody']))
    else:
        story.append(Paragraph('No briefing forms submitted for this date.', styles['ReportBody']))

    # ---- 3. QA INSPECTIONS ----
    story.append(PageBreak())
    story.append(Paragraph('3. QA INSPECTION REPORTS', styles['SectionHeader']))

    if qa_forms.exists():
        qa_data = [['Team', 'Area Inspected', 'Project', 'Workmanship', 'Compliance', 'Snags', 'Outcome']]
        for f in qa_forms:
            qa_data.append([
                f.team.code,
                f.area_inspected[:30],
                f.project.name[:20] if f.project else '-',
                f.get_workmanship_quality_display(),
                f'{f.compliance_percentage}%',
                str(f.snags_count),
                f.get_overall_outcome_display(),
            ])

        t = Table(qa_data, colWidths=[40, 100, 80, 65, 55, 40, 75])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a1a2e')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#d1d5db')),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f9fafb')]),
            ('TOPPADDING', (0, 0), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ]))
        story.append(t)
        story.append(Spacer(1, 3*mm))

        # Detailed QA notes per form
        for f in qa_forms:
            story.append(Paragraph(f'<b>{f.team.code} — {f.area_inspected}</b>', styles['SubHeader']))

            checks_data = [
                ['Check Item', 'Status'],
                ['Materials Correct', 'PASS' if f.materials_correct else 'FAIL'],
                ['Materials Stored Properly', 'PASS' if f.materials_stored_properly else 'FAIL'],
                ['Work to Method Statement', 'PASS' if f.work_to_method_statement else 'FAIL'],
                ['Work to Drawings', 'PASS' if f.work_to_drawings else 'FAIL'],
                ['Area Clean & Tidy', 'PASS' if f.area_clean_tidy else 'FAIL'],
                ['Waste Segregated', 'PASS' if f.waste_segregated else 'FAIL'],
                ['Barriers & Signage', 'PASS' if f.barriers_signage else 'FAIL'],
                ['PPE Compliant', 'PASS' if f.ppe_compliant else 'FAIL'],
                ['Existing Services Protected', 'PASS' if f.existing_services_protected else 'FAIL'],
                ['Completed Work Protected', 'PASS' if f.completed_work_protected else 'FAIL'],
            ]

            ct = Table(checks_data, colWidths=[200, 80])
            style_cmds = [
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#374151')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('FONTSIZE', (0, 0), (-1, -1), 8),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('ALIGN', (1, 0), (1, -1), 'CENTER'),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#d1d5db')),
                ('TOPPADDING', (0, 0), (-1, -1), 2),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
            ]
            # Color FAIL cells red
            for row_idx, row in enumerate(checks_data[1:], start=1):
                if row[1] == 'FAIL':
                    style_cmds.append(('TEXTCOLOR', (1, row_idx), (1, row_idx), colors.HexColor('#ef4444')))
                    style_cmds.append(('FONTNAME', (1, row_idx), (1, row_idx), 'Helvetica-Bold'))

            ct.setStyle(TableStyle(style_cmds))
            story.append(ct)

            if f.snags_identified:
                story.append(Paragraph(f'<b>Snags:</b> {f.snags_identified}', styles['ReportBody']))
            if f.inspector_comments:
                story.append(Paragraph(f'<b>Comments:</b> {f.inspector_comments}', styles['ReportBody']))
            if f.deviations:
                story.append(Paragraph(f'<b>Deviations:</b> {f.deviations}', styles['ReportBody']))

            story.append(Spacer(1, 3*mm))
    else:
        story.append(Paragraph('No QA inspection forms submitted for this date.', styles['ReportBody']))

    # ---- 4. INCIDENTS ----
    story.append(Paragraph('4. INCIDENTS & NEAR MISSES', styles['SectionHeader']))

    if incidents.exists():
        for inc in incidents:
            sev_colors = {'near_miss': '#f59e0b', 'minor': '#f59e0b', 'major': '#ef4444', 'serious': '#dc2626'}
            story.append(Paragraph(
                f'<b>[{inc.get_severity_display().upper()}]</b> {inc.title}',
                styles['ReportBody']
            ))
            story.append(Paragraph(
                f'Team: {inc.team.code if inc.team else "N/A"} | '
                f'Location: {inc.location} | '
                f'Time: {inc.reported_at.strftime("%H:%M")} | '
                f'Status: {"Resolved" if inc.is_resolved else "Open"}',
                styles['SmallText']
            ))
            story.append(Paragraph(inc.description, styles['ReportBody']))
            story.append(Spacer(1, 2*mm))
    else:
        story.append(Paragraph('No incidents reported during this shift.', styles['ReportBody']))

    # Near misses from briefing forms
    near_misses = briefing_forms.exclude(near_misses='')
    if near_misses.exists():
        story.append(Paragraph('Near Misses (from briefing forms):', styles['SubHeader']))
        for f in near_misses:
            story.append(Paragraph(f'<b>{f.team.code}:</b> {f.near_misses}', styles['ReportBody']))

    # ---- 5. OPEN NCRs ----
    story.append(Paragraph('5. OPEN NON-CONFORMANCE REPORTS', styles['SectionHeader']))

    if open_ncrs.exists():
        ncr_data = [['NCR #', 'Project', 'Title', 'Severity', 'Status', 'Due Date']]
        for ncr in open_ncrs:
            ncr_data.append([
                f'NCR-{ncr.id}',
                ncr.project.name[:20],
                ncr.title[:35],
                ncr.get_severity_display(),
                ncr.get_status_display(),
                ncr.due_date.strftime('%d/%m/%y') if ncr.due_date else '-',
            ])

        t = Table(ncr_data, colWidths=[45, 80, 120, 55, 75, 55])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a1a2e')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#d1d5db')),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f9fafb')]),
            ('TOPPADDING', (0, 0), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ]))
        story.append(t)
    else:
        story.append(Paragraph('No open NCRs at this time.', styles['ReportBody']))

    # ---- 6. HANDOVER NOTES ----
    if report and (report.key_issues or report.handover_notes):
        story.append(Paragraph('6. KEY ISSUES & HANDOVER', styles['SectionHeader']))
        if report.key_issues:
            story.append(Paragraph('<b>Key Issues:</b>', styles['SubHeader']))
            story.append(Paragraph(report.key_issues, styles['ReportBody']))
        if report.handover_notes:
            story.append(Paragraph('<b>Handover to Day Shift:</b>', styles['SubHeader']))
            story.append(Paragraph(report.handover_notes, styles['ReportBody']))

    # ---- FOOTER ----
    story.append(Spacer(1, 10*mm))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#d1d5db')))
    story.append(Spacer(1, 2*mm))
    story.append(Paragraph(
        f'Generated: {timezone.now().strftime("%d/%m/%Y %H:%M")} | '
        f'AtkinsRéalis Night Operations | Confidential',
        styles['SmallText']
    ))

    # Build PDF
    doc.build(story)
    buffer.seek(0)

    filename = f'NightOps_Report_{date.strftime("%Y-%m-%d")}.pdf'
    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response


def _pdf_styles():
    """Shared PDF styles for all report types."""
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib import colors
    from reportlab.lib.units import mm

    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(
        'ReportTitle', parent=styles['Title'],
        fontSize=22, spaceAfter=4*mm, textColor=colors.HexColor('#1a1a2e'),
    ))
    styles.add(ParagraphStyle(
        'SectionHeader', parent=styles['Heading1'],
        fontSize=14, spaceAfter=3*mm, spaceBefore=6*mm,
        textColor=colors.HexColor('#1a1a2e'),
    ))
    styles.add(ParagraphStyle(
        'SubHeader', parent=styles['Heading2'],
        fontSize=11, spaceAfter=2*mm, spaceBefore=4*mm,
        textColor=colors.HexColor('#374151'),
    ))
    styles.add(ParagraphStyle(
        'ReportBody', parent=styles['Normal'],
        fontSize=9, spaceAfter=2*mm, leading=13,
    ))
    styles.add(ParagraphStyle(
        'SmallText', parent=styles['Normal'],
        fontSize=8, textColor=colors.HexColor('#6b7280'),
    ))
    return styles


def _pdf_header_table(data, col_widths):
    """Create a standard styled table with dark header."""
    from reportlab.lib import colors
    from reportlab.platypus import Table, TableStyle

    t = Table(data, colWidths=col_widths)
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a1a2e')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#d1d5db')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f9fafb')]),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
    ]))
    return t


def briefing_pdf(request, date_str):
    """Generate PDF with all pre-briefing forms for a given date."""
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.units import mm, cm
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, HRFlowable

    date = datetime.strptime(date_str, '%Y-%m-%d').date()
    styles = _pdf_styles()

    briefing_forms = PreBriefingForm.objects.filter(shift_date=date).select_related('team', 'submitted_by').order_by('team__code')
    teams_total = Team.objects.filter(is_active=True).count()

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        leftMargin=1.5*cm, rightMargin=1.5*cm,
        topMargin=2*cm, bottomMargin=2*cm,
    )

    story = []

    # Header
    story.append(Paragraph('NIGHT BRIEFING REPORT', styles['ReportTitle']))
    story.append(Paragraph('AtkinsRéalis — Heathrow Infrastructure Programme', styles['ReportBody']))
    story.append(Paragraph(f'Date: {date.strftime("%A, %d %B %Y")} | Shift: Night', styles['ReportBody']))
    story.append(Paragraph(f'Teams Submitted: {briefing_forms.count()} / {teams_total}', styles['ReportBody']))
    story.append(Spacer(1, 4*mm))
    story.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor('#fbbf24')))
    story.append(Spacer(1, 4*mm))

    if not briefing_forms.exists():
        story.append(Paragraph('No briefing forms submitted for this date.', styles['ReportBody']))
    else:
        # Summary table
        total_present = sum(f.staff_present for f in briefing_forms)
        total_expected = sum(f.staff_expected for f in briefing_forms)
        risk_g = briefing_forms.filter(risk_rating='green').count()
        risk_a = briefing_forms.filter(risk_rating='amber').count()
        risk_r = briefing_forms.filter(risk_rating='red').count()

        story.append(Paragraph('SUMMARY', styles['SectionHeader']))
        summary_data = [
            ['Metric', 'Value'],
            ['Teams Submitted', f'{briefing_forms.count()} / {teams_total}'],
            ['Total Staff Present', f'{total_present} / {total_expected}'],
            ['Risk Distribution', f'Green: {risk_g}  |  Amber: {risk_a}  |  Red: {risk_r}'],
        ]
        story.append(_pdf_header_table(summary_data, [150, 320]))
        story.append(Spacer(1, 4*mm))

        # Overview table
        story.append(Paragraph('ALL TEAMS OVERVIEW', styles['SectionHeader']))
        overview_data = [['Team', 'Staff', 'Equipment', 'PPE', 'Permits', 'Risk', 'Time']]
        for f in briefing_forms:
            equip_map = {'all_ok': 'OK', 'minor_issues': 'Minor', 'major_issues': 'MAJOR', 'critical': 'CRITICAL'}
            overview_data.append([
                f.team.code,
                f'{f.staff_present}/{f.staff_expected}',
                equip_map.get(f.equipment_status, f.equipment_status),
                'Yes' if f.ppe_check_completed else 'NO',
                'Yes' if f.permits_in_place else 'NO',
                f.risk_rating.upper(),
                f.submitted_at.strftime('%H:%M'),
            ])
        story.append(_pdf_header_table(overview_data, [50, 55, 65, 40, 50, 50, 55]))
        story.append(Spacer(1, 4*mm))

        # Safety concerns
        concerns = briefing_forms.exclude(safety_concerns='')
        if concerns.exists():
            story.append(Paragraph('SAFETY CONCERNS', styles['SectionHeader']))
            for f in concerns:
                story.append(Paragraph(f'<b>{f.team.code} ({f.team.name}):</b> {f.safety_concerns}', styles['ReportBody']))

        # Near misses
        near_misses = briefing_forms.exclude(near_misses='')
        if near_misses.exists():
            story.append(Paragraph('NEAR MISSES REPORTED', styles['SectionHeader']))
            for f in near_misses:
                story.append(Paragraph(f'<b>{f.team.code}:</b> {f.near_misses}', styles['ReportBody']))

        # Detailed per-team forms
        story.append(PageBreak())
        story.append(Paragraph('DETAILED TEAM SUBMISSIONS', styles['SectionHeader']))

        for f in briefing_forms:
            story.append(Paragraph(f'{f.team.code} — {f.team.name}', styles['SubHeader']))

            detail_data = [
                ['Field', 'Value'],
                ['Submitted By', f.submitted_by.get_full_name() if f.submitted_by else 'N/A'],
                ['Submitted At', f.submitted_at.strftime('%H:%M')],
                ['Staff Present / Expected', f'{f.staff_present} / {f.staff_expected}'],
                ['Absentees', f.absentees or 'None'],
                ['Equipment Status', f.get_equipment_status_display()],
                ['Equipment Notes', f.equipment_notes or 'None'],
                ['PPE Check Completed', 'Yes' if f.ppe_check_completed else 'NO'],
                ['Safety Concerns', f.safety_concerns or 'None'],
                ['Near Misses', f.near_misses or 'None'],
                ['Planned Tasks Tonight', f.planned_tasks_tonight or '-'],
                ['Pending Tasks from Previous', f.pending_tasks_from_previous or '-'],
                ['Blockers', f.blockers or 'None'],
                ['Materials Needed', f.materials_needed or 'None'],
                ['Permits in Place', 'Yes' if f.permits_in_place else 'NO'],
                ['Permit Details', f.permit_details or '-'],
                ['Method Statements Reviewed', 'Yes' if f.method_statements_reviewed else 'No'],
                ['Weather Impact', f.get_weather_impact_display()],
                ['Weather Notes', f.weather_notes or '-'],
                ['Risk Rating', f.risk_rating.upper()],
                ['Additional Notes', f.additional_notes or '-'],
            ]

            t = Table(detail_data, colWidths=[150, 320])
            style_cmds = [
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#374151')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('FONTSIZE', (0, 0), (-1, -1), 8),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
                ('ALIGN', (0, 0), (0, -1), 'LEFT'),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#d1d5db')),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f9fafb')]),
                ('TOPPADDING', (0, 0), (-1, -1), 3),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
                ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ]

            # Highlight risk rows
            risk_row = len(detail_data) - 2  # 'Risk Rating' row
            if f.risk_rating == 'red':
                style_cmds.append(('TEXTCOLOR', (1, risk_row), (1, risk_row), colors.HexColor('#ef4444')))
                style_cmds.append(('FONTNAME', (1, risk_row), (1, risk_row), 'Helvetica-Bold'))
            elif f.risk_rating == 'amber':
                style_cmds.append(('TEXTCOLOR', (1, risk_row), (1, risk_row), colors.HexColor('#f59e0b')))

            t.setStyle(TableStyle(style_cmds))
            story.append(t)
            story.append(Spacer(1, 6*mm))

    # Footer
    story.append(Spacer(1, 10*mm))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#d1d5db')))
    story.append(Paragraph(
        f'Generated: {timezone.now().strftime("%d/%m/%Y %H:%M")} | AtkinsRéalis Night Operations | Confidential',
        styles['SmallText']
    ))

    doc.build(story)
    buffer.seek(0)

    filename = f'NightBriefing_{date.strftime("%Y-%m-%d")}.pdf'
    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response


def qa_pdf(request, date_str):
    """Generate PDF with all QA checklist forms for a given date."""
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.units import mm, cm
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, HRFlowable

    date = datetime.strptime(date_str, '%Y-%m-%d').date()
    styles = _pdf_styles()

    qa_forms = QAChecklistForm.objects.filter(shift_date=date).select_related('team', 'project', 'submitted_by').order_by('team__code')

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        leftMargin=1.5*cm, rightMargin=1.5*cm,
        topMargin=2*cm, bottomMargin=2*cm,
    )

    story = []

    # Header
    story.append(Paragraph('QA INSPECTION REPORT', styles['ReportTitle']))
    story.append(Paragraph('AtkinsRéalis — Heathrow Infrastructure Programme', styles['ReportBody']))
    story.append(Paragraph(f'Date: {date.strftime("%A, %d %B %Y")} | Shift: Night', styles['ReportBody']))
    story.append(Paragraph(f'Total Inspections: {qa_forms.count()}', styles['ReportBody']))
    story.append(Spacer(1, 4*mm))
    story.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor('#fbbf24')))
    story.append(Spacer(1, 4*mm))

    if not qa_forms.exists():
        story.append(Paragraph('No QA inspection forms submitted for this date.', styles['ReportBody']))
    else:
        # Summary stats
        approved = qa_forms.filter(overall_outcome='approved').count()
        conditional = qa_forms.filter(overall_outcome='conditional').count()
        rework = qa_forms.filter(overall_outcome='rework').count()
        rejected = qa_forms.filter(overall_outcome='rejected').count()
        avg_compliance = round(sum(f.compliance_percentage for f in qa_forms) / qa_forms.count())

        story.append(Paragraph('SUMMARY', styles['SectionHeader']))
        summary_data = [
            ['Metric', 'Value'],
            ['Total Inspections', str(qa_forms.count())],
            ['Approved', str(approved)],
            ['Conditional Approval', str(conditional)],
            ['Rework Required', str(rework)],
            ['Rejected', str(rejected)],
            ['Average Compliance', f'{avg_compliance}%'],
        ]
        story.append(_pdf_header_table(summary_data, [150, 320]))
        story.append(Spacer(1, 4*mm))

        # Overview table
        story.append(Paragraph('ALL INSPECTIONS OVERVIEW', styles['SectionHeader']))
        overview_data = [['Team', 'Area Inspected', 'Project', 'Workmanship', 'Compliance', 'Snags', 'Outcome']]
        for f in qa_forms:
            overview_data.append([
                f.team.code,
                f.area_inspected[:30],
                f.project.name[:20] if f.project else '-',
                f.get_workmanship_quality_display(),
                f'{f.compliance_percentage}%',
                str(f.snags_count),
                f.get_overall_outcome_display(),
            ])
        story.append(_pdf_header_table(overview_data, [40, 100, 80, 65, 55, 40, 75]))

        # Detailed per-form reports
        story.append(PageBreak())
        story.append(Paragraph('DETAILED INSPECTION REPORTS', styles['SectionHeader']))

        for f in qa_forms:
            story.append(Paragraph(
                f'{f.team.code} — {f.area_inspected}',
                styles['SubHeader']
            ))
            if f.project:
                story.append(Paragraph(f'Project: {f.project.name}', styles['SmallText']))

            # Checklist table
            checks_data = [
                ['Check Item', 'Status'],
                ['Materials Correct', 'PASS' if f.materials_correct else 'FAIL'],
                ['Materials Stored Properly', 'PASS' if f.materials_stored_properly else 'FAIL'],
                ['Work to Method Statement', 'PASS' if f.work_to_method_statement else 'FAIL'],
                ['Work to Drawings', 'PASS' if f.work_to_drawings else 'FAIL'],
                ['Area Clean & Tidy', 'PASS' if f.area_clean_tidy else 'FAIL'],
                ['Waste Segregated', 'PASS' if f.waste_segregated else 'FAIL'],
                ['Barriers & Signage', 'PASS' if f.barriers_signage else 'FAIL'],
                ['PPE Compliant', 'PASS' if f.ppe_compliant else 'FAIL'],
                ['Existing Services Protected', 'PASS' if f.existing_services_protected else 'FAIL'],
                ['Completed Work Protected', 'PASS' if f.completed_work_protected else 'FAIL'],
            ]

            ct = Table(checks_data, colWidths=[200, 80])
            style_cmds = [
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#374151')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('FONTSIZE', (0, 0), (-1, -1), 8),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('ALIGN', (1, 0), (1, -1), 'CENTER'),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#d1d5db')),
                ('TOPPADDING', (0, 0), (-1, -1), 2),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
            ]
            for row_idx, row in enumerate(checks_data[1:], start=1):
                if row[1] == 'FAIL':
                    style_cmds.append(('TEXTCOLOR', (1, row_idx), (1, row_idx), colors.HexColor('#ef4444')))
                    style_cmds.append(('FONTNAME', (1, row_idx), (1, row_idx), 'Helvetica-Bold'))
                else:
                    style_cmds.append(('TEXTCOLOR', (1, row_idx), (1, row_idx), colors.HexColor('#22c55e')))

            ct.setStyle(TableStyle(style_cmds))
            story.append(ct)
            story.append(Spacer(1, 2*mm))

            # Additional info
            info_data = [
                ['Field', 'Value'],
                ['Workmanship Quality', f.get_workmanship_quality_display()],
                ['Overall Outcome', f.get_overall_outcome_display()],
                ['Compliance', f'{f.compliance_percentage}% ({f.pass_count}/{f.total_checks} checks passed)'],
                ['Snags Count', str(f.snags_count)],
            ]
            if f.snags_identified:
                info_data.append(['Snags Identified', f.snags_identified[:200]])
            if f.deviations:
                info_data.append(['Deviations', f.deviations[:200]])
            if f.inspector_comments:
                info_data.append(['Inspector Comments', f.inspector_comments[:200]])
            if f.workmanship_notes:
                info_data.append(['Workmanship Notes', f.workmanship_notes[:200]])
            if f.materials_notes:
                info_data.append(['Materials Notes', f.materials_notes[:200]])
            if f.housekeeping_notes:
                info_data.append(['Housekeeping Notes', f.housekeeping_notes[:200]])
            if f.protection_notes:
                info_data.append(['Protection Notes', f.protection_notes[:200]])
            if f.follow_up_required:
                info_data.append(['Follow-Up Required', f.follow_up_details or 'Yes'])

            info_data.append(['Submitted By', f.submitted_by.get_full_name() if f.submitted_by else 'N/A'])
            info_data.append(['Submitted At', f.submitted_at.strftime('%H:%M %d/%m/%Y')])

            it = Table(info_data, colWidths=[150, 320])
            it.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#374151')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('FONTSIZE', (0, 0), (-1, -1), 8),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#d1d5db')),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f9fafb')]),
                ('TOPPADDING', (0, 0), (-1, -1), 3),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
                ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ]))
            story.append(it)
            story.append(Spacer(1, 8*mm))

    # Footer
    story.append(Spacer(1, 10*mm))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#d1d5db')))
    story.append(Paragraph(
        f'Generated: {timezone.now().strftime("%d/%m/%Y %H:%M")} | AtkinsRéalis Night Operations | Confidential',
        styles['SmallText']
    ))

    doc.build(story)
    buffer.seek(0)

    filename = f'QA_Report_{date.strftime("%Y-%m-%d")}.pdf'
    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response


def incidents_pdf(request, date_str):
    """Generate PDF with all incidents for a given date."""
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.units import mm, cm
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable

    date = datetime.strptime(date_str, '%Y-%m-%d').date()
    styles = _pdf_styles()

    incidents = IncidentReport.objects.filter(reported_at__date=date).select_related('team', 'reported_by')

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        leftMargin=1.5*cm, rightMargin=1.5*cm,
        topMargin=2*cm, bottomMargin=2*cm,
    )

    story = []

    # Header
    story.append(Paragraph('INCIDENT & NEAR MISS REPORT', styles['ReportTitle']))
    story.append(Paragraph('AtkinsRéalis — Heathrow Infrastructure Programme', styles['ReportBody']))
    story.append(Paragraph(f'Date: {date.strftime("%A, %d %B %Y")} | Shift: Night', styles['ReportBody']))
    story.append(Paragraph(f'Total Incidents: {incidents.count()}', styles['ReportBody']))
    story.append(Spacer(1, 4*mm))
    story.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor('#fbbf24')))
    story.append(Spacer(1, 6*mm))

    if not incidents.exists():
        story.append(Paragraph('No incidents or near misses reported for this date.', styles['ReportBody']))
    else:
        for inc in incidents:
            sev_text = inc.get_severity_display().upper()
            story.append(Paragraph(f'[{sev_text}] {inc.title}', styles['SubHeader']))

            detail_data = [
                ['Field', 'Value'],
                ['Severity', sev_text],
                ['Team', f'{inc.team.code} — {inc.team.name}' if inc.team else 'N/A'],
                ['Reported By', inc.reported_by.get_full_name() if inc.reported_by else 'N/A'],
                ['Location', inc.location],
                ['Time Reported', inc.reported_at.strftime('%H:%M %d/%m/%Y')],
                ['Status', 'Resolved' if inc.is_resolved else 'OPEN'],
                ['Description', inc.description[:400]],
                ['Immediate Action Taken', inc.immediate_action[:400] if inc.immediate_action else 'None recorded'],
            ]

            t = Table(detail_data, colWidths=[150, 320])
            style_cmds = [
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#374151')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('FONTSIZE', (0, 0), (-1, -1), 8),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#d1d5db')),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f9fafb')]),
                ('TOPPADDING', (0, 0), (-1, -1), 3),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
                ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ]

            # Red highlight for severity
            if inc.severity in ('major', 'serious'):
                style_cmds.append(('TEXTCOLOR', (1, 1), (1, 1), colors.HexColor('#ef4444')))
                style_cmds.append(('FONTNAME', (1, 1), (1, 1), 'Helvetica-Bold'))

            t.setStyle(TableStyle(style_cmds))
            story.append(t)
            story.append(Spacer(1, 8*mm))

    # Footer
    story.append(Spacer(1, 10*mm))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#d1d5db')))
    story.append(Paragraph(
        f'Generated: {timezone.now().strftime("%d/%m/%Y %H:%M")} | AtkinsRéalis Night Operations | Confidential',
        styles['SmallText']
    ))

    doc.build(story)
    buffer.seek(0)

    filename = f'Incidents_Report_{date.strftime("%Y-%m-%d")}.pdf'
    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response

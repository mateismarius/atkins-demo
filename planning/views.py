import io
from datetime import datetime, timedelta
from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone
from django.http import HttpResponse
from django.contrib import messages
from .models import ShiftPlan, ShiftAssignment, Resource
from .forms import ShiftPlanForm, ShiftAssignmentForm
from core.models import Team


def planning_dashboard(request):
    today = timezone.now().date()

    # This week's plans
    week_start = today - timedelta(days=today.weekday())
    week_end = week_start + timedelta(days=6)
    week_plans = ShiftPlan.objects.filter(
        date__gte=week_start, date__lte=week_end
    ).prefetch_related('assignments__team')

    # Calendar data
    calendar_data = []
    for i in range(7):
        day = week_start + timedelta(days=i)
        plan = week_plans.filter(date=day).first()
        assignments = plan.assignments.all() if plan else []
        completed = [a for a in assignments if a.status == 'completed']
        critical = [a for a in assignments if a.priority == 'critical']
        calendar_data.append({
            'date': day,
            'plan': plan,
            'assignments': assignments,
            'is_today': day == today,
            'completed_count': len(completed),
            'critical_count': len(critical),
        })

    # Tonight's plan
    tonight_plan = ShiftPlan.objects.filter(date=today, shift='night').first()
    tonight_assignments = tonight_plan.assignments.select_related('team').all() if tonight_plan else []

    # Assignment stats for tonight
    tonight_stats = {
        'total': tonight_assignments.count(),
        'completed': tonight_assignments.filter(status='completed').count(),
        'in_progress': tonight_assignments.filter(status='in_progress').count(),
        'planned': tonight_assignments.filter(status='planned').count(),
        'deferred': tonight_assignments.filter(status='deferred').count(),
        'total_est_hours': sum(a.estimated_hours for a in tonight_assignments),
        'total_actual_hours': sum(a.actual_hours or 0 for a in tonight_assignments),
        'critical_count': tonight_assignments.filter(priority='critical').count(),
        'high_count': tonight_assignments.filter(priority='high').count(),
    }

    # Resources
    resources = Resource.objects.all()
    resource_stats = {
        'available': resources.filter(status='available').count(),
        'in_use': resources.filter(status='in_use').count(),
        'maintenance': resources.filter(status='maintenance').count(),
        'total': resources.count(),
    }

    # Teams
    teams = Team.objects.filter(is_active=True)

    # Recent plans
    recent_plans = ShiftPlan.objects.all()[:14]

    return render(request, 'planning/dashboard.html', {
        'calendar_data': calendar_data,
        'tonight_plan': tonight_plan,
        'tonight_assignments': tonight_assignments,
        'tonight_stats': tonight_stats,
        'resources': resources,
        'resource_stats': resource_stats,
        'teams': teams,
        'today': today,
        'week_start': week_start,
        'week_end': week_end,
        'recent_plans': recent_plans,
    })


def shift_plan_detail(request, pk):
    plan = get_object_or_404(ShiftPlan, pk=pk)
    assignments = plan.assignments.select_related('team').all()

    stats = {
        'total': assignments.count(),
        'completed': assignments.filter(status='completed').count(),
        'in_progress': assignments.filter(status='in_progress').count(),
        'planned': assignments.filter(status='planned').count(),
        'deferred': assignments.filter(status='deferred').count(),
        'total_est_hours': sum(a.estimated_hours for a in assignments),
        'total_actual_hours': sum(a.actual_hours or 0 for a in assignments),
    }

    # Group by priority
    by_priority = {
        'critical': assignments.filter(priority='critical'),
        'high': assignments.filter(priority='high'),
        'normal': assignments.filter(priority='normal'),
        'low': assignments.filter(priority='low'),
    }

    return render(request, 'planning/plan_detail.html', {
        'plan': plan, 'assignments': assignments,
        'stats': stats, 'by_priority': by_priority,
    })


def create_plan(request):
    today = timezone.now().date()

    if request.method == 'POST':
        form = ShiftPlanForm(request.POST)
        if form.is_valid():
            plan = form.save(commit=False)
            plan.created_by = request.user if request.user.is_authenticated else None
            plan.save()
            messages.success(request, f'Shift plan for {plan.date} created!')
            return redirect('planning:plan_detail', pk=plan.pk)
    else:
        tomorrow = today + timedelta(days=1)
        form = ShiftPlanForm(initial={'date': tomorrow, 'shift': 'night'})

    return render(request, 'planning/create_plan.html', {
        'form': form, 'today': today,
    })


def copy_plan(request, pk):
    source_plan = get_object_or_404(ShiftPlan, pk=pk)
    source_assignments = source_plan.assignments.select_related('team').all()

    if request.method == 'POST':
        new_date_str = request.POST.get('new_date')
        if new_date_str:
            new_date = datetime.strptime(new_date_str, '%Y-%m-%d').date()

            existing = ShiftPlan.objects.filter(date=new_date, shift=source_plan.shift).first()
            if existing:
                messages.error(request, f'A {source_plan.shift} plan already exists for {new_date}.')
                return redirect('planning:plan_detail', pk=pk)

            new_plan = ShiftPlan.objects.create(
                date=new_date,
                shift=source_plan.shift,
                created_by=request.user if request.user.is_authenticated else None,
                notes=f'Copied from {source_plan.date}. {source_plan.notes}',
            )

            for a in source_assignments:
                ShiftAssignment.objects.create(
                    plan=new_plan,
                    team=a.team,
                    area=a.area,
                    task_description=a.task_description,
                    priority=a.priority,
                    estimated_hours=a.estimated_hours,
                    status='planned',
                    notes=a.notes,
                )

            messages.success(request, f'Plan copied to {new_date} with {source_assignments.count()} assignments!')
            return redirect('planning:plan_detail', pk=new_plan.pk)

    return render(request, 'planning/copy_plan.html', {
        'source_plan': source_plan,
        'source_assignments': source_assignments,
    })


def add_assignment(request, plan_pk):
    plan = get_object_or_404(ShiftPlan, pk=plan_pk)

    if request.method == 'POST':
        form = ShiftAssignmentForm(request.POST)
        if form.is_valid():
            assignment = form.save(commit=False)
            assignment.plan = plan
            assignment.save()
            messages.success(request, f'Assignment added for {assignment.team.code}!')
            return redirect('planning:plan_detail', pk=plan.pk)
    else:
        form = ShiftAssignmentForm()

    return render(request, 'planning/assignment_form.html', {
        'form': form, 'plan': plan, 'editing': False,
    })


def edit_assignment(request, pk):
    assignment = get_object_or_404(ShiftAssignment, pk=pk)

    if request.method == 'POST':
        form = ShiftAssignmentForm(request.POST, instance=assignment)
        if form.is_valid():
            form.save()
            messages.success(request, f'Assignment updated for {assignment.team.code}!')
            return redirect('planning:plan_detail', pk=assignment.plan.pk)
    else:
        form = ShiftAssignmentForm(instance=assignment)

    return render(request, 'planning/assignment_form.html', {
        'form': form, 'plan': assignment.plan, 'assignment': assignment, 'editing': True,
    })


def delete_assignment(request, pk):
    assignment = get_object_or_404(ShiftAssignment, pk=pk)
    plan_pk = assignment.plan.pk

    if request.method == 'POST':
        team_code = assignment.team.code
        assignment.delete()
        messages.success(request, f'Assignment for {team_code} deleted.')
        return redirect('planning:plan_detail', pk=plan_pk)

    return render(request, 'planning/confirm_delete.html', {
        'assignment': assignment,
    })


def update_assignment_status(request, pk):
    assignment = get_object_or_404(ShiftAssignment, pk=pk)

    if request.method == 'POST':
        new_status = request.POST.get('status')
        actual_hours = request.POST.get('actual_hours')
        if new_status:
            assignment.status = new_status
        if actual_hours:
            try:
                assignment.actual_hours = float(actual_hours)
            except ValueError:
                pass
        assignment.save()
        messages.success(request, f'{assignment.team.code} → {assignment.get_status_display()}')

    return redirect('planning:plan_detail', pk=assignment.plan.pk)


def toggle_publish(request, pk):
    plan = get_object_or_404(ShiftPlan, pk=pk)
    if request.method == 'POST':
        plan.is_published = not plan.is_published
        plan.save()
        status = 'published' if plan.is_published else 'unpublished'
        messages.success(request, f'Plan {status}!')
    return redirect('planning:plan_detail', pk=plan.pk)


def resource_list(request):
    type_filter = request.GET.get('type', '')
    resources = Resource.objects.select_related('assigned_to').all()
    if type_filter:
        resources = resources.filter(resource_type=type_filter)
    return render(request, 'planning/resources.html', {
        'resources': resources, 'current_filter': type_filter,
    })


def plan_pdf(request, pk):
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import mm, cm
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable

    plan = get_object_or_404(ShiftPlan, pk=pk)
    assignments = plan.assignments.select_related('team').all()

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, leftMargin=1.5*cm, rightMargin=1.5*cm, topMargin=2*cm, bottomMargin=2*cm)

    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle('ReportTitle', parent=styles['Title'], fontSize=22, spaceAfter=4*mm, textColor=colors.HexColor('#1a1a2e')))
    styles.add(ParagraphStyle('SectionHeader', parent=styles['Heading1'], fontSize=14, spaceAfter=3*mm, spaceBefore=6*mm, textColor=colors.HexColor('#1a1a2e')))
    styles.add(ParagraphStyle('SubHeader', parent=styles['Heading2'], fontSize=11, spaceAfter=2*mm, spaceBefore=4*mm, textColor=colors.HexColor('#374151')))
    styles.add(ParagraphStyle('Body', parent=styles['Normal'], fontSize=9, spaceAfter=2*mm, leading=13))
    styles.add(ParagraphStyle('SmallText', parent=styles['Normal'], fontSize=8, textColor=colors.HexColor('#6b7280')))

    story = []

    # Header
    story.append(Paragraph('SHIFT PLAN', styles['ReportTitle']))
    story.append(Paragraph('AtkinsRéalis — Heathrow Infrastructure Programme', styles['Body']))
    story.append(Paragraph(f'Date: {plan.date.strftime("%A, %d %B %Y")} | Shift: {plan.get_shift_display()}', styles['Body']))
    story.append(Paragraph(f'Status: {"PUBLISHED" if plan.is_published else "DRAFT"} | Assignments: {assignments.count()}', styles['Body']))
    story.append(Spacer(1, 4*mm))
    story.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor('#fbbf24')))
    story.append(Spacer(1, 4*mm))

    # Summary
    total_est = sum(a.estimated_hours for a in assignments)
    total_act = sum(a.actual_hours or 0 for a in assignments)

    story.append(Paragraph('SUMMARY', styles['SectionHeader']))
    summary_data = [
        ['Metric', 'Value'],
        ['Total Assignments', str(assignments.count())],
        ['Completed', str(assignments.filter(status='completed').count())],
        ['Estimated Hours', f'{total_est}h'],
        ['Actual Hours', f'{total_act}h'],
        ['Critical Tasks', str(assignments.filter(priority='critical').count())],
        ['High Priority', str(assignments.filter(priority='high').count())],
    ]
    t = Table(summary_data, colWidths=[150, 320])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a1a2e')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#d1d5db')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f9fafb')]),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(t)
    story.append(Spacer(1, 4*mm))

    # Assignments table
    story.append(Paragraph('ASSIGNMENTS', styles['SectionHeader']))
    assign_data = [['Team', 'Area', 'Task', 'Priority', 'Est.', 'Status']]
    for a in assignments:
        assign_data.append([
            a.team.code,
            a.area[:25],
            a.task_description[:40],
            a.get_priority_display(),
            f'{a.estimated_hours}h',
            a.get_status_display(),
        ])

    t = Table(assign_data, colWidths=[40, 90, 155, 55, 40, 70])
    style_cmds = [
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a1a2e')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('ALIGN', (2, 1), (2, -1), 'LEFT'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#d1d5db')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f9fafb')]),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
    ]
    for row_idx, a in enumerate(assignments, start=1):
        if a.priority == 'critical':
            style_cmds.append(('TEXTCOLOR', (3, row_idx), (3, row_idx), colors.HexColor('#ef4444')))
            style_cmds.append(('FONTNAME', (3, row_idx), (3, row_idx), 'Helvetica-Bold'))
        elif a.priority == 'high':
            style_cmds.append(('TEXTCOLOR', (3, row_idx), (3, row_idx), colors.HexColor('#f59e0b')))
    t.setStyle(TableStyle(style_cmds))
    story.append(t)
    story.append(Spacer(1, 4*mm))

    # Detailed assignments
    story.append(Paragraph('DETAILED ASSIGNMENTS', styles['SectionHeader']))
    for a in assignments:
        story.append(Paragraph(f'<b>{a.team.code} — {a.team.name}</b> | {a.area}', styles['SubHeader']))
        story.append(Paragraph(f'Task: {a.task_description}', styles['Body']))
        story.append(Paragraph(
            f'Priority: {a.get_priority_display()} | Est: {a.estimated_hours}h | '
            f'Actual: {a.actual_hours or "—"}h | Status: {a.get_status_display()}',
            styles['SmallText']
        ))
        if a.notes:
            story.append(Paragraph(f'Notes: {a.notes}', styles['SmallText']))
        story.append(Spacer(1, 3*mm))

    if plan.notes:
        story.append(Paragraph('PLAN NOTES', styles['SectionHeader']))
        story.append(Paragraph(plan.notes, styles['Body']))

    # Footer
    story.append(Spacer(1, 10*mm))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#d1d5db')))
    story.append(Paragraph(
        f'Generated: {timezone.now().strftime("%d/%m/%Y %H:%M")} | AtkinsRéalis Night Operations | Confidential',
        styles['SmallText']
    ))

    doc.build(story)
    buffer.seek(0)

    filename = f'ShiftPlan_{plan.date.strftime("%Y-%m-%d")}_{plan.shift}.pdf'
    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response

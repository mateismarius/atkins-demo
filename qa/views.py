from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone
from django.contrib import messages
from .models import Inspection, NonConformance, QAChecklistForm
from .forms import QAChecklistFormForm


def qa_dashboard(request):
    today = timezone.now().date()
    inspections = Inspection.objects.select_related('project', 'inspector')[:20]
    ncrs = NonConformance.objects.select_related('project', 'raised_by', 'assigned_to')[:20]

    # QA checklists for today
    qa_forms_today = QAChecklistForm.objects.filter(shift_date=today).select_related('team', 'project')

    stats = {
        'total_inspections': Inspection.objects.count(),
        'completed_inspections': Inspection.objects.filter(status='completed').count(),
        'failed_inspections': Inspection.objects.filter(status='failed').count(),
        'avg_score': Inspection.objects.filter(status='completed').values_list('score', flat=True),
        'open_ncrs': NonConformance.objects.exclude(status='closed').count(),
        'critical_ncrs': NonConformance.objects.filter(severity='critical').exclude(status='closed').count(),
        'qa_forms_today': qa_forms_today.count(),
        'qa_approved_today': qa_forms_today.filter(overall_outcome='approved').count(),
        'qa_rework_today': qa_forms_today.filter(overall_outcome__in=['rework', 'rejected']).count(),
    }

    scores = list(stats['avg_score'])
    stats['avg_score'] = round(sum(scores) / len(scores)) if scores else 0

    return render(request, 'qa/dashboard.html', {
        'inspections': inspections, 'ncrs': ncrs, 'stats': stats,
        'qa_forms_today': qa_forms_today, 'today': today,
    })


def qa_checklist_create(request):
    today = timezone.now().date()
    if request.method == 'POST':
        form = QAChecklistFormForm(request.POST)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.submitted_by = request.user if request.user.is_authenticated else None
            obj.save()
            messages.success(request, f'QA checklist submitted for {obj.team.name} - {obj.area_inspected}!')
            return redirect('qa:dashboard')
    else:
        form = QAChecklistFormForm(initial={'shift_date': today})

    return render(request, 'qa/checklist_form.html', {
        'form': form, 'today': today,
    })


def qa_checklist_detail(request, pk):
    qa_form = get_object_or_404(QAChecklistForm, pk=pk)
    return render(request, 'qa/checklist_detail.html', {'qa_form': qa_form})


def inspection_detail(request, pk):
    inspection = get_object_or_404(Inspection, pk=pk)
    items = inspection.items.all()
    compliant = items.filter(is_compliant=True).count()
    total = items.count()
    return render(request, 'qa/inspection_detail.html', {
        'inspection': inspection, 'items': items,
        'compliant': compliant, 'total': total,
    })


def ncr_list(request):
    status_filter = request.GET.get('status', '')
    ncrs = NonConformance.objects.select_related('project', 'raised_by', 'assigned_to')
    if status_filter:
        ncrs = ncrs.filter(status=status_filter)
    return render(request, 'qa/ncr_list.html', {'ncrs': ncrs, 'current_filter': status_filter})

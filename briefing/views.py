from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone
from django.contrib import messages
from .models import PreBriefingForm, NightBriefing, BriefingActionItem
from .forms import PreBriefingFormForm
from core.models import Team


def briefing_dashboard(request):
    today = timezone.now().date()
    tonight_briefing = NightBriefing.objects.filter(date=today).first()

    # Forms status for tonight
    teams = Team.objects.filter(is_active=True)
    forms_today = PreBriefingForm.objects.filter(shift_date=today).select_related('team', 'submitted_by')
    submitted_team_ids = forms_today.values_list('team_id', flat=True)

    teams_status = []
    for team in teams:
        form = forms_today.filter(team=team).first()
        teams_status.append({
            'team': team,
            'submitted': team.id in submitted_team_ids,
            'form': form,
        })

    forms_count = forms_today.count()
    total_teams = teams.count()
    all_submitted = forms_count >= total_teams

    # Risk summary
    risk_counts = {
        'green': forms_today.filter(risk_rating='green').count(),
        'amber': forms_today.filter(risk_rating='amber').count(),
        'red': forms_today.filter(risk_rating='red').count(),
    }

    # Safety concerns
    safety_concerns = forms_today.exclude(safety_concerns='').values_list(
        'team__code', 'safety_concerns'
    )

    # Recent briefings
    recent_briefings = NightBriefing.objects.all()[:7]

    # Action items
    pending_actions = BriefingActionItem.objects.exclude(status='done').select_related('assigned_to', 'team')[:10]

    return render(request, 'briefing/dashboard.html', {
        'tonight_briefing': tonight_briefing,
        'teams_status': teams_status,
        'forms_count': forms_count,
        'total_teams': total_teams,
        'all_submitted': all_submitted,
        'risk_counts': risk_counts,
        'safety_concerns': safety_concerns,
        'recent_briefings': recent_briefings,
        'pending_actions': pending_actions,
        'today': today,
    })


def prebriefing_form_create(request):
    today = timezone.now().date()
    if request.method == 'POST':
        form = PreBriefingFormForm(request.POST)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.submitted_by = request.user if request.user.is_authenticated else None
            obj.save()
            messages.success(request, f'Pre-briefing form submitted for {obj.team.name}!')
            return redirect('briefing:dashboard')
    else:
        form = PreBriefingFormForm(initial={'shift_date': today})

    return render(request, 'briefing/prebriefing_form.html', {
        'form': form, 'today': today,
    })


def prebriefing_form_detail(request, pk):
    form_obj = get_object_or_404(PreBriefingForm, pk=pk)
    return render(request, 'briefing/prebriefing_detail.html', {'form_obj': form_obj})


def briefing_detail(request, pk):
    briefing = get_object_or_404(NightBriefing, pk=pk)
    forms = PreBriefingForm.objects.filter(shift_date=briefing.date).select_related('team')
    actions = briefing.actions.all()
    return render(request, 'briefing/briefing_detail.html', {
        'briefing': briefing, 'forms': forms, 'actions': actions,
    })


def briefing_overview(request, date_str=None):
    """View all submitted forms for a given date - the meeting overview."""
    if date_str:
        from datetime import datetime
        date = datetime.strptime(date_str, '%Y-%m-%d').date()
    else:
        date = timezone.now().date()

    forms = PreBriefingForm.objects.filter(shift_date=date).select_related('team', 'submitted_by')
    briefing = NightBriefing.objects.filter(date=date).first()

    # Aggregated stats
    total_staff_present = sum(f.staff_present for f in forms)
    total_staff_expected = sum(f.staff_expected for f in forms)

    return render(request, 'briefing/overview.html', {
        'forms': forms, 'briefing': briefing, 'date': date,
        'total_staff_present': total_staff_present,
        'total_staff_expected': total_staff_expected,
    })

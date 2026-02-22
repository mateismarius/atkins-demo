from django.shortcuts import render
from django.utils import timezone
from django.db.models import Count, Q, Avg
from projects.models import Project, Task
from qa.models import Inspection, NonConformance
from briefing.models import PreBriefingForm, NightBriefing
from monitoring.models import TeamStatus, IncidentReport, ActivityLog
from planning.models import ShiftPlan, Resource
from core.models import Team


def dashboard(request):
    today = timezone.now().date()

    # Stats
    active_projects = Project.objects.filter(status='active').count()
    total_tasks = Task.objects.exclude(status='done').count()
    open_ncrs = NonConformance.objects.exclude(status='closed').count()
    teams_on_shift = TeamStatus.objects.filter(date=today, status='active').count()

    # Tonight's briefing
    tonight_briefing = NightBriefing.objects.filter(date=today).first()
    forms_submitted = PreBriefingForm.objects.filter(shift_date=today).count()
    total_teams = Team.objects.filter(is_active=True).count()

    # Recent activity
    recent_logs = ActivityLog.objects.select_related('team', 'user')[:10]

    # Team statuses
    team_statuses = TeamStatus.objects.filter(date=today).select_related('team')

    # Upcoming inspections
    upcoming_inspections = Inspection.objects.filter(
        date__gte=timezone.now(), status='scheduled'
    ).select_related('project')[:5]

    # Resources
    resources_in_use = Resource.objects.filter(status='in_use').count()
    resources_total = Resource.objects.count()

    # Open incidents
    open_incidents = IncidentReport.objects.filter(is_resolved=False).count()

    context = {
        'active_projects': active_projects,
        'total_tasks': total_tasks,
        'open_ncrs': open_ncrs,
        'teams_on_shift': teams_on_shift,
        'tonight_briefing': tonight_briefing,
        'forms_submitted': forms_submitted,
        'total_teams': total_teams,
        'recent_logs': recent_logs,
        'team_statuses': team_statuses,
        'upcoming_inspections': upcoming_inspections,
        'resources_in_use': resources_in_use,
        'resources_total': resources_total,
        'open_incidents': open_incidents,
        'today': today,
    }
    return render(request, 'core/dashboard.html', context)

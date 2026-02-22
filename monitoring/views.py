from django.shortcuts import render
from django.utils import timezone
from django.db.models import Count, Sum, Q
from collections import OrderedDict
from .models import TeamStatus, ActivityLog, IncidentReport
from core.models import Team


# Location zone definitions for Heathrow
LOCATION_ZONES = OrderedDict([
    ('Terminal 2', {
        'icon': '🏢',
        'color': 'cyan',
        'keywords': ['terminal 2', 't2'],
        'description': 'Terminal 2 — The Queen\'s Terminal',
    }),
    ('Terminal 3', {
        'icon': '🏢',
        'color': 'amber',
        'keywords': ['terminal 3', 't3'],
        'description': 'Terminal 3 — Long Haul',
    }),
    ('Terminal 4', {
        'icon': '🏢',
        'color': 'purple',
        'keywords': ['terminal 4', 't4'],
        'description': 'Terminal 4 — South Side',
    }),
    ('Terminal 5', {
        'icon': '🏢',
        'color': 'green',
        'keywords': ['terminal 5', 't5'],
        'description': 'Terminal 5 — British Airways Hub',
    }),
    ('Airfield', {
        'icon': '✈️',
        'color': 'blue',
        'keywords': ['airfield', 'taxiway', 'runway', 'apron'],
        'description': 'Airfield — Taxiways, Runways & Aprons',
    }),
    ('Baggage & Tunnels', {
        'icon': '🧳',
        'color': 'orange',
        'keywords': ['baggage', 'tunnel', 'conveyor'],
        'description': 'Baggage Systems & Tunnel Infrastructure',
    }),
    ('Cargo & Logistics', {
        'icon': '📦',
        'color': 'yellow',
        'keywords': ['cargo', 'logistics', 'freight'],
        'description': 'Cargo Area & Logistics Facilities',
    }),
    ('Perimeter & Roads', {
        'icon': '🛣️',
        'color': 'gray',
        'keywords': ['perimeter', 'road', 'fence', 'boundary'],
        'description': 'Perimeter Security & Road Infrastructure',
    }),
    ('Utilities & Systems', {
        'icon': '⚡',
        'color': 'red',
        'keywords': ['utilities', 'mep', 'emergency', 'generator', 'fire', 'electrical', 'pump'],
        'description': 'MEP, Emergency Systems & Utilities',
    }),
])


def _get_zone_for_location(location_str):
    """Match a location string to a zone."""
    loc_lower = location_str.lower()
    for zone_name, zone_info in LOCATION_ZONES.items():
        for keyword in zone_info['keywords']:
            if keyword in loc_lower:
                return zone_name
    return 'Other'


def location_map(request):
    """Location-based monitoring view — teams grouped by zone."""
    today = timezone.now().date()
    statuses = TeamStatus.objects.filter(date=today).select_related('team')
    incidents_today = IncidentReport.objects.filter(
        reported_at__date=today, is_resolved=False
    ).select_related('team')

    # Build zone data
    zones = OrderedDict()
    for zone_name, zone_info in LOCATION_ZONES.items():
        zones[zone_name] = {
            **zone_info,
            'teams': [],
            'total_staff': 0,
            'active_count': 0,
            'delayed_count': 0,
            'incident_count': 0,
        }
    zones['Other'] = {
        'icon': '📍',
        'color': 'gray',
        'keywords': [],
        'description': 'Other / Unassigned Areas',
        'teams': [],
        'total_staff': 0,
        'active_count': 0,
        'delayed_count': 0,
        'incident_count': 0,
    }

    for status in statuses:
        zone_name = _get_zone_for_location(status.location)
        zone = zones[zone_name]

        # Recent activity for this team
        recent_logs = ActivityLog.objects.filter(team=status.team)[:3]

        zone['teams'].append({
            'status': status,
            'team': status.team,
            'recent_logs': recent_logs,
        })
        zone['total_staff'] += status.staff_count
        if status.status == 'active':
            zone['active_count'] += 1
        if status.status == 'delayed':
            zone['delayed_count'] += 1

    # Map incidents to zones
    for inc in incidents_today:
        zone_name = _get_zone_for_location(inc.location)
        if zone_name in zones:
            zones[zone_name]['incident_count'] += 1

    # Remove empty zones
    active_zones = OrderedDict(
        (k, v) for k, v in zones.items() if v['teams']
    )
    empty_zones = [k for k, v in zones.items() if not v['teams'] and k != 'Other']

    # Summary
    total_teams = statuses.count()
    total_staff = sum(s.staff_count for s in statuses)
    total_zones = len(active_zones)

    return render(request, 'monitoring/location_map.html', {
        'zones': active_zones,
        'empty_zones': empty_zones,
        'total_teams': total_teams,
        'total_staff': total_staff,
        'total_zones': total_zones,
        'incidents_today': incidents_today,
        'today': today,
    })


def monitoring_dashboard(request):
    today = timezone.now().date()
    teams = Team.objects.filter(is_active=True)
    statuses = TeamStatus.objects.filter(date=today).select_related('team')
    
    # Map teams to statuses
    team_data = []
    for team in teams:
        status = statuses.filter(team=team).first()
        recent_logs = ActivityLog.objects.filter(team=team).select_related('user')[:5]
        team_data.append({
            'team': team,
            'status': status,
            'recent_logs': recent_logs,
        })

    # Activity timeline
    timeline = ActivityLog.objects.select_related('team', 'user')[:30]

    # Active incidents
    active_incidents = IncidentReport.objects.filter(is_resolved=False).select_related('team', 'reported_by')

    # Summary stats
    stats = {
        'active_teams': statuses.filter(status='active').count(),
        'on_break': statuses.filter(status='on_break').count(),
        'delayed': statuses.filter(status='delayed').count(),
        'incidents': active_incidents.count(),
        'total_staff': sum(s.staff_count for s in statuses),
        'avg_progress': round(sum(s.progress for s in statuses) / max(statuses.count(), 1)),
    }

    return render(request, 'monitoring/dashboard.html', {
        'team_data': team_data, 'timeline': timeline,
        'active_incidents': active_incidents, 'stats': stats, 'today': today,
    })


def team_detail(request, pk):
    team = Team.objects.get(pk=pk)
    today = timezone.now().date()
    status = TeamStatus.objects.filter(team=team, date=today).first()
    logs = ActivityLog.objects.filter(team=team).select_related('user')[:50]
    incidents = IncidentReport.objects.filter(team=team).select_related('reported_by')[:10]
    members = team.members.select_related('user').all()

    return render(request, 'monitoring/team_detail.html', {
        'team': team, 'status': status, 'logs': logs,
        'incidents': incidents, 'members': members,
    })

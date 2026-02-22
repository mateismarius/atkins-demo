from django.shortcuts import render, get_object_or_404
from .models import Project, Task, Milestone


def project_list(request):
    status_filter = request.GET.get('status', '')
    projects = Project.objects.all()
    if status_filter:
        projects = projects.filter(status=status_filter)
    
    stats = {
        'total': Project.objects.count(),
        'active': Project.objects.filter(status='active').count(),
        'completed': Project.objects.filter(status='completed').count(),
        'on_hold': Project.objects.filter(status='on_hold').count(),
    }
    return render(request, 'projects/project_list.html', {
        'projects': projects, 'stats': stats, 'current_filter': status_filter,
    })


def project_detail(request, pk):
    project = get_object_or_404(Project, pk=pk)
    tasks = project.tasks.all()
    milestones = project.milestones.all()

    task_stats = {
        'backlog': tasks.filter(status='backlog').count(),
        'todo': tasks.filter(status='todo').count(),
        'in_progress': tasks.filter(status='in_progress').count(),
        'review': tasks.filter(status='review').count(),
        'done': tasks.filter(status='done').count(),
    }

    return render(request, 'projects/project_detail.html', {
        'project': project, 'tasks': tasks, 'milestones': milestones,
        'task_stats': task_stats,
    })


def kanban_board(request, pk):
    project = get_object_or_404(Project, pk=pk)
    columns = {
        'backlog': project.tasks.filter(status='backlog'),
        'todo': project.tasks.filter(status='todo'),
        'in_progress': project.tasks.filter(status='in_progress'),
        'review': project.tasks.filter(status='review'),
        'done': project.tasks.filter(status='done'),
    }
    return render(request, 'projects/kanban.html', {
        'project': project, 'columns': columns,
    })

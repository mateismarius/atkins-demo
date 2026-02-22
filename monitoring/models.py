from django.db import models
from django.contrib.auth.models import User
from core.models import Team


class TeamStatus(models.Model):
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('on_break', 'On Break'),
        ('standby', 'Standby'),
        ('delayed', 'Delayed'),
        ('completed', 'Completed'),
        ('incident', 'Incident'),
    ]
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='statuses')
    date = models.DateField()
    current_task = models.CharField(max_length=300)
    location = models.CharField(max_length=200)
    progress = models.IntegerField(default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    staff_count = models.IntegerField(default=0)
    notes = models.TextField(blank=True)
    last_update = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.team.code} - {self.status}"

    class Meta:
        ordering = ['team__code']
        verbose_name_plural = 'Team Statuses'


class ActivityLog(models.Model):
    ACTION_CHOICES = [
        ('task_started', 'Task Started'),
        ('task_completed', 'Task Completed'),
        ('break_start', 'Break Started'),
        ('break_end', 'Break Ended'),
        ('incident', 'Incident Reported'),
        ('update', 'Status Update'),
        ('handover', 'Shift Handover'),
        ('delay', 'Delay Reported'),
    ]
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='activity_logs')
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    details = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.team.code} - {self.action} - {self.timestamp}"

    class Meta:
        ordering = ['-timestamp']


class IncidentReport(models.Model):
    SEVERITY_CHOICES = [
        ('near_miss', 'Near Miss'),
        ('minor', 'Minor'),
        ('major', 'Major'),
        ('serious', 'Serious'),
    ]
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='incidents')
    reported_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    title = models.CharField(max_length=200)
    description = models.TextField()
    severity = models.CharField(max_length=10, choices=SEVERITY_CHOICES)
    location = models.CharField(max_length=200)
    immediate_action = models.TextField(blank=True)
    is_resolved = models.BooleanField(default=False)
    reported_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"INC-{self.id}: {self.title}"

    class Meta:
        ordering = ['-reported_at']

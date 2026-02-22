from django.db import models
from django.contrib.auth.models import User
from core.models import Team


class ShiftPlan(models.Model):
    date = models.DateField()
    shift = models.CharField(max_length=10, choices=[
        ('night', 'Night'), ('day', 'Day'), ('swing', 'Swing'),
    ], default='night')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    is_published = models.BooleanField(default=False)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Plan - {self.date} ({self.shift})"

    class Meta:
        ordering = ['-date']
        unique_together = ['date', 'shift']


class ShiftAssignment(models.Model):
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('normal', 'Normal'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ]
    plan = models.ForeignKey(ShiftPlan, on_delete=models.CASCADE, related_name='assignments')
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='shift_assignments')
    area = models.CharField(max_length=200)
    task_description = models.TextField()
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='normal')
    estimated_hours = models.DecimalField(max_digits=4, decimal_places=1, default=8)
    actual_hours = models.DecimalField(max_digits=4, decimal_places=1, null=True, blank=True)
    status = models.CharField(max_length=20, choices=[
        ('planned', 'Planned'), ('in_progress', 'In Progress'),
        ('completed', 'Completed'), ('deferred', 'Deferred'),
    ], default='planned')
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"{self.team.code} - {self.area}"

    class Meta:
        ordering = ['team__code']


class Resource(models.Model):
    TYPE_CHOICES = [
        ('vehicle', 'Vehicle'),
        ('equipment', 'Equipment'),
        ('tool', 'Tool'),
        ('material', 'Material'),
    ]
    STATUS_CHOICES = [
        ('available', 'Available'),
        ('in_use', 'In Use'),
        ('maintenance', 'Maintenance'),
        ('out_of_service', 'Out of Service'),
    ]
    name = models.CharField(max_length=100)
    resource_type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='available')
    assigned_to = models.ForeignKey(Team, on_delete=models.SET_NULL, null=True, blank=True)
    location = models.CharField(max_length=200, blank=True)
    last_inspection = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"{self.name} ({self.get_resource_type_display()})"

    class Meta:
        ordering = ['resource_type', 'name']

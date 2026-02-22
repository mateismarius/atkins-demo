from django.db import models
from django.contrib.auth.models import User
from core.models import Team


class PreBriefingForm(models.Model):
    """Form that each team must complete BEFORE the night briefing meeting."""
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='prebriefing_forms')
    shift_date = models.DateField()
    submitted_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)

    # Staffing
    staff_present = models.IntegerField(default=0)
    staff_expected = models.IntegerField(default=0)
    absentees = models.TextField(blank=True, help_text='List absentees and reasons')

    # Equipment & Safety
    equipment_status = models.CharField(max_length=20, choices=[
        ('all_ok', 'All OK'),
        ('minor_issues', 'Minor Issues'),
        ('major_issues', 'Major Issues'),
        ('critical', 'Critical'),
    ], default='all_ok')
    equipment_notes = models.TextField(blank=True)

    ppe_check_completed = models.BooleanField(default=False)
    safety_concerns = models.TextField(blank=True)
    near_misses = models.TextField(blank=True, help_text='Report any near misses from previous shift')

    # Work Status
    pending_tasks_from_previous = models.TextField(blank=True, help_text='Tasks carried over from previous shift')
    planned_tasks_tonight = models.TextField(blank=True, help_text='What the team plans to accomplish')
    blockers = models.TextField(blank=True, help_text='Any blockers or dependencies')
    materials_needed = models.TextField(blank=True)

    # Permits & Compliance
    permits_in_place = models.BooleanField(default=True)
    permit_details = models.TextField(blank=True)
    method_statements_reviewed = models.BooleanField(default=False)

    # Weather & Conditions
    weather_impact = models.CharField(max_length=20, choices=[
        ('none', 'No Impact'),
        ('minor', 'Minor Impact'),
        ('significant', 'Significant Impact'),
        ('work_stopped', 'Work Stopped'),
    ], default='none')
    weather_notes = models.TextField(blank=True)

    # Additional
    additional_notes = models.TextField(blank=True)
    risk_rating = models.CharField(max_length=10, choices=[
        ('green', 'Green - Low Risk'),
        ('amber', 'Amber - Medium Risk'),
        ('red', 'Red - High Risk'),
    ], default='green')

    submitted_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.team.code} - {self.shift_date}"

    @property
    def staff_percentage(self):
        if self.staff_expected == 0:
            return 0
        return round((self.staff_present / self.staff_expected) * 100)

    class Meta:
        ordering = ['-shift_date', 'team__code']
        unique_together = ['team', 'shift_date']


class NightBriefing(models.Model):
    """The actual night briefing session, populated after all teams submit forms."""
    date = models.DateField(unique=True)
    shift = models.CharField(max_length=10, default='night')
    conducted_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    start_time = models.TimeField(null=True, blank=True)
    end_time = models.TimeField(null=True, blank=True)

    # Aggregated from forms
    total_staff_present = models.IntegerField(default=0)
    total_staff_expected = models.IntegerField(default=0)

    # Meeting content
    safety_briefing = models.TextField(blank=True, help_text='Safety topics discussed')
    key_decisions = models.TextField(blank=True)
    action_items = models.TextField(blank=True)
    escalations = models.TextField(blank=True, help_text='Issues escalated to management')
    next_shift_handover = models.TextField(blank=True)

    overall_risk = models.CharField(max_length=10, choices=[
        ('green', 'Green'), ('amber', 'Amber'), ('red', 'Red'),
    ], default='green')

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Night Briefing - {self.date}"

    @property
    def forms_submitted(self):
        return PreBriefingForm.objects.filter(shift_date=self.date).count()

    class Meta:
        ordering = ['-date']


class BriefingActionItem(models.Model):
    briefing = models.ForeignKey(NightBriefing, on_delete=models.CASCADE, related_name='actions')
    description = models.CharField(max_length=300)
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    team = models.ForeignKey(Team, on_delete=models.SET_NULL, null=True, blank=True)
    priority = models.CharField(max_length=10, choices=[
        ('low', 'Low'), ('medium', 'Medium'), ('high', 'High'), ('urgent', 'Urgent'),
    ], default='medium')
    status = models.CharField(max_length=20, choices=[
        ('pending', 'Pending'), ('in_progress', 'In Progress'), ('done', 'Done'),
    ], default='pending')
    due_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.description

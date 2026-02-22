from django.db import models
from django.contrib.auth.models import User


class NightReport(models.Model):
    """Consolidated night shift report combining briefing, QA, and incidents."""
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('generated', 'Generated'),
        ('reviewed', 'Reviewed'),
        ('approved', 'Approved'),
    ]
    date = models.DateField(unique=True)
    generated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='draft')

    # Summary fields (auto-populated when generating)
    total_teams = models.IntegerField(default=0)
    briefing_forms_submitted = models.IntegerField(default=0)
    qa_forms_submitted = models.IntegerField(default=0)
    total_staff_present = models.IntegerField(default=0)
    total_staff_expected = models.IntegerField(default=0)
    incidents_count = models.IntegerField(default=0)
    overall_risk = models.CharField(max_length=10, choices=[
        ('green', 'Green'), ('amber', 'Amber'), ('red', 'Red'),
    ], default='green')

    # Manager notes
    manager_summary = models.TextField(blank=True, help_text='Night Operations Manager summary')
    key_issues = models.TextField(blank=True)
    handover_notes = models.TextField(blank=True, help_text='Notes for the day shift')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Night Report - {self.date}"

    class Meta:
        ordering = ['-date']

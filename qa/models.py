from django.db import models
from django.contrib.auth.models import User
from projects.models import Project
from core.models import Team


class QAChecklistForm(models.Model):
    """QA checklist form that teams fill in during the shift."""
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='qa_forms')
    shift_date = models.DateField()
    submitted_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    area_inspected = models.CharField(max_length=200, help_text='Location / area inspected')
    project = models.ForeignKey(Project, on_delete=models.SET_NULL, null=True, blank=True, related_name='qa_checklists')

    # Workmanship
    RATING_CHOICES = [
        ('pass', 'Pass'),
        ('minor', 'Minor Issue'),
        ('major', 'Major Issue'),
        ('fail', 'Fail'),
        ('na', 'N/A'),
    ]
    workmanship_quality = models.CharField(max_length=10, choices=RATING_CHOICES, default='pass')
    workmanship_notes = models.TextField(blank=True)

    # Materials
    materials_correct = models.BooleanField(default=True, help_text='Correct materials used as per specification')
    materials_stored_properly = models.BooleanField(default=True)
    materials_notes = models.TextField(blank=True)

    # Method Statements & Drawings
    work_to_method_statement = models.BooleanField(default=True, help_text='Work carried out as per method statement')
    work_to_drawings = models.BooleanField(default=True, help_text='Work carried out as per drawings')
    deviations = models.TextField(blank=True, help_text='List any deviations from method statement or drawings')

    # Housekeeping & Safety
    area_clean_tidy = models.BooleanField(default=True, help_text='Work area clean and tidy')
    waste_segregated = models.BooleanField(default=True, help_text='Waste properly segregated')
    barriers_signage = models.BooleanField(default=True, help_text='Barriers and signage in place')
    ppe_compliant = models.BooleanField(default=True, help_text='All personnel wearing correct PPE')
    housekeeping_notes = models.TextField(blank=True)

    # Services & Protection
    existing_services_protected = models.BooleanField(default=True, help_text='Existing services protected from damage')
    completed_work_protected = models.BooleanField(default=True, help_text='Completed work protected')
    protection_notes = models.TextField(blank=True)

    # Snag List
    snags_identified = models.TextField(blank=True, help_text='List of defects/snags found')
    snags_count = models.IntegerField(default=0)

    # Overall
    OUTCOME_CHOICES = [
        ('approved', 'Approved'),
        ('conditional', 'Conditional Approval'),
        ('rework', 'Rework Required'),
        ('rejected', 'Rejected'),
    ]
    overall_outcome = models.CharField(max_length=15, choices=OUTCOME_CHOICES, default='approved')
    inspector_comments = models.TextField(blank=True)
    follow_up_required = models.BooleanField(default=False)
    follow_up_details = models.TextField(blank=True)

    # Photos would go here in production
    # photo_1 = models.ImageField(...)

    submitted_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"QA Check - {self.team.code} - {self.area_inspected} ({self.shift_date})"

    @property
    def pass_count(self):
        checks = [
            self.materials_correct, self.materials_stored_properly,
            self.work_to_method_statement, self.work_to_drawings,
            self.area_clean_tidy, self.waste_segregated,
            self.barriers_signage, self.ppe_compliant,
            self.existing_services_protected, self.completed_work_protected,
        ]
        return sum(1 for c in checks if c)

    @property
    def total_checks(self):
        return 10

    @property
    def compliance_percentage(self):
        return round((self.pass_count / self.total_checks) * 100)

    class Meta:
        ordering = ['-shift_date', 'team__code']
        unique_together = ['team', 'shift_date', 'area_inspected']


class Inspection(models.Model):
    STATUS_CHOICES = [
        ('scheduled', 'Scheduled'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='inspections')
    inspector = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='inspections')
    date = models.DateTimeField()
    area = models.CharField(max_length=200)
    inspection_type = models.CharField(max_length=100, default='General')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='scheduled')
    score = models.IntegerField(default=0)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Inspection {self.id} - {self.area}"

    class Meta:
        ordering = ['-date']


class InspectionItem(models.Model):
    inspection = models.ForeignKey(Inspection, on_delete=models.CASCADE, related_name='items')
    description = models.CharField(max_length=300)
    is_compliant = models.BooleanField(default=True)
    severity = models.CharField(max_length=20, default='minor', choices=[
        ('info', 'Info'), ('minor', 'Minor'), ('major', 'Major'), ('critical', 'Critical')
    ])
    notes = models.TextField(blank=True)
    photo = models.CharField(max_length=300, blank=True)

    def __str__(self):
        return self.description


class NonConformance(models.Model):
    STATUS_CHOICES = [
        ('open', 'Open'),
        ('investigating', 'Investigating'),
        ('corrective_action', 'Corrective Action'),
        ('closed', 'Closed'),
    ]
    SEVERITY_CHOICES = [
        ('minor', 'Minor'),
        ('major', 'Major'),
        ('critical', 'Critical'),
    ]
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='ncrs')
    title = models.CharField(max_length=200)
    description = models.TextField()
    severity = models.CharField(max_length=10, choices=SEVERITY_CHOICES, default='minor')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')
    raised_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='raised_ncrs')
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_ncrs')
    corrective_action = models.TextField(blank=True)
    due_date = models.DateField(null=True, blank=True)
    raised_date = models.DateTimeField(auto_now_add=True)
    closed_date = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"NCR-{self.id}: {self.title}"

    class Meta:
        ordering = ['-raised_date']
        verbose_name = 'Non-Conformance Report'
        verbose_name_plural = 'Non-Conformance Reports'

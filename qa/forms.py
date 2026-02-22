from django import forms
from .models import QAChecklistForm


class QAChecklistFormForm(forms.ModelForm):
    class Meta:
        model = QAChecklistForm
        exclude = ['submitted_by', 'submitted_at', 'updated_at']
        widgets = {
            'shift_date': forms.DateInput(attrs={'type': 'date', 'class': 'input input-bordered w-full'}),
            'team': forms.Select(attrs={'class': 'select select-bordered w-full'}),
            'area_inspected': forms.TextInput(attrs={'class': 'input input-bordered w-full', 'placeholder': 'e.g. Terminal 2 Baggage Hall, Taxiway Alpha Section 3'}),
            'project': forms.Select(attrs={'class': 'select select-bordered w-full'}),
            'workmanship_quality': forms.Select(attrs={'class': 'select select-bordered w-full'}),
            'workmanship_notes': forms.Textarea(attrs={'class': 'textarea textarea-bordered w-full', 'rows': 2}),
            'materials_correct': forms.CheckboxInput(attrs={'class': 'toggle toggle-success'}),
            'materials_stored_properly': forms.CheckboxInput(attrs={'class': 'toggle toggle-success'}),
            'materials_notes': forms.Textarea(attrs={'class': 'textarea textarea-bordered w-full', 'rows': 2}),
            'work_to_method_statement': forms.CheckboxInput(attrs={'class': 'toggle toggle-success'}),
            'work_to_drawings': forms.CheckboxInput(attrs={'class': 'toggle toggle-success'}),
            'deviations': forms.Textarea(attrs={'class': 'textarea textarea-bordered w-full', 'rows': 2, 'placeholder': 'List any deviations...'}),
            'area_clean_tidy': forms.CheckboxInput(attrs={'class': 'toggle toggle-success'}),
            'waste_segregated': forms.CheckboxInput(attrs={'class': 'toggle toggle-success'}),
            'barriers_signage': forms.CheckboxInput(attrs={'class': 'toggle toggle-success'}),
            'ppe_compliant': forms.CheckboxInput(attrs={'class': 'toggle toggle-success'}),
            'housekeeping_notes': forms.Textarea(attrs={'class': 'textarea textarea-bordered w-full', 'rows': 2}),
            'existing_services_protected': forms.CheckboxInput(attrs={'class': 'toggle toggle-success'}),
            'completed_work_protected': forms.CheckboxInput(attrs={'class': 'toggle toggle-success'}),
            'protection_notes': forms.Textarea(attrs={'class': 'textarea textarea-bordered w-full', 'rows': 2}),
            'snags_identified': forms.Textarea(attrs={'class': 'textarea textarea-bordered w-full', 'rows': 3, 'placeholder': 'List defects/snags found...'}),
            'snags_count': forms.NumberInput(attrs={'class': 'input input-bordered w-full', 'min': 0}),
            'overall_outcome': forms.Select(attrs={'class': 'select select-bordered w-full'}),
            'inspector_comments': forms.Textarea(attrs={'class': 'textarea textarea-bordered w-full', 'rows': 3}),
            'follow_up_required': forms.CheckboxInput(attrs={'class': 'toggle toggle-warning'}),
            'follow_up_details': forms.Textarea(attrs={'class': 'textarea textarea-bordered w-full', 'rows': 2, 'placeholder': 'What follow-up is needed?'}),
        }

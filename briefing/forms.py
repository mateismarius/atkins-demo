from django import forms
from .models import PreBriefingForm, NightBriefing, BriefingActionItem


class PreBriefingFormForm(forms.ModelForm):
    class Meta:
        model = PreBriefingForm
        exclude = ['submitted_by', 'submitted_at', 'updated_at']
        widgets = {
            'shift_date': forms.DateInput(attrs={'type': 'date', 'class': 'input input-bordered w-full'}),
            'team': forms.Select(attrs={'class': 'select select-bordered w-full'}),
            'staff_present': forms.NumberInput(attrs={'class': 'input input-bordered w-full', 'min': 0}),
            'staff_expected': forms.NumberInput(attrs={'class': 'input input-bordered w-full', 'min': 0}),
            'absentees': forms.Textarea(attrs={'class': 'textarea textarea-bordered w-full', 'rows': 2, 'placeholder': 'List names and reasons...'}),
            'equipment_status': forms.Select(attrs={'class': 'select select-bordered w-full'}),
            'equipment_notes': forms.Textarea(attrs={'class': 'textarea textarea-bordered w-full', 'rows': 2}),
            'ppe_check_completed': forms.CheckboxInput(attrs={'class': 'toggle toggle-success'}),
            'safety_concerns': forms.Textarea(attrs={'class': 'textarea textarea-bordered w-full', 'rows': 2, 'placeholder': 'Any safety concerns to report?'}),
            'near_misses': forms.Textarea(attrs={'class': 'textarea textarea-bordered w-full', 'rows': 2, 'placeholder': 'Report near misses from previous shift...'}),
            'pending_tasks_from_previous': forms.Textarea(attrs={'class': 'textarea textarea-bordered w-full', 'rows': 3, 'placeholder': 'Tasks carried over...'}),
            'planned_tasks_tonight': forms.Textarea(attrs={'class': 'textarea textarea-bordered w-full', 'rows': 3, 'placeholder': 'What do you plan to accomplish tonight?'}),
            'blockers': forms.Textarea(attrs={'class': 'textarea textarea-bordered w-full', 'rows': 2, 'placeholder': 'Any blockers or dependencies?'}),
            'materials_needed': forms.Textarea(attrs={'class': 'textarea textarea-bordered w-full', 'rows': 2}),
            'permits_in_place': forms.CheckboxInput(attrs={'class': 'toggle toggle-success'}),
            'permit_details': forms.Textarea(attrs={'class': 'textarea textarea-bordered w-full', 'rows': 2}),
            'method_statements_reviewed': forms.CheckboxInput(attrs={'class': 'toggle toggle-success'}),
            'weather_impact': forms.Select(attrs={'class': 'select select-bordered w-full'}),
            'weather_notes': forms.Textarea(attrs={'class': 'textarea textarea-bordered w-full', 'rows': 2}),
            'additional_notes': forms.Textarea(attrs={'class': 'textarea textarea-bordered w-full', 'rows': 3}),
            'risk_rating': forms.Select(attrs={'class': 'select select-bordered w-full'}),
        }


class NightBriefingForm(forms.ModelForm):
    class Meta:
        model = NightBriefing
        exclude = ['created_at']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date', 'class': 'input input-bordered w-full'}),
            'shift': forms.Select(attrs={'class': 'select select-bordered w-full'}),
            'conducted_by': forms.Select(attrs={'class': 'select select-bordered w-full'}),
            'start_time': forms.TimeInput(attrs={'type': 'time', 'class': 'input input-bordered w-full'}),
            'end_time': forms.TimeInput(attrs={'type': 'time', 'class': 'input input-bordered w-full'}),
            'total_staff_present': forms.NumberInput(attrs={'class': 'input input-bordered w-full'}),
            'total_staff_expected': forms.NumberInput(attrs={'class': 'input input-bordered w-full'}),
            'safety_briefing': forms.Textarea(attrs={'class': 'textarea textarea-bordered w-full', 'rows': 3}),
            'key_decisions': forms.Textarea(attrs={'class': 'textarea textarea-bordered w-full', 'rows': 3}),
            'action_items': forms.Textarea(attrs={'class': 'textarea textarea-bordered w-full', 'rows': 3}),
            'escalations': forms.Textarea(attrs={'class': 'textarea textarea-bordered w-full', 'rows': 3}),
            'next_shift_handover': forms.Textarea(attrs={'class': 'textarea textarea-bordered w-full', 'rows': 3}),
            'overall_risk': forms.Select(attrs={'class': 'select select-bordered w-full'}),
        }

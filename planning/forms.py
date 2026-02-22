from django import forms
from .models import ShiftPlan, ShiftAssignment, Resource
from core.models import Team


class ShiftPlanForm(forms.ModelForm):
    class Meta:
        model = ShiftPlan
        fields = ['date', 'shift', 'notes']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date', 'class': 'input input-bordered w-full'}),
            'shift': forms.Select(attrs={'class': 'select select-bordered w-full'}),
            'notes': forms.Textarea(attrs={'class': 'textarea textarea-bordered w-full', 'rows': 3, 'placeholder': 'General notes for this shift plan...'}),
        }


class ShiftAssignmentForm(forms.ModelForm):
    class Meta:
        model = ShiftAssignment
        fields = ['team', 'area', 'task_description', 'priority', 'estimated_hours', 'notes']
        widgets = {
            'team': forms.Select(attrs={'class': 'select select-bordered w-full'}),
            'area': forms.TextInput(attrs={'class': 'input input-bordered w-full', 'placeholder': 'e.g. Terminal 2 - Arrivals'}),
            'task_description': forms.Textarea(attrs={'class': 'textarea textarea-bordered w-full', 'rows': 2, 'placeholder': 'Describe the task...'}),
            'priority': forms.Select(attrs={'class': 'select select-bordered w-full'}),
            'estimated_hours': forms.NumberInput(attrs={'class': 'input input-bordered w-full', 'step': '0.5', 'min': '0.5', 'max': '12'}),
            'notes': forms.Textarea(attrs={'class': 'textarea textarea-bordered w-full', 'rows': 2, 'placeholder': 'Additional notes...'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['team'].queryset = Team.objects.filter(is_active=True)
        self.fields['notes'].required = False


class AssignmentStatusForm(forms.ModelForm):
    class Meta:
        model = ShiftAssignment
        fields = ['status', 'actual_hours', 'notes']
        widgets = {
            'status': forms.Select(attrs={'class': 'select select-bordered select-sm w-full'}),
            'actual_hours': forms.NumberInput(attrs={'class': 'input input-bordered input-sm w-full', 'step': '0.5'}),
            'notes': forms.Textarea(attrs={'class': 'textarea textarea-bordered textarea-sm w-full', 'rows': 2}),
        }


class ResourceForm(forms.ModelForm):
    class Meta:
        model = Resource
        fields = ['name', 'resource_type', 'status', 'assigned_to', 'location', 'notes']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'input input-bordered w-full'}),
            'resource_type': forms.Select(attrs={'class': 'select select-bordered w-full'}),
            'status': forms.Select(attrs={'class': 'select select-bordered w-full'}),
            'assigned_to': forms.Select(attrs={'class': 'select select-bordered w-full'}),
            'location': forms.TextInput(attrs={'class': 'input input-bordered w-full'}),
            'notes': forms.Textarea(attrs={'class': 'textarea textarea-bordered w-full', 'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['assigned_to'].queryset = Team.objects.filter(is_active=True)
        self.fields['assigned_to'].required = False
        self.fields['notes'].required = False
        self.fields['location'].required = False

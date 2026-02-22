from django.db import models
from django.contrib.auth.models import User


class Team(models.Model):
    SHIFT_CHOICES = [
        ('night', 'Night Shift'),
        ('day', 'Day Shift'),
        ('swing', 'Swing Shift'),
    ]
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=10, unique=True)
    leader = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='led_teams')
    shift = models.CharField(max_length=10, choices=SHIFT_CHOICES, default='night')
    area = models.CharField(max_length=200, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.code} - {self.name}"

    class Meta:
        ordering = ['code']


class TeamMember(models.Model):
    ROLE_CHOICES = [
        ('leader', 'Team Leader'),
        ('supervisor', 'Supervisor'),
        ('operative', 'Operative'),
        ('engineer', 'Engineer'),
        ('apprentice', 'Apprentice'),
    ]
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='team_profile')
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='members')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='operative')
    phone = models.CharField(max_length=20, blank=True)
    employee_id = models.CharField(max_length=20, blank=True)
    is_on_shift = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.get_full_name()} ({self.team.code})"

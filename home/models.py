from django.db import models
from django.contrib.auth.models import User


class StudentProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='student_profile')
    application_id = models.CharField(max_length=20, unique=True)
    full_name = models.CharField(max_length=200)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.full_name} ({self.application_id})"


class Document(models.Model):
    STATUS_CHOICES = [
        ('uploaded', 'Uploaded'),
        ('pending', 'Pending'),
        ('done', 'Done'),
        ('missing', 'Missing'),
    ]

    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='documents')
    name = models.CharField(max_length=200)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    uploaded_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.name} - {self.get_status_display()}"


class ApplicationStep(models.Model):
    STEP_STATUS_CHOICES = [
        ('done', 'Done'),
        ('current', 'Current'),
        ('locked', 'Locked'),
    ]

    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='application_steps')
    step_number = models.PositiveIntegerField()
    title = models.CharField(max_length=200)
    status = models.CharField(max_length=20, choices=STEP_STATUS_CHOICES, default='locked')

    class Meta:
        ordering = ['step_number']

    def __str__(self):
        return f"Step {self.step_number}: {self.title} ({self.get_status_display()})"


class UpcomingDate(models.Model):
    title = models.CharField(max_length=200)
    date = models.DateField()
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['date']

    def __str__(self):
        return f"{self.title} - {self.date}"


class Reminder(models.Model):
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='reminders', null=True, blank=True)
    message = models.TextField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.message[:50]


class Announcement(models.Model):
    title = models.CharField(max_length=300)
    summary = models.TextField()
    image = models.ImageField(upload_to='announcements/', null=True, blank=True)
    published_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['-published_at']

    def __str__(self):
        return self.title

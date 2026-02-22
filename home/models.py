from django.db import models
from django.contrib.auth.models import User


class Office(models.Model):
    """Campus office that can accept student assistants."""
    name = models.CharField(max_length=200, unique=True)
    building = models.CharField(max_length=200)
    room = models.CharField(max_length=200, blank=True, default='')
    hours = models.CharField(max_length=200, default='Mon–Fri, 8:00 AM – 5:00 PM')
    head = models.CharField(max_length=200, blank=True, default='')
    total_slots = models.PositiveIntegerField(default=3)
    latitude = models.FloatField(default=10.7426)
    longitude = models.FloatField(default=122.9703)
    icon = models.CharField(max_length=100, default='fa-solid fa-building')
    description = models.TextField(blank=True, default='')
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


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
    PRIORITY_CHOICES = [
        ('info', 'Info'),
        ('warning', 'Warning'),
        ('urgent', 'Urgent'),
    ]

    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='reminders', null=True, blank=True)
    message = models.TextField()
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='info')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"[{self.get_priority_display()}] {self.message[:50]}"


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


class NewApplication(models.Model):
    GENDER_CHOICES = [
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other'),
    ]

    YEAR_LEVEL_CHOICES = [
        (1, '1st Year'),
        (2, '2nd Year'),
        (3, '3rd Year'),
        (4, '4th Year'),
    ]

    SEMESTER_CHOICES = [
        ('1st', '1st Semester'),
        ('2nd', '2nd Semester'),
    ]

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('under_review', 'Under Review'),
        ('interview_scheduled', 'Interview Scheduled'),
        ('office_assigned', 'Office Assigned'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]

    # ── Personal Information ──
    first_name = models.CharField(max_length=15)
    middle_initial = models.CharField(max_length=1)
    last_name = models.CharField(max_length=10)
    extension_name = models.CharField(max_length=5, blank=True, default='')
    date_of_birth = models.DateField()
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES)
    contact_number = models.CharField(max_length=11)
    email = models.EmailField()
    address = models.TextField()

    # ── Academic Information ──
    student_id = models.CharField(max_length=8, unique=True)
    course = models.CharField(max_length=100)
    year_level = models.IntegerField(choices=YEAR_LEVEL_CHOICES)
    semester = models.CharField(max_length=5, choices=SEMESTER_CHOICES)

    # ── Document Uploads ──
    application_form = models.FileField(upload_to='applications/new/', blank=True)
    id_picture = models.ImageField(upload_to='applications/new/', blank=True)
    barangay_clearance = models.FileField(upload_to='applications/new/', blank=True)
    parents_itr = models.FileField(upload_to='applications/new/', blank=True)
    enrolment_form = models.FileField(upload_to='applications/new/', blank=True)
    schedule_classes = models.FileField(upload_to='applications/new/', blank=True)
    proof_insurance = models.FileField(upload_to='applications/new/', blank=True)
    grades_last_sem = models.FileField(upload_to='applications/new/', blank=True)
    official_time = models.FileField(upload_to='applications/new/', blank=True)

    # ── Preferred Office ──
    preferred_office = models.ForeignKey(
        Office, null=True, blank=True, on_delete=models.SET_NULL,
        related_name='new_applications',
        help_text='Office the student prefers to be assigned to.',
    )

    # ── Workflow / Scheduling ──
    interview_date = models.DateTimeField(null=True, blank=True)
    assigned_office = models.CharField(max_length=200, blank=True, default='')
    start_date = models.DateField(null=True, blank=True)

    # ── Meta ──
    submitted_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    class Meta:
        ordering = ['-submitted_at']

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.student_id})"


class RenewalApplication(models.Model):
    """Renewal application for returning student assistants."""

    YEAR_LEVEL_CHOICES = NewApplication.YEAR_LEVEL_CHOICES
    SEMESTER_CHOICES = NewApplication.SEMESTER_CHOICES
    STATUS_CHOICES = NewApplication.STATUS_CHOICES

    # ── Identity ──
    student_id = models.CharField(max_length=8, unique=True)
    full_name = models.CharField(max_length=200)
    email = models.EmailField()
    contact_number = models.CharField(max_length=11)
    address = models.TextField()

    # ── Academic ──
    course = models.CharField(max_length=100)
    year_level = models.IntegerField(choices=YEAR_LEVEL_CHOICES)
    semester = models.CharField(max_length=5, choices=SEMESTER_CHOICES)

    # ── Previous & Preferred Assignment ──
    previous_office = models.ForeignKey(
        Office, null=True, blank=True, on_delete=models.SET_NULL,
        related_name='renewal_previous',
        help_text='Office where the student previously served.',
    )
    preferred_office = models.ForeignKey(
        Office, null=True, blank=True, on_delete=models.SET_NULL,
        related_name='renewal_preferred',
        help_text='Office the student prefers for renewal.',
    )
    hours_rendered = models.PositiveIntegerField()
    supervisor_name = models.CharField(max_length=200, blank=True, default='')

    # ── Renewal Documents ──
    enrolment_form = models.FileField(upload_to='applications/renewal/', blank=True)
    schedule_classes = models.FileField(upload_to='applications/renewal/', blank=True)
    grades_last_sem = models.FileField(upload_to='applications/renewal/', blank=True)
    official_time = models.FileField(upload_to='applications/renewal/', blank=True)
    recommendation_letter = models.FileField(upload_to='applications/renewal/', blank=True)
    evaluation_form = models.FileField(upload_to='applications/renewal/', blank=True)

    # ── Workflow / Scheduling ──
    interview_date = models.DateTimeField(null=True, blank=True)
    assigned_office = models.CharField(max_length=200, blank=True, default='')
    start_date = models.DateField(null=True, blank=True)

    # ── Meta ──
    submitted_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    class Meta:
        ordering = ['-submitted_at']

    def __str__(self):
        return f"[Renewal] {self.full_name} ({self.student_id})"

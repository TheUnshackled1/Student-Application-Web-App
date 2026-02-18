from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login
from django.http import HttpResponseForbidden, JsonResponse
from django.views.decorators.http import require_POST
from django.conf import settings
from django.utils import timezone
from .models import (
    StudentProfile, Document, ApplicationStep,
    UpcomingDate, Reminder, Announcement,
)
from .forms import ReminderForm, UpcomingDateForm, AnnouncementForm
from datetime import date as _date, timedelta
import json
import base64
import os
import uuid
import cv2
import numpy as np


def _urgency_for_days(days_left):
    """Return urgency level string based on days remaining."""
    if days_left < 0:
        return 'passed'
    elif days_left <= 3:
        return 'critical'
    elif days_left <= 7:
        return 'urgent'
    elif days_left <= 14:
        return 'soon'
    return 'normal'


def home(request):
    """Home/dashboard view for student applicants."""
    today = _date.today()

    # Default demo data for the template (no login required)
    documents = [
        {'name': 'Form 138', 'status': 'uploaded', 'label': 'Uploaded'},
        {'name': 'Good Moral', 'status': 'pending', 'label': 'Pending'},
        {'name': 'Birth Certificate', 'status': 'done', 'label': 'Done'},
    ]

    steps = [
        {'step_number': 1, 'title': 'Registration', 'status': 'done'},
        {'step_number': 2, 'title': 'Document Review', 'status': 'current'},
        {'step_number': 3, 'title': 'Interview', 'status': 'locked'},
    ]

    upcoming_dates = [
        {'title': 'Entrance Exam', 'date': 'March 15, 2026', 'days_left': 25, 'urgency': 'normal'},
        {'title': 'Interview', 'date': 'April 02, 2026', 'days_left': 43, 'urgency': 'normal'},
    ]

    reminders = [
        {
            'message': 'Please upload your Grade 12 Report Card before Friday.',
            'priority': 'warning',
            'created_at': 'Just now',
            'id': 0,
        },
    ]

    announcements = [
        {
            'title': 'Online Registration Now Open',
            'summary': 'The online registration portal for S.Y. 2026-2027 is now accepting applications.',
            'image': None,
            'published_at': 'Feb 15, 2026',
            'is_new': True,
        },
        {
            'title': 'Campus Orientation Schedule',
            'summary': 'New student assistants are required to attend the campus orientation on March 1.',
            'image': None,
            'published_at': 'Feb 10, 2026',
            'is_new': True,
        },
    ]

    application_status = 'Under Review'
    status_message = "Your documents currently being verified by the Registrar's Office"

    # Try to load real data if user is authenticated
    student = None
    if request.user.is_authenticated:
        try:
            student = StudentProfile.objects.get(user=request.user)
            db_documents = Document.objects.filter(student=student)
            if db_documents.exists():
                documents = [
                    {'name': d.name, 'status': d.status, 'label': d.get_status_display()}
                    for d in db_documents
                ]
            db_steps = ApplicationStep.objects.filter(student=student)
            if db_steps.exists():
                steps = [
                    {'step_number': s.step_number, 'title': s.title, 'status': s.status}
                    for s in db_steps
                ]
            db_reminders = Reminder.objects.filter(student=student, is_active=True)
            if db_reminders.exists():
                reminders = [
                    {
                        'message': r.message,
                        'priority': getattr(r, 'priority', 'info'),
                        'id': r.id,
                        'created_at': r.created_at.strftime('%b %d, %Y'),
                    }
                    for r in db_reminders
                ]
        except StudentProfile.DoesNotExist:
            pass

    # --- Upcoming Dates with countdown & urgency ---
    db_dates = UpcomingDate.objects.filter(is_active=True)
    if db_dates.exists():
        upcoming_dates = []
        for d in db_dates:
            delta = (d.date - today).days
            upcoming_dates.append({
                'title': d.title,
                'date': d.date.strftime('%B %d, %Y'),
                'days_left': max(delta, 0),
                'urgency': _urgency_for_days(delta),
            })

    # --- Announcements with published date & "new" badge ---
    db_announcements = Announcement.objects.filter(is_active=True)[:6]
    if db_announcements.exists():
        seven_days_ago = timezone.now() - timedelta(days=7)
        announcements = [
            {
                'title': a.title,
                'summary': a.summary,
                'image': a.image,
                'published_at': a.published_at.strftime('%b %d, %Y'),
                'is_new': a.published_at >= seven_days_ago,
            }
            for a in db_announcements
        ]

    # Calculate progress percentage
    total_steps = len(steps)
    done_steps = sum(1 for s in steps if s['status'] == 'done')
    progress_percent = int((done_steps / total_steps) * 100) if total_steps > 0 else 0

    context = {
        'student_name': student.full_name if student else 'Juan Dela Cruz',
        'application_id': student.application_id if student else '2024-00123',
        'documents': documents,
        'steps': steps,
        'upcoming_dates': upcoming_dates,
        'reminders': reminders,
        'announcements': announcements,
        'application_status': application_status,
        'status_message': status_message,
        'progress_percent': progress_percent,
    }
    return render(request, 'home/home.html', context)


def available_offices(request):
    """GIS campus map with available offices for student assistants."""
    return render(request, 'home/available_offices.html')


def apply_new(request):
    """Application form for new student assistants."""
    return render(request, 'home/apply_new.html')


def apply_renew(request):
    """Renewal form for existing student assistants."""
    return render(request, 'home/apply_renew.html')


@require_POST
def process_camera_photo(request):
    """Receive a base64 webcam image, process with OpenCV (cv2), and save."""
    try:
        data = json.loads(request.body)
        image_data = data.get('image', '')
        field_name = data.get('field', 'photo')

        # Strip the data URL prefix (e.g. "data:image/png;base64,")
        if ',' in image_data:
            image_data = image_data.split(',', 1)[1]

        # Decode base64 to bytes
        img_bytes = base64.b64decode(image_data)

        # Convert to numpy array and decode with OpenCV
        np_arr = np.frombuffer(img_bytes, np.uint8)
        img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

        if img is None:
            return JsonResponse({'status': 'error', 'message': 'Invalid image data'}, status=400)

        # --- OpenCV processing ---
        # Auto-adjust brightness/contrast
        lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        l = clahe.apply(l)
        img = cv2.merge([l, a, b])
        img = cv2.cvtColor(img, cv2.COLOR_LAB2BGR)

        # Light denoise
        img = cv2.fastNlMeansDenoisingColored(img, None, 5, 5, 7, 21)

        # Save processed image
        upload_dir = os.path.join(settings.MEDIA_ROOT, 'camera_photos')
        os.makedirs(upload_dir, exist_ok=True)

        filename = f"{field_name}_{uuid.uuid4().hex[:8]}.png"
        filepath = os.path.join(upload_dir, filename)
        cv2.imwrite(filepath, img)

        return JsonResponse({
            'status': 'ok',
            'filename': filename,
            'path': f"{settings.MEDIA_URL}camera_photos/{filename}",
        })
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


def staff_login(request):
    """Login page for staff users."""
    if request.user.is_authenticated:
        return redirect('home:staff_dashboard')

    error = None
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None and (user.is_staff or user.is_superuser):
            login(request, user)
            return redirect('home:staff_dashboard')
        elif user is not None:
            error = 'This account does not have staff privileges.'
        else:
            error = 'Invalid username or password. Please try again.'

    return render(request, 'staff/login.html', {'error': error})


def director_login(request):
    """Login page for the Student Director (superuser)."""
    if request.user.is_authenticated:
        return redirect('home:director_dashboard')

    error = None
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None and user.is_superuser:
            login(request, user)
            return redirect('home:director_dashboard')
        elif user is not None:
            error = 'This account does not have director privileges.'
        else:
            error = 'Invalid username or password. Please try again.'

    return render(request, 'director/login.html', {'error': error})


@login_required
def staff_dashboard(request):
    """Staff dashboard view. Accessible by staff users and superusers (director)."""
    if not (request.user.is_staff or request.user.is_superuser):
        return redirect('home:home')

    pending_applications = [
        {'id': 'APP-2024-001', 'student': 'Maria Santos', 'date': 'Feb 10, 2026', 'status': 'pending'},
        {'id': 'APP-2024-002', 'student': 'Jose Rizal Jr.', 'date': 'Feb 12, 2026', 'status': 'pending'},
        {'id': 'APP-2024-003', 'student': 'Ana Reyes', 'date': 'Feb 14, 2026', 'status': 'under_review'},
    ]

    recent_activity = [
        {'action': 'Approved application', 'student': 'Juan Dela Cruz', 'time': '2 hours ago'},
        {'action': 'Requested documents', 'student': 'Pedro Garcia', 'time': '5 hours ago'},
        {'action': 'Scheduled interview', 'student': 'Rosa Flores', 'time': '1 day ago'},
    ]

    stats = {
        'total_applications': 45,
        'pending_review': 12,
        'approved': 28,
        'rejected': 5,
    }

    context = {
        'staff_name': request.user.get_full_name() or request.user.username,
        'pending_applications': pending_applications,
        'recent_activity': recent_activity,
        'stats': stats,
        # Management data
        'reminders': Reminder.objects.all().order_by('-created_at'),
        'upcoming_dates': UpcomingDate.objects.all().order_by('date'),
        'announcements': Announcement.objects.all().order_by('-published_at'),
        # Forms
        'reminder_form': ReminderForm(),
        'date_form': UpcomingDateForm(),
        'announcement_form': AnnouncementForm(),
    }
    return render(request, 'staff/dashboard.html', context)


# ================================================================
#  STAFF CRUD — Reminders
# ================================================================

@login_required
@require_POST
def staff_add_reminder(request):
    if not (request.user.is_staff or request.user.is_superuser):
        return redirect('home:home')
    form = ReminderForm(request.POST)
    if form.is_valid():
        form.save()
    return redirect('home:staff_dashboard')


@login_required
@require_POST
def staff_edit_reminder(request, pk):
    if not (request.user.is_staff or request.user.is_superuser):
        return redirect('home:home')
    reminder = get_object_or_404(Reminder, pk=pk)
    form = ReminderForm(request.POST, instance=reminder)
    if form.is_valid():
        form.save()
    return redirect('home:staff_dashboard')


@login_required
@require_POST
def staff_delete_reminder(request, pk):
    if not (request.user.is_staff or request.user.is_superuser):
        return redirect('home:home')
    get_object_or_404(Reminder, pk=pk).delete()
    return redirect('home:staff_dashboard')


# ================================================================
#  STAFF CRUD — Upcoming Dates
# ================================================================

@login_required
@require_POST
def staff_add_date(request):
    if not (request.user.is_staff or request.user.is_superuser):
        return redirect('home:home')
    form = UpcomingDateForm(request.POST)
    if form.is_valid():
        form.save()
    return redirect('home:staff_dashboard')


@login_required
@require_POST
def staff_edit_date(request, pk):
    if not (request.user.is_staff or request.user.is_superuser):
        return redirect('home:home')
    obj = get_object_or_404(UpcomingDate, pk=pk)
    form = UpcomingDateForm(request.POST, instance=obj)
    if form.is_valid():
        form.save()
    return redirect('home:staff_dashboard')


@login_required
@require_POST
def staff_delete_date(request, pk):
    if not (request.user.is_staff or request.user.is_superuser):
        return redirect('home:home')
    get_object_or_404(UpcomingDate, pk=pk).delete()
    return redirect('home:staff_dashboard')


# ================================================================
#  STAFF CRUD — Announcements
# ================================================================

@login_required
@require_POST
def staff_add_announcement(request):
    if not (request.user.is_staff or request.user.is_superuser):
        return redirect('home:home')
    form = AnnouncementForm(request.POST, request.FILES)
    if form.is_valid():
        form.save()
    return redirect('home:staff_dashboard')


@login_required
@require_POST
def staff_edit_announcement(request, pk):
    if not (request.user.is_staff or request.user.is_superuser):
        return redirect('home:home')
    obj = get_object_or_404(Announcement, pk=pk)
    form = AnnouncementForm(request.POST, request.FILES, instance=obj)
    if form.is_valid():
        form.save()
    return redirect('home:staff_dashboard')


@login_required
@require_POST
def staff_delete_announcement(request, pk):
    if not (request.user.is_staff or request.user.is_superuser):
        return redirect('home:home')
    get_object_or_404(Announcement, pk=pk).delete()
    return redirect('home:staff_dashboard')


@login_required
def director_dashboard(request):
    """Student Director dashboard view. Accessible by superusers only."""
    if not request.user.is_superuser:
        return redirect('home:home')

    assistants = [
        {'name': 'Juan Dela Cruz', 'office': 'Registrar', 'hours': 120, 'status': 'active'},
        {'name': 'Maria Santos', 'office': 'Library', 'hours': 95, 'status': 'active'},
        {'name': 'Pedro Garcia', 'office': 'Guidance', 'hours': 80, 'status': 'probation'},
    ]

    office_summary = [
        {'name': 'Registrar', 'slots': 5, 'filled': 4},
        {'name': 'Library', 'slots': 3, 'filled': 2},
        {'name': 'Guidance Office', 'slots': 4, 'filled': 3},
        {'name': 'Dean\'s Office', 'slots': 2, 'filled': 1},
    ]

    pending_approvals = [
        {'student': 'Ana Reyes', 'type': 'New Application', 'date': 'Feb 15, 2026'},
        {'student': 'Rosa Flores', 'type': 'Renewal', 'date': 'Feb 14, 2026'},
    ]

    stats = {
        'total_assistants': 24,
        'active': 20,
        'on_probation': 3,
        'pending_approval': 4,
    }

    context = {
        'director_name': 'Director',
        'assistants': assistants,
        'office_summary': office_summary,
        'pending_approvals': pending_approvals,
        'stats': stats,
    }
    return render(request, 'director/dashboard.html', context)

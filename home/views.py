from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login
from django.http import HttpResponseForbidden, JsonResponse
from django.views.decorators.http import require_POST
from django.conf import settings
from django.utils import timezone
from .models import (
    StudentProfile, Document, ApplicationStep,
    UpcomingDate, Reminder, Announcement, NewApplication, RenewalApplication, Office,
)
from .forms import ReminderForm, UpcomingDateForm, AnnouncementForm, NewApplicationForm, RenewalApplicationForm
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


def _build_documents_from_app(app):
    """Build document status list from a NewApplication's file fields."""
    doc_fields = [
        ('application_form', 'Application Form'),
        ('id_picture', '2x2 ID Picture'),
        ('barangay_clearance', 'Barangay Clearance'),
        ('parents_itr', "Parent's ITR / Certificate of Indigency"),
        ('enrolment_form', 'Certificate of Enrolment'),
        ('schedule_classes', 'Schedule of Classes'),
        ('proof_insurance', 'Proof of Insurance'),
        ('grades_last_sem', 'Grades Last Semester'),
        ('official_time', 'Official Time'),
    ]
    documents = []
    for field_name, label in doc_fields:
        file_field = getattr(app, field_name)
        if file_field:
            url = file_field.url
            if app.status in ('approved', 'office_assigned'):
                documents.append({'name': label, 'status': 'done', 'label': 'Done', 'url': url})
            else:
                documents.append({'name': label, 'status': 'uploaded', 'label': 'Uploaded', 'url': url})
        else:
            documents.append({'name': label, 'status': 'missing', 'label': 'Missing', 'url': ''})
    return documents


def _build_documents_from_renewal(app):
    """Build document status list from a RenewalApplication's file fields."""
    doc_fields = [
        ('enrolment_form', 'Photocopy of Enrolment Form'),
        ('schedule_classes', 'Schedule of Classes'),
        ('grades_last_sem', 'Grades Last Semester'),
        ('official_time', 'Filled Out Official Time'),
        ('recommendation_letter', 'Recommendation Letter & Budget Allocation'),
        ('evaluation_form', 'Evaluation Form'),
    ]
    documents = []
    for field_name, label in doc_fields:
        file_field = getattr(app, field_name)
        if file_field:
            url = file_field.url
            if app.status in ('approved', 'office_assigned'):
                documents.append({'name': label, 'status': 'done', 'label': 'Done', 'url': url})
            else:
                documents.append({'name': label, 'status': 'uploaded', 'label': 'Uploaded', 'url': url})
        else:
            documents.append({'name': label, 'status': 'missing', 'label': 'Missing', 'url': ''})
    return documents


def _build_steps_from_status(status):
    """Build workflow steps based on application status."""
    step_defs = [
        (1, 'Application Submitted'),
        (2, 'Document Verification'),
        (3, 'Interview & Assessment'),
        (4, 'Office Assignment'),
        (5, 'Final Approval'),
    ]
    # Map status to the step that is currently active (1-indexed)
    status_to_current = {
        'pending': 2,                # submitted, now waiting for doc verification
        'under_review': 3,           # docs verified, now interview/assessment
        'interview_scheduled': 3,    # interview date set, awaiting interview
        'office_assigned': 5,        # office given, waiting for final approval / start date
        'approved': 6,               # all steps done (past the last step)
        'rejected': 0,               # none active
    }
    current_step = status_to_current.get(status, 2)

    steps = []
    for num, title in step_defs:
        if num < current_step:
            steps.append({'step_number': num, 'title': title, 'status': 'done'})
        elif num == current_step:
            steps.append({'step_number': num, 'title': title, 'status': 'current'})
        else:
            steps.append({'step_number': num, 'title': title, 'status': 'locked'})
    return steps


STATUS_DISPLAY_MAP = {
    'pending': ('Pending', 'Your application has been submitted and is awaiting review.'),
    'under_review': ('Under Review', "Your documents are currently being verified by the Registrar's Office."),
    'interview_scheduled': ('Interview Scheduled', 'Your documents have been verified. Please check your scheduled interview date below.'),
    'office_assigned': ('Office Assigned', 'Your interview is complete and you have been assigned to an office. Awaiting final approval with your start date.'),
    'approved': ('Approved', 'Congratulations! Your application has been approved. Check your start date below.'),
    'rejected': ('Rejected', 'Your application was not approved. Please contact the office for details.'),
}


def home(request):
    """Home/dashboard view for student applicants."""
    today = _date.today()

    # ── Collect ALL applications for this visitor ──
    new_apps = []
    renewal_apps = []

    # 1. Check session PKs
    app_pk = request.session.get('application_pk')
    if app_pk:
        obj = NewApplication.objects.filter(pk=app_pk).first()
        if obj:
            new_apps.append(obj)

    renewal_pk = request.session.get('renewal_pk')
    if renewal_pk:
        obj = RenewalApplication.objects.filter(pk=renewal_pk).first()
        if obj:
            renewal_apps.append(obj)

    # 2. If authenticated, also find by email
    if request.user.is_authenticated:
        email_new = NewApplication.objects.filter(
            email=request.user.email
        ).order_by('-submitted_at')
        for a in email_new:
            if a not in new_apps:
                new_apps.append(a)

        email_renewal = RenewalApplication.objects.filter(
            email=request.user.email
        ).order_by('-submitted_at')
        for a in email_renewal:
            if a not in renewal_apps:
                renewal_apps.append(a)

    # 3. If a session-based new app exists, find matching renewals & vice-versa
    session_student_ids = set()
    session_emails = set()
    for a in new_apps:
        session_student_ids.add(a.student_id)
        session_emails.add(a.email)
    for a in renewal_apps:
        session_student_ids.add(a.student_id)
        session_emails.add(a.email)

    if session_student_ids:
        for a in NewApplication.objects.filter(student_id__in=session_student_ids).order_by('-submitted_at'):
            if a not in new_apps:
                new_apps.append(a)
        for a in RenewalApplication.objects.filter(student_id__in=session_student_ids).order_by('-submitted_at'):
            if a not in renewal_apps:
                renewal_apps.append(a)

    if session_emails:
        for a in NewApplication.objects.filter(email__in=session_emails).order_by('-submitted_at'):
            if a not in new_apps:
                new_apps.append(a)
        for a in RenewalApplication.objects.filter(email__in=session_emails).order_by('-submitted_at'):
            if a not in renewal_apps:
                renewal_apps.append(a)

    # ── Build unified application cards ──
    applications = []

    for app in new_apps:
        student_name = f"{app.first_name} {app.last_name}"
        documents = _build_documents_from_app(app)
        steps = _build_steps_from_status(app.status)
        display_status, status_message = STATUS_DISPLAY_MAP.get(
            app.status,
            ('Under Review', "Your documents are currently being verified.")
        )

        total_steps = len(steps)
        done_steps = sum(1 for s in steps if s['status'] == 'done')
        progress_pct = int((done_steps / total_steps) * 100) if total_steps else 0
        total_docs = len(documents)
        completed_docs = sum(1 for d in documents if d['status'] in ('uploaded', 'done'))
        pending_docs = sum(1 for d in documents if d['status'] in ('pending', 'missing'))

        applications.append({
            'obj': app,
            'app_type': 'New Application',
            'app_type_icon': 'fa-file-circle-plus',
            'app_type_class': 'new',
            'student_name': student_name,
            'application_id': app.student_id,
            'documents': documents,
            'steps': steps,
            'application_status': display_status,
            'status_message': status_message,
            'raw_status': app.status,
            'progress_percent': progress_pct,
            'total_steps': total_steps,
            'completed_steps': done_steps,
            'total_docs': total_docs,
            'completed_docs': completed_docs,
            'pending_docs': pending_docs,
            'submitted_at': app.submitted_at,
        })

    for app in renewal_apps:
        documents = _build_documents_from_renewal(app)
        steps = _build_steps_from_status(app.status)
        display_status, status_message = STATUS_DISPLAY_MAP.get(
            app.status,
            ('Under Review', "Your documents are currently being verified.")
        )

        total_steps = len(steps)
        done_steps = sum(1 for s in steps if s['status'] == 'done')
        progress_pct = int((done_steps / total_steps) * 100) if total_steps else 0
        total_docs = len(documents)
        completed_docs = sum(1 for d in documents if d['status'] in ('uploaded', 'done'))
        pending_docs = sum(1 for d in documents if d['status'] in ('pending', 'missing'))

        applications.append({
            'obj': app,
            'app_type': 'Renewal Application',
            'app_type_icon': 'fa-arrows-rotate',
            'app_type_class': 'renewal',
            'student_name': app.full_name,
            'application_id': app.student_id,
            'documents': documents,
            'steps': steps,
            'application_status': display_status,
            'status_message': status_message,
            'raw_status': app.status,
            'progress_percent': progress_pct,
            'total_steps': total_steps,
            'completed_steps': done_steps,
            'total_docs': total_docs,
            'completed_docs': completed_docs,
            'pending_docs': pending_docs,
            'submitted_at': app.submitted_at,
        })

    # Sort all applications by submitted date descending
    applications.sort(key=lambda x: x['submitted_at'], reverse=True)

    has_application = len(applications) > 0

    # ── Upcoming dates ──
    upcoming_dates = []
    db_dates = UpcomingDate.objects.filter(is_active=True)
    if db_dates.exists():
        for d in db_dates:
            delta = (d.date - today).days
            upcoming_dates.append({
                'title': d.title,
                'date': d.date.strftime('%B %d, %Y'),
                'day': d.date.strftime('%d'),
                'month': d.date.strftime('%b').upper(),
                'days_left': max(delta, 0),
                'urgency': _urgency_for_days(delta),
            })

    # ── Reminders ──
    from django.db.models import Q
    reminder_filter = Q(student__isnull=True, is_active=True)
    db_reminders = Reminder.objects.filter(reminder_filter).order_by('-created_at')
    reminders = [
        {
            'message': r.message,
            'priority': r.priority,
            'id': r.id,
            'created_at': r.created_at.strftime('%b %d, %Y'),
        }
        for r in db_reminders
    ]

    # ── Announcements ──
    db_announcements = Announcement.objects.filter(is_active=True)[:6]
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

    context = {
        'applications': applications,
        'has_application': has_application,
        'upcoming_dates': upcoming_dates,
        'reminders': reminders,
        'announcements': announcements,
    }
    return render(request, 'home/home.html', context)


def available_offices(request):
    """GIS campus map with available offices — real data from DB."""
    offices_qs = Office.objects.filter(is_active=True)

    # Count filled slots per office from both application types
    # (students with status office_assigned or approved)
    offices_data = []
    for office in offices_qs:
        filled_new = NewApplication.objects.filter(
            assigned_office=office.name,
            status__in=['office_assigned', 'approved'],
        ).count()
        filled_renewal = RenewalApplication.objects.filter(
            assigned_office=office.name,
            status__in=['office_assigned', 'approved'],
        ).count()
        filled = filled_new + filled_renewal
        available = max(0, office.total_slots - filled)

        if filled >= office.total_slots:
            status = 'full'
        elif available <= 1 and office.total_slots > 1:
            status = 'limited'
        else:
            status = 'open'

        # Get list of assigned students for this office
        assigned_students = []
        for app in NewApplication.objects.filter(
            assigned_office=office.name,
            status__in=['office_assigned', 'approved'],
        ).order_by('last_name'):
            assigned_students.append({
                'name': f"{app.first_name} {app.last_name}",
                'student_id': app.student_id,
                'status': app.get_status_display(),
                'status_key': app.status,
            })
        for app in RenewalApplication.objects.filter(
            assigned_office=office.name,
            status__in=['office_assigned', 'approved'],
        ).order_by('full_name'):
            assigned_students.append({
                'name': app.full_name,
                'student_id': app.student_id,
                'status': app.get_status_display(),
                'status_key': app.status,
            })

        offices_data.append({
            'id': office.pk,
            'name': office.name,
            'building': office.building,
            'room': office.room,
            'hours': office.hours,
            'head': office.head,
            'total_slots': office.total_slots,
            'filled': filled,
            'available': available,
            'status': status,
            'lat': office.latitude,
            'lng': office.longitude,
            'icon': office.icon,
            'description': office.description,
            'students': assigned_students,
        })

    context = {
        'offices_json': json.dumps(offices_data),
        'total_offices': offices_qs.count(),
        'total_open': sum(1 for o in offices_data if o['status'] == 'open'),
        'total_limited': sum(1 for o in offices_data if o['status'] == 'limited'),
        'total_full': sum(1 for o in offices_data if o['status'] == 'full'),
    }
    return render(request, 'home/available_offices.html', context)


def apply_new(request):
    """Application form for new student assistants."""
    if request.method == 'POST':
        form = NewApplicationForm(request.POST, request.FILES)
        if form.is_valid():
            application = form.save()
            request.session['application_pk'] = application.pk
            return redirect('home:home')
    else:
        form = NewApplicationForm()
    return render(request, 'home/apply_new.html', {'form': form})


def apply_renew(request):
    """Renewal form for existing student assistants."""
    if request.method == 'POST':
        form = RenewalApplicationForm(request.POST, request.FILES)
        if form.is_valid():
            application = form.save()
            request.session['renewal_pk'] = application.pk
            return redirect('home:home')
    else:
        form = RenewalApplicationForm()
    return render(request, 'home/apply_renew.html', {'form': form})


def check_student_id(request):
    """AJAX endpoint — check if a student_id already exists in the database."""
    student_id = request.GET.get('student_id', '').strip()
    if not student_id or not student_id.isdigit():
        return JsonResponse({'exists': False})

    # Look up in NewApplication (the most recent matching record)
    app = NewApplication.objects.filter(student_id=student_id).order_by('-submitted_at').first()

    if app:
        # Build a full name from separate fields
        full_name_parts = [app.first_name]
        if app.middle_initial:
            full_name_parts.append(app.middle_initial + '.')
        full_name_parts.append(app.last_name)
        if app.extension_name:
            full_name_parts.append(app.extension_name)
        full_name = ' '.join(full_name_parts)

        return JsonResponse({
            'exists': True,
            'source': 'new',
            'data': {
                'full_name': full_name,
                'first_name': app.first_name,
                'middle_initial': app.middle_initial,
                'last_name': app.last_name,
                'extension_name': app.extension_name or '',
                'email': app.email,
                'contact_number': app.contact_number,
                'address': app.address,
                'course': app.course,
                'year_level': str(app.year_level),
                'semester': app.semester,
                'status': app.get_status_display(),
                'assigned_office': app.assigned_office or '',
            },
        })

    # Also check RenewalApplication
    renewal = RenewalApplication.objects.filter(student_id=student_id).order_by('-submitted_at').first()
    if renewal:
        return JsonResponse({
            'exists': True,
            'source': 'renewal',
            'data': {
                'full_name': renewal.full_name,
                'email': renewal.email,
                'contact_number': renewal.contact_number,
                'address': renewal.address,
                'course': renewal.course,
                'year_level': str(renewal.year_level),
                'semester': renewal.semester,
                'status': renewal.get_status_display(),
                'assigned_office': renewal.assigned_office or '',
                'previous_office': renewal.previous_office or '',
            },
        })

    return JsonResponse({'exists': False})


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

    # ── Real application data from NewApplication + RenewalApplication ──
    new_apps = NewApplication.objects.all()
    renewal_apps = RenewalApplication.objects.all()

    total_new = new_apps.count()
    total_renewal = renewal_apps.count()
    total_applications = total_new + total_renewal

    pending_count = (
        new_apps.filter(status='pending').count()
        + renewal_apps.filter(status='pending').count()
    )
    under_review_count = (
        new_apps.filter(status='under_review').count()
        + renewal_apps.filter(status='under_review').count()
    )
    interview_count = (
        new_apps.filter(status='interview_scheduled').count()
        + renewal_apps.filter(status='interview_scheduled').count()
    )
    office_assigned_count = (
        new_apps.filter(status='office_assigned').count()
        + renewal_apps.filter(status='office_assigned').count()
    )
    approved_count = (
        new_apps.filter(status='approved').count()
        + renewal_apps.filter(status='approved').count()
    )
    rejected_count = (
        new_apps.filter(status='rejected').count()
        + renewal_apps.filter(status='rejected').count()
    )

    stats = {
        'total_applications': total_applications,
        'pending_review': pending_count + under_review_count,
        'interview_scheduled': interview_count,
        'office_assigned': office_assigned_count,
        'approved': approved_count,
        'rejected': rejected_count,
    }

    # ── Build unified list of ALL students (new + renewal) ──
    all_students = []

    for app in new_apps.order_by('-submitted_at'):
        all_students.append({
            'pk': app.pk,
            'app_type': 'New',
            'app_type_class': 'new',
            'student_id': app.student_id,
            'first_name': app.first_name,
            'last_name': app.last_name,
            'middle_initial': app.middle_initial,
            'extension_name': app.extension_name,
            'full_name': f"{app.first_name} {app.middle_initial}. {app.last_name}" + (f" {app.extension_name}" if app.extension_name else ""),
            'email': app.email,
            'course': app.course,
            'year_level_display': app.get_year_level_display(),
            'semester_display': app.get_semester_display(),
            'submitted_at': app.submitted_at,
            'status': app.status,
            'status_display': app.get_status_display(),
            'review_url_name': 'home:staff_review_application',
            'status_url_name': 'home:staff_update_application_status',
        })

    for app in renewal_apps.order_by('-submitted_at'):
        all_students.append({
            'pk': app.pk,
            'app_type': 'Renewal',
            'app_type_class': 'renewal',
            'student_id': app.student_id,
            'first_name': app.full_name.split()[0] if app.full_name else '',
            'last_name': ' '.join(app.full_name.split()[1:]) if app.full_name else '',
            'middle_initial': '',
            'extension_name': '',
            'full_name': app.full_name,
            'email': app.email,
            'course': app.course,
            'year_level_display': app.get_year_level_display(),
            'semester_display': app.get_semester_display(),
            'submitted_at': app.submitted_at,
            'status': app.status,
            'status_display': app.get_status_display(),
            'review_url_name': 'home:staff_review_application',
            'status_url_name': 'home:staff_update_application_status',
            'is_renewal': True,
        })

    # Sort all by submitted_at descending
    all_students.sort(key=lambda x: x['submitted_at'], reverse=True)

    # Applications needing attention (pending + under_review), newest first
    pending_applications = new_apps.filter(
        status__in=['pending', 'under_review']
    ).order_by('-submitted_at')

    # All applications for the full table (keeping for backward compat)
    all_applications = new_apps.order_by('-submitted_at')

    # Recent activity: last 10 approved/rejected with timestamps (both types)
    recent_new = list(new_apps.filter(status__in=['approved', 'rejected']).order_by('-submitted_at')[:10])
    recent_renewal = list(renewal_apps.filter(status__in=['approved', 'rejected']).order_by('-submitted_at')[:10])

    # Normalize renewal apps to have first_name/last_name for template
    for r in recent_renewal:
        r.first_name = r.full_name.split()[0] if r.full_name else ''
        r.last_name = ' '.join(r.full_name.split()[1:]) if r.full_name else ''
        r.app_type = 'Renewal'

    for n in recent_new:
        n.app_type = 'New'

    recent_combined = recent_new + recent_renewal
    recent_combined.sort(key=lambda x: x.submitted_at, reverse=True)
    recent_activity = recent_combined[:10]

    context = {
        'staff_name': request.user.get_full_name() or request.user.username,
        'pending_applications': pending_applications,
        'all_applications': all_applications,
        'all_students': all_students,
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


@login_required
def staff_review_application(request, pk):
    """View full details of a single application."""
    if not (request.user.is_staff or request.user.is_superuser):
        return redirect('home:home')
    app = get_object_or_404(NewApplication, pk=pk)

    # Build document list with status for this application
    doc_fields = [
        ('application_form', 'Application Form'),
        ('id_picture', '2x2 ID Picture'),
        ('barangay_clearance', 'Barangay Clearance'),
        ('parents_itr', "Parent's ITR / Certificate of Indigency"),
        ('enrolment_form', 'Certificate of Enrolment'),
        ('schedule_classes', 'Schedule of Classes'),
        ('proof_insurance', 'Proof of Insurance'),
        ('grades_last_sem', 'Grades Last Semester'),
        ('official_time', 'Official Time'),
    ]
    documents = []
    for field_name, label in doc_fields:
        file_field = getattr(app, field_name)
        documents.append({
            'name': label,
            'field': field_name,
            'file': file_field if file_field else None,
            'uploaded': bool(file_field),
        })

    total_docs = len(documents)
    uploaded_docs = sum(1 for d in documents if d['uploaded'])

    context = {
        'app': app,
        'documents': documents,
        'total_docs': total_docs,
        'uploaded_docs': uploaded_docs,
        'staff_name': request.user.get_full_name() or request.user.username,
    }
    return render(request, 'staff/review_application.html', context)


@login_required
@require_POST
def staff_update_application_status(request, pk):
    """Update the status of an application, optionally with scheduling data."""
    if not (request.user.is_staff or request.user.is_superuser):
        return redirect('home:home')
    app = get_object_or_404(NewApplication, pk=pk)
    new_status = request.POST.get('status')
    if new_status in dict(NewApplication.STATUS_CHOICES):
        app.status = new_status

        # Handle interview scheduling
        if new_status == 'interview_scheduled':
            interview_dt = request.POST.get('interview_date')
            if interview_dt:
                from datetime import datetime as _dt
                try:
                    app.interview_date = _dt.fromisoformat(interview_dt)
                except (ValueError, TypeError):
                    pass

        # Handle office assignment
        if new_status == 'office_assigned':
            office = request.POST.get('assigned_office', '').strip()
            if office:
                app.assigned_office = office

        # Handle final approval with start date
        if new_status == 'approved':
            start = request.POST.get('start_date')
            if start:
                app.start_date = start

        app.save()
    next_url = request.POST.get('next', '')
    if next_url:
        return redirect(next_url)
    return redirect('home:staff_dashboard')


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

    all_apps = NewApplication.objects.all()

    # Applications awaiting interview (interview_scheduled)
    interview_apps = all_apps.filter(
        status='interview_scheduled'
    ).order_by('interview_date')

    # Applications awaiting office assignment (after interview, director assigns)
    # These are still interview_scheduled until director moves them forward
    # Applications that have been assigned an office but not yet approved
    office_assigned_apps = all_apps.filter(
        status='office_assigned'
    ).order_by('-submitted_at')

    # Approved student assistants
    approved_apps = all_apps.filter(status='approved').order_by('-submitted_at')

    # Stats
    stats = {
        'total_applications': all_apps.count(),
        'awaiting_interview': interview_apps.count(),
        'office_assigned': office_assigned_apps.count(),
        'approved': approved_apps.count(),
        'rejected': all_apps.filter(status='rejected').count(),
    }

    offices = Office.objects.filter(is_active=True).order_by('name')

    context = {
        'director_name': request.user.get_full_name() or 'Director',
        'interview_apps': interview_apps,
        'office_assigned_apps': office_assigned_apps,
        'approved_apps': approved_apps,
        'all_apps': all_apps.order_by('-submitted_at'),
        'stats': stats,
        'offices': offices,
    }
    return render(request, 'director/dashboard.html', context)


@login_required
def director_review_application(request, pk):
    """Director's view of a single application — read-only review with director actions."""
    if not request.user.is_superuser:
        return redirect('home:home')
    app = get_object_or_404(NewApplication, pk=pk)

    doc_fields = [
        ('application_form', 'Application Form'),
        ('id_picture', '2x2 ID Picture'),
        ('barangay_clearance', 'Barangay Clearance'),
        ('parents_itr', "Parent's ITR / Certificate of Indigency"),
        ('enrolment_form', 'Certificate of Enrolment'),
        ('schedule_classes', 'Schedule of Classes'),
        ('proof_insurance', 'Proof of Insurance'),
        ('grades_last_sem', 'Grades Last Semester'),
        ('official_time', 'Official Time'),
    ]
    documents = []
    for field_name, label in doc_fields:
        file_field = getattr(app, field_name)
        documents.append({
            'name': label,
            'field': field_name,
            'file': file_field if file_field else None,
            'uploaded': bool(file_field),
        })

    total_docs = len(documents)
    uploaded_docs = sum(1 for d in documents if d['uploaded'])

    offices = Office.objects.filter(is_active=True).order_by('name')

    context = {
        'app': app,
        'documents': documents,
        'total_docs': total_docs,
        'uploaded_docs': uploaded_docs,
        'director_name': request.user.get_full_name() or 'Director',
        'offices': offices,
    }
    return render(request, 'director/review_application.html', context)


@login_required
@require_POST
def director_update_application_status(request, pk):
    """Director-specific status update (office assignment, approval, etc.)."""
    if not request.user.is_superuser:
        return redirect('home:home')
    app = get_object_or_404(NewApplication, pk=pk)
    new_status = request.POST.get('status')
    if new_status in dict(NewApplication.STATUS_CHOICES):
        app.status = new_status

        if new_status == 'office_assigned':
            office = request.POST.get('assigned_office', '').strip()
            if office:
                app.assigned_office = office

        if new_status == 'approved':
            start = request.POST.get('start_date')
            if start:
                app.start_date = start

        if new_status == 'interview_scheduled':
            interview_dt = request.POST.get('interview_date')
            if interview_dt:
                from datetime import datetime as _dt
                try:
                    app.interview_date = _dt.fromisoformat(interview_dt)
                except (ValueError, TypeError):
                    pass

        app.save()
    next_url = request.POST.get('next', '')
    if next_url:
        return redirect(next_url)
    return redirect('home:director_dashboard')

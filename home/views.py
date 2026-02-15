from django.shortcuts import render
from .models import (
    StudentProfile, Document, ApplicationStep,
    UpcomingDate, Reminder, Announcement,
)


def home(request):
    """Home/dashboard view for student applicants."""
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
        {'title': 'Entrance Exam', 'date': 'March 15'},
        {'title': 'Interview', 'date': 'April 02'},
    ]

    reminders = [
        {'message': 'Reminder! Please upload your Grade 12 Report Card before Friday'},
    ]

    announcements = [
        {
            'title': 'Online Registration',
            'summary': 'Campus Expo: Intra-Year Agency of Asia & Europe, Sorting the next 2019 Council Crisis.',
        },
        {
            'title': 'More Announcements',
            'summary': "CenterFresh's also light Delu, Home of Malaysia tali Energyshare, Diploma 101 Provisions.",
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
                reminders = [{'message': r.message} for r in db_reminders]
        except StudentProfile.DoesNotExist:
            pass

    db_dates = UpcomingDate.objects.filter(is_active=True)
    if db_dates.exists():
        upcoming_dates = [
            {'title': d.title, 'date': d.date.strftime('%B %d')}
            for d in db_dates
        ]

    db_announcements = Announcement.objects.filter(is_active=True)[:4]
    if db_announcements.exists():
        announcements = [
            {'title': a.title, 'summary': a.summary, 'image': a.image}
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

from django.shortcuts import render


def staff_dashboard(request):
    """Staff dashboard view."""
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
        'staff_name': 'Staff Member',
        'pending_applications': pending_applications,
        'recent_activity': recent_activity,
        'stats': stats,
    }
    return render(request, 'staff/dashboard.html', context)

from django.shortcuts import render


def director_dashboard(request):
    """Student Director dashboard view."""
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

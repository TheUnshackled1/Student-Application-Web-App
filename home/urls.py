from django.urls import path
from . import views

app_name = 'home'

urlpatterns = [
    path('', views.home, name='home'),
    path('offices/', views.available_offices, name='available_offices'),
    path('apply/new/', views.apply_new, name='apply_new'),
    path('apply/renew/', views.apply_renew, name='apply_renew'),
    path('apply/check-student/', views.check_student_id, name='check_student_id'),
    path('apply/camera-photo/', views.process_camera_photo, name='process_camera_photo'),
    path('staff/login/', views.staff_login, name='staff_login'),
    path('director/login/', views.director_login, name='director_login'),
    path('staff/', views.staff_dashboard, name='staff_dashboard'),
    path('staff/applications/<int:pk>/review/', views.staff_review_application, name='staff_review_application'),
    path('staff/applications/<int:pk>/status/', views.staff_update_application_status, name='staff_update_application_status'),
    path('director/', views.director_dashboard, name='director_dashboard'),
    path('director/applications/<int:pk>/review/', views.director_review_application, name='director_review_application'),
    path('director/applications/<int:pk>/status/', views.director_update_application_status, name='director_update_application_status'),

    # ---- Staff CRUD: Reminders ----
    path('staff/reminders/add/', views.staff_add_reminder, name='staff_add_reminder'),
    path('staff/reminders/<int:pk>/edit/', views.staff_edit_reminder, name='staff_edit_reminder'),
    path('staff/reminders/<int:pk>/delete/', views.staff_delete_reminder, name='staff_delete_reminder'),

    # ---- Staff CRUD: Upcoming Dates ----
    path('staff/dates/add/', views.staff_add_date, name='staff_add_date'),
    path('staff/dates/<int:pk>/edit/', views.staff_edit_date, name='staff_edit_date'),
    path('staff/dates/<int:pk>/delete/', views.staff_delete_date, name='staff_delete_date'),

    # ---- Staff CRUD: Announcements ----
    path('staff/announcements/add/', views.staff_add_announcement, name='staff_add_announcement'),
    path('staff/announcements/<int:pk>/edit/', views.staff_edit_announcement, name='staff_edit_announcement'),
    path('staff/announcements/<int:pk>/delete/', views.staff_delete_announcement, name='staff_delete_announcement'),

    # ---- Staff CRUD: Offices ----
    path('staff/offices/add/', views.staff_add_office, name='staff_add_office'),
    path('staff/offices/<int:pk>/edit/', views.staff_edit_office, name='staff_edit_office'),
    path('staff/offices/<int:pk>/delete/', views.staff_delete_office, name='staff_delete_office'),
    path('staff/offices/<int:pk>/json/', views.staff_get_office_json, name='staff_get_office_json'),

    # ---- Director: Move Office Marker ----
    path('director/offices/<int:pk>/move/', views.director_move_office, name='director_move_office'),
]

from django.urls import path
from . import views

app_name = 'home'

urlpatterns = [
    path('', views.home, name='home'),
    path('offices/', views.available_offices, name='available_offices'),
    path('apply/new/', views.apply_new, name='apply_new'),
    path('apply/renew/', views.apply_renew, name='apply_renew'),
    path('apply/camera-photo/', views.process_camera_photo, name='process_camera_photo'),
    path('staff/login/', views.staff_login, name='staff_login'),
    path('director/login/', views.director_login, name='director_login'),
    path('staff/', views.staff_dashboard, name='staff_dashboard'),
    path('director/', views.director_dashboard, name='director_dashboard'),
]

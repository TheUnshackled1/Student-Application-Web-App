from django.urls import path
from . import views

app_name = 'home'

urlpatterns = [
    path('', views.home, name='home'),
    path('staff/', views.staff_dashboard, name='staff_dashboard'),
    path('director/', views.director_dashboard, name='director_dashboard'),
]

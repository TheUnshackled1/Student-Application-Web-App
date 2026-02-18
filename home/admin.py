from django.contrib import admin
from .models import (
    StudentProfile, Document, ApplicationStep,
    UpcomingDate, Reminder, Announcement, NewApplication, RenewalApplication, Office,
)


@admin.register(StudentProfile)
class StudentProfileAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'application_id', 'user', 'created_at')
    search_fields = ('full_name', 'application_id')


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ('name', 'student', 'status', 'uploaded_at')
    list_filter = ('status',)


@admin.register(ApplicationStep)
class ApplicationStepAdmin(admin.ModelAdmin):
    list_display = ('student', 'step_number', 'title', 'status')
    list_filter = ('status',)


@admin.register(UpcomingDate)
class UpcomingDateAdmin(admin.ModelAdmin):
    list_display = ('title', 'date', 'is_active')


@admin.register(Reminder)
class ReminderAdmin(admin.ModelAdmin):
    list_display = ('message', 'student', 'is_active', 'created_at')


@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    list_display = ('title', 'published_at', 'is_active')
    list_filter = ('is_active',)


@admin.register(NewApplication)
class NewApplicationAdmin(admin.ModelAdmin):
    list_display = ('student_id', 'first_name', 'last_name', 'course', 'status', 'submitted_at')
    list_filter = ('status', 'gender', 'year_level', 'semester')
    search_fields = ('first_name', 'last_name', 'student_id', 'email')


@admin.register(RenewalApplication)
class RenewalApplicationAdmin(admin.ModelAdmin):
    list_display = ('student_id', 'full_name', 'course', 'status', 'submitted_at')
    list_filter = ('status', 'year_level', 'semester')
    search_fields = ('full_name', 'student_id', 'email')


@admin.register(Office)
class OfficeAdmin(admin.ModelAdmin):
    list_display = ('name', 'building', 'room', 'head', 'total_slots', 'is_active')
    list_filter = ('is_active', 'building')
    search_fields = ('name', 'building', 'head')

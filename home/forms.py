from django import forms
from .models import Reminder, UpcomingDate, Announcement, NewApplication


class ReminderForm(forms.ModelForm):
    class Meta:
        model = Reminder
        fields = ['message', 'priority', 'is_active']
        widgets = {
            'message': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Enter reminder message...',
            }),
            'priority': forms.Select(attrs={'class': 'form-select'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class UpcomingDateForm(forms.ModelForm):
    class Meta:
        model = UpcomingDate
        fields = ['title', 'date', 'is_active']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g. Entrance Exam',
            }),
            'date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
            }),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class AnnouncementForm(forms.ModelForm):
    class Meta:
        model = Announcement
        fields = ['title', 'summary', 'image', 'is_active']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Announcement title...',
            }),
            'summary': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Write the announcement details...',
            }),
            'image': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class NewApplicationForm(forms.ModelForm):
    class Meta:
        model = NewApplication
        fields = [
            'first_name', 'middle_initial', 'last_name', 'extension_name',
            'date_of_birth', 'gender', 'contact_number', 'email', 'address',
            'student_id', 'course', 'year_level', 'semester',
            'application_form', 'id_picture', 'barangay_clearance',
            'parents_itr', 'enrolment_form', 'schedule_classes',
            'proof_insurance', 'grades_last_sem', 'official_time',
        ]
        widgets = {
            'first_name': forms.TextInput(attrs={
                'class': 'form-control', 'maxlength': 15,
                'placeholder': 'Enter first name',
            }),
            'middle_initial': forms.TextInput(attrs={
                'class': 'form-control', 'maxlength': 1,
                'placeholder': 'M',
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'form-control', 'maxlength': 10,
                'placeholder': 'Enter last name',
            }),
            'extension_name': forms.TextInput(attrs={
                'class': 'form-control', 'maxlength': 5,
                'placeholder': 'Jr, Sr, III',
            }),
            'date_of_birth': forms.DateInput(attrs={
                'class': 'form-control', 'type': 'date',
            }),
            'gender': forms.Select(attrs={'class': 'form-select'}),
            'contact_number': forms.TextInput(attrs={
                'class': 'form-control', 'maxlength': 11,
                'placeholder': '09XXXXXXXXX', 'inputmode': 'numeric',
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'name@example.com',
            }),
            'address': forms.Textarea(attrs={
                'class': 'form-control', 'rows': 2, 'id': 'id_address',
                'placeholder': 'Home address (click Detect to auto-fill)',
            }),
            'student_id': forms.TextInput(attrs={
                'class': 'form-control', 'maxlength': 8,
                'placeholder': '12345678', 'inputmode': 'numeric',
            }),
            'course': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g. BSIT, BSCS, BEED',
            }),
            'year_level': forms.Select(attrs={'class': 'form-select'}),
            'semester': forms.Select(attrs={'class': 'form-select'}),
        }

    def clean_contact_number(self):
        val = self.cleaned_data['contact_number']
        if not val.isdigit():
            raise forms.ValidationError('Contact number must contain only digits.')
        if len(val) != 11:
            raise forms.ValidationError('Contact number must be exactly 11 digits.')
        return val

    def clean_student_id(self):
        val = self.cleaned_data['student_id']
        if not val.isdigit():
            raise forms.ValidationError('Student ID must contain only digits.')
        if len(val) > 8:
            raise forms.ValidationError('Student ID must be at most 8 digits.')
        return val

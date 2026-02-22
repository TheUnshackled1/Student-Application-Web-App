from django import forms
from .models import Reminder, UpcomingDate, Announcement, NewApplication, RenewalApplication, Office


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
            'student_id', 'course', 'year_level', 'semester', 'preferred_office',
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
            'preferred_office': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Populate preferred_office with active offices that still have open slots
        active_offices = Office.objects.filter(is_active=True).order_by('name')
        self.fields['preferred_office'].queryset = active_offices
        self.fields['preferred_office'].empty_label = 'Select preferred office'

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

    def clean_date_of_birth(self):
        from datetime import date
        dob = self.cleaned_data['date_of_birth']
        today = date.today()
        age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
        if age < 18:
            raise forms.ValidationError('You must be at least 18 years old to apply. Only college-level students are eligible.')
        return dob


class RenewalApplicationForm(forms.ModelForm):
    class Meta:
        model = RenewalApplication
        fields = [
            'student_id', 'full_name', 'email', 'contact_number', 'address',
            'course', 'year_level', 'semester',
            'previous_office', 'preferred_office', 'hours_rendered', 'supervisor_name',
            'enrolment_form', 'schedule_classes', 'grades_last_sem',
            'official_time', 'recommendation_letter', 'evaluation_form',
        ]
        widgets = {
            'student_id': forms.TextInput(attrs={
                'class': 'form-control', 'maxlength': 8,
                'placeholder': '12345678', 'inputmode': 'numeric',
            }),
            'full_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Juan A. Dela Cruz',
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'name@example.com',
            }),
            'contact_number': forms.TextInput(attrs={
                'class': 'form-control', 'maxlength': 11,
                'placeholder': '09XXXXXXXXX', 'inputmode': 'numeric',
            }),
            'address': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Street, Barangay, City / Municipality, Province',
            }),
            'course': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g. BSIT, BSCS, BEED',
            }),
            'year_level': forms.Select(attrs={'class': 'form-select'}),
            'semester': forms.Select(attrs={'class': 'form-select'}),
            'previous_office': forms.Select(attrs={'class': 'form-select'}),
            'preferred_office': forms.Select(attrs={'class': 'form-select'}),
            'hours_rendered': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g. 120',
            }),
            'supervisor_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Full name of your previous supervisor',
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        active_offices = Office.objects.filter(is_active=True).order_by('name')
        self.fields['previous_office'].queryset = active_offices
        self.fields['previous_office'].empty_label = 'Select office'
        self.fields['preferred_office'].queryset = active_offices
        self.fields['preferred_office'].empty_label = 'Select office'

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


# ================================================================
#  OFFICE FORM
# ================================================================

ICON_CHOICES = [
    ('fa-solid fa-building', 'Building'),
    ('fa-solid fa-book', 'Book / Library'),
    ('fa-solid fa-user-tie', 'User / Office Head'),
    ('fa-solid fa-gavel', 'Gavel / Dean'),
    ('fa-solid fa-calculator', 'Calculator / Accounting'),
    ('fa-solid fa-cash-register', 'Cash Register / Cashier'),
    ('fa-solid fa-users', 'Users / Student Affairs'),
    ('fa-solid fa-laptop-code', 'Laptop / ICT'),
    ('fa-solid fa-flask', 'Flask / Research'),
    ('fa-solid fa-id-card', 'ID Card / HR'),
    ('fa-solid fa-hand-holding-heart', 'Heart / Guidance'),
    ('fa-solid fa-graduation-cap', 'Grad Cap / Academic'),
    ('fa-solid fa-clipboard-list', 'Clipboard / Registrar'),
    ('fa-solid fa-shield-halved', 'Shield / Security'),
    ('fa-solid fa-stethoscope', 'Stethoscope / Clinic'),
    ('fa-solid fa-tools', 'Tools / Maintenance'),
]


class OfficeForm(forms.ModelForm):
    class Meta:
        model = Office
        fields = [
            'name', 'building', 'room', 'hours', 'head',
            'total_slots', 'latitude', 'longitude', 'icon', 'description', 'is_active',
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g. Registrar\u2019s Office',
            }),
            'building': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g. Administration Building',
            }),
            'room': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g. Ground Floor, Room 101',
            }),
            'hours': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Mon\u2013Fri, 8:00 AM \u2013 5:00 PM',
            }),
            'head': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Head / Supervisor name',
            }),
            'total_slots': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1', 'max': '50',
                'placeholder': '3',
            }),
            'latitude': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.00001', 'id': 'id_latitude',
            }),
            'longitude': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.00001', 'id': 'id_longitude',
            }),
            'icon': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Brief description of the office\u2026',
            }),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['icon'].choices = ICON_CHOICES
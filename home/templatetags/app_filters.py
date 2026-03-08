from django import template

register = template.Library()


@register.filter
def get_item(dictionary, key):
    """Retrieve a value from a dict by key in templates.

    Usage: {{ mydict|get_item:key_var }}
    """
    if isinstance(dictionary, dict):
        return dictionary.get(key, [])
    return []


@register.filter
def contains(value_list, item):
    """Check if item is in list. Returns True/False.

    Usage: {% if my_list|contains:item %}
    """
    if isinstance(value_list, (list, tuple)):
        return item in value_list
    return False


DOC_FIELD_LABELS = {
    'application_form': 'Application Form',
    'id_picture': '2x2 ID Picture',
    'barangay_clearance': 'Barangay Clearance',
    'parents_itr': "Parent's ITR / Certificate of Indigency",
    'enrolment_form': 'Certificate of Enrolment',
    'schedule_classes': 'Schedule of Classes',
    'proof_insurance': 'Proof of Insurance',
    'grades_last_sem': 'Grades Last Semester',
    'official_time': 'Official Time',
    'recommendation_letter': 'Recommendation Letter',
    'evaluation_form': 'Evaluation Form',
    'id_picture_renewal': 'Updated 2x2 ID Picture',
}


@register.filter
def doc_label(field_name):
    """Convert a document field name to a human-readable label."""
    return DOC_FIELD_LABELS.get(field_name, field_name.replace('_', ' ').title())

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

from django import template # type: ignore

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """Custom filter to get an item from a dictionary by key."""
    return dictionary.get(key)

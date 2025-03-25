from django import template
from django.db.models import Avg

register = template.Library()

@register.filter
def time_format(seconds):
    """Format seconds into minutes and seconds."""
    minutes = seconds // 60
    remaining_seconds = seconds % 60
    
    if minutes > 0:
        return f"{minutes}m {remaining_seconds}s"
    return f"{remaining_seconds}s"

@register.filter
def correct_count(responses):
    """Count the number of correct responses."""
    return sum(1 for response in responses if response.is_correct)

@register.filter
def avg_response_time(responses):
    """Calculate average response time."""
    if not responses:
        return 0
    return sum(response.response_time for response in responses) / len(responses)

@register.filter
def get_item(dictionary, key):
    """Get an item from a dictionary."""
    return dictionary.get(key) 
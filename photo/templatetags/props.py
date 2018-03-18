from django import template
from django.template.defaultfilters import stringfilter


register = template.Library()

@register.filter(name='get_photo_prop')
def get_photo_prop(photo, property):
    return photo.get_prop(property)
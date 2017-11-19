from django import template
from django.template.defaultfilters import stringfilter

register = template.Library()

@register.filter(name='get_thumbnail')
def get_thumbnail(photo, max_size):
    return photo.get_thumbnail(photo, max_size)

@register.filter(name='get_cover')
def get_cover(album, max_size):
    return album.get_cover(album, max_size)
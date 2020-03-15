from django import template

register = template.Library()


@register.filter(name='get_photo_prop')
def get_photo_prop(photo, property):
    return photo.get_prop(property)

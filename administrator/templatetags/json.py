import json as j

from django import template

register = template.Library()


@register.filter
def json(data):
    return j.dumps(data)

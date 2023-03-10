from django import template

register = template.Library()


@register.filter
def salutation_name(user, *args, **kwargs):
    if hasattr(user, "customer"):
        return user.customer.first_name
    return "Customer"

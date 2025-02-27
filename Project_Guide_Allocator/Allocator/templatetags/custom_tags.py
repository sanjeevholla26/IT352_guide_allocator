from django import template

register = template.Library()

@register.filter
def has_permission(user, perm_str):
    fun, app = perm_str.split(',')
    return user.has_permission(fun, app)

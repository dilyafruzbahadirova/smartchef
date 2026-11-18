from django import template
from recipes.cooking import decode_recipe
register = template.Library()
@register.filter
def structured(value):
    return decode_recipe(value)

import json

PREFIX = "SMARTCHEF_JSON_V1\n"

class RecipeValidationError(ValueError):
    pass

def _pairs(items):
    result = {}
    for key, value in items:
        if key in result:
            raise RecipeValidationError("Duplicate JSON key")
        result[key] = value
    return result

def validate_recipe(raw):
    if not isinstance(raw, str) or len(raw) > 30000:
        raise RecipeValidationError("Recipe response exceeds 30000 characters")
    try:
        obj = json.loads(raw, object_pairs_hook=_pairs)
    except (ValueError, TypeError) as exc:
        raise RecipeValidationError("Invalid JSON") from exc
    if type(obj) is not dict or set(obj) != {"title", "ingredients", "steps"}:
        raise RecipeValidationError("Invalid recipe fields")
    title = obj["title"]
    if type(title) is not str or not 1 <= len(title.strip()) <= 120:
        raise RecipeValidationError("Invalid title")
    for key, max_items, max_chars in (("ingredients", 24, 200), ("steps", 12, 1200)):
        values = obj[key]
        if type(values) is not list or not 1 <= len(values) <= max_items:
            raise RecipeValidationError("Invalid " + key)
        if any(type(x) is not str or not 1 <= len(x.strip()) <= max_chars for x in values):
            raise RecipeValidationError("Invalid item in " + key)
    return obj

def encode_recipe(obj):
    return PREFIX + json.dumps(obj, ensure_ascii=False)

def decode_recipe(value):
    if not isinstance(value, str) or not value.startswith(PREFIX):
        return None
    try:
        return validate_recipe(value[len(PREFIX):])
    except RecipeValidationError:
        return None

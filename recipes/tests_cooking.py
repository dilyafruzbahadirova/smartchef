from django.test import SimpleTestCase
from .cooking import validate_recipe, encode_recipe, decode_recipe, RecipeValidationError

class CookingJSONTests(SimpleTestCase):
    def test_valid(self):
        data=validate_recipe('{"title":"Омлет","ingredients":["2 жұмыртқа"],"steps":["Араластырыңыз"]}')
        self.assertEqual(decode_recipe(encode_recipe(data)),data)
    def test_duplicate_keys(self):
        with self.assertRaises(RecipeValidationError):
            validate_recipe('{"title":"a","title":"b","ingredients":["x"],"steps":["y"]}')
    def test_extra_keys(self):
        with self.assertRaises(RecipeValidationError):
            validate_recipe('{"title":"a","ingredients":["x"],"steps":["y"],"tip":"z"}')
    def test_wrong_types(self):
        with self.assertRaises(RecipeValidationError):
            validate_recipe('{"title":2,"ingredients":["x"],"steps":["y"]}')
    def test_legacy(self):
        self.assertIsNone(decode_recipe("Бұрынғы рецепт. Бірінші қадам."))

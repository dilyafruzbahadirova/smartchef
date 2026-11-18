from unittest.mock import patch, Mock
from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from .models import SavedRecipe
from .cooking import encode_recipe


class ProposalOnlyTests(TestCase):
    def setUp(self):
        self.original = encode_recipe({"title": "Омлет", "ingredients": ["2 жұмыртқа"], "steps": ["Араластыру"]})
        self.item = SavedRecipe.objects.create(products="жұмыртқа", minutes=15, language="kk", recipe=self.original)
        self.url = reverse("recipes:revise_recipe", args=[self.item.token])

    def test_invalid_instruction_does_not_change_recipe(self):
        response = self.client.post(self.url, {"action": "request", "instruction": "ab"})
        self.assertEqual(response.status_code, 200)
        self.item.refresh_from_db()
        self.assertEqual(self.item.recipe, self.original)

    def test_accept_without_pending_is_rejected(self):
        response = self.client.post(self.url, {"action": "accept"})
        self.assertEqual(response.status_code, 400)

    def test_html_is_escaped(self):
        self.item.recipe = '<script>alert(1)</script>'
        self.item.save(update_fields=["recipe"])
        response = self.client.get(self.url)
        self.assertContains(response, '&lt;script&gt;alert(1)&lt;/script&gt;')

    @patch("google.genai.Client")
    @patch("recipes.views.dotenv_values", return_value={"GEMINI_API_KEY": "fake", "GEMINI_MODEL": "test"})
    def test_pending_has_required_fields_and_does_not_write(self, _, client):
        client.return_value.interactions.create.return_value.output_text = '{"title":"Омлет 2","ingredients":["су"],"steps":["Пісіру"]}'
        response = self.client.post(self.url, {"action": "request", "instruction": "Суды қос"})
        self.assertEqual(response.status_code, 200)
        pending = self.client.session[f"smartchef_revision_{self.item.pk}"]
        self.assertEqual(pending["recipe_id"], self.item.pk)
        self.assertEqual(pending["original_text"], self.original)
        self.assertEqual(pending["candidate"]["title"], "Омлет 2")
        self.assertGreaterEqual(len(pending["token"]), 32)
        self.assertGreater(pending["expires_at"], timezone.now().timestamp())
        self.item.refresh_from_db()
        self.assertEqual(self.item.recipe, self.original)

    @patch("google.genai.Client")
    @patch("recipes.views.dotenv_values", return_value={"GEMINI_API_KEY": "fake"})
    def test_duplicate_json_rejected(self, _, client):
        client.return_value.interactions.create.return_value.output_text = '{"title":"a","title":"b","ingredients":["x"],"steps":["y"]}'
        response = self.client.post(self.url, {"action": "request", "instruction": "Өзгерт"})
        self.assertEqual(response.status_code, 200)
        self.assertNotIn(f"smartchef_revision_{self.item.pk}", self.client.session)

    def _seed_pending(self, *, original=None, expires_at=None):
        import secrets
        from datetime import timedelta
        from django.utils import timezone
        pending = {
            "recipe_id": self.item.pk,
            "original_text": original if original is not None else self.original,
            "candidate": {"title": "Жаңа омлет", "ingredients": ["су"], "steps": ["Пісіру"]},
            "token": secrets.token_urlsafe(32),
            "expires_at": expires_at if expires_at is not None else (timezone.now() + timedelta(minutes=20)).timestamp(),
        }
        session = self.client.session
        session[f"smartchef_revision_{self.item.pk}"] = pending
        session.save()
        return pending

    def test_accept_then_replay_and_undo_once(self):
        pending = self._seed_pending()
        data = {"action": "accept", "pending_token": pending["token"]}
        self.assertEqual(self.client.post(self.url, data).status_code, 200)
        self.item.refresh_from_db()
        self.assertNotEqual(self.item.recipe, self.original)
        accepted = self.item.recipe
        self.client.post(self.url, data)
        self.item.refresh_from_db()
        self.assertEqual(self.item.recipe, accepted)
        undo = self.client.session[f"smartchef_revision_undo_{self.item.pk}"]
        undo_data = {"action": "undo", "pending_token": undo["token"]}
        self.client.post(self.url, undo_data)
        self.item.refresh_from_db()
        self.assertEqual(self.item.recipe, self.original)
        self.client.post(self.url, undo_data)
        self.item.refresh_from_db()
        self.assertEqual(self.item.recipe, self.original)

    def test_reject_does_not_write(self):
        pending = self._seed_pending()
        self.client.post(self.url, {"action": "reject", "pending_token": pending["token"]})
        self.item.refresh_from_db()
        self.assertEqual(self.item.recipe, self.original)
        self.assertNotIn(f"smartchef_revision_{self.item.pk}", self.client.session)

    def test_stale_and_expired_do_not_write(self):
        from datetime import timedelta
        pending = self._seed_pending()
        self.item.recipe = "changed externally"
        self.item.save(update_fields=["recipe"])
        self.client.post(self.url, {"action": "accept", "pending_token": pending["token"]})
        self.item.refresh_from_db()
        self.assertEqual(self.item.recipe, "changed externally")
        self.item.recipe = self.original
        self.item.save(update_fields=["recipe"])
        pending = self._seed_pending(expires_at=(timezone.now() - timedelta(seconds=1)).timestamp())
        self.client.post(self.url, {"action": "accept", "pending_token": pending["token"]})
        self.item.refresh_from_db()
        self.assertEqual(self.item.recipe, self.original)

    def test_other_session_cannot_accept(self):
        from django.test import Client
        pending = self._seed_pending()
        stranger = Client()
        stranger.post(self.url, {"action": "accept", "pending_token": pending["token"]})
        self.item.refresh_from_db()
        self.assertEqual(self.item.recipe, self.original)

    def test_undo_stale_does_not_overwrite_external_edit(self):
        pending = self._seed_pending()
        self.client.post(self.url, {"action": "accept", "pending_token": pending["token"]})
        undo = self.client.session[f"smartchef_revision_undo_{self.item.pk}"]
        self.item.refresh_from_db()
        self.item.recipe = "external change"
        self.item.save(update_fields=["recipe"])
        self.client.post(self.url, {"action": "undo", "pending_token": undo["token"]})
        self.item.refresh_from_db()
        self.assertEqual(self.item.recipe, "external change")

    def test_undo_wrong_token_or_recipe_id_does_not_write(self):
        pending = self._seed_pending()
        self.client.post(self.url, {"action": "accept", "pending_token": pending["token"]})
        self.item.refresh_from_db()
        accepted = self.item.recipe
        response = self.client.post(self.url, {"action": "undo", "pending_token": "wrong"})
        self.assertEqual(response.status_code, 200)
        self.item.refresh_from_db()
        self.assertEqual(self.item.recipe, accepted)
        other = SavedRecipe.objects.create(products="x", minutes=15, language="kk", recipe=self.original)
        other_url = reverse("recipes:revise_recipe", args=[other.token])
        undo = self.client.session[f"smartchef_revision_undo_{self.item.pk}"]
        self.client.post(other_url, {"action": "undo", "pending_token": undo["token"]})
        other.refresh_from_db()
        self.assertEqual(other.recipe, self.original)

    def test_undo_expired_does_not_write(self):
        pending = self._seed_pending()
        self.client.post(self.url, {"action": "accept", "pending_token": pending["token"]})
        self.item.refresh_from_db()
        accepted = self.item.recipe
        session = self.client.session
        key = f"smartchef_revision_undo_{self.item.pk}"
        undo = session[key]
        undo["expires_at"] = timezone.now().timestamp() - 1
        session[key] = undo
        session.save()
        self.client.post(self.url, {"action": "undo", "pending_token": undo["token"]})
        self.item.refresh_from_db()
        self.assertEqual(self.item.recipe, accepted)

    def test_csrf_required_for_mutations(self):
        protected = Client(enforce_csrf_checks=True)
        pending = self._seed_pending()
        response = protected.post(self.url, {"action": "accept", "pending_token": pending["token"]})
        self.assertEqual(response.status_code, 403)
        response = protected.post(self.url, {"action": "reject", "pending_token": pending["token"]})
        self.assertEqual(response.status_code, 403)
        response = protected.post(self.url, {"action": "undo", "pending_token": "x"})
        self.assertEqual(response.status_code, 403)

    @patch("google.genai.Client")
    @patch("recipes.views.dotenv_values", return_value={"GEMINI_API_KEY": "fake", "GEMINI_MODEL": "test"})
    def test_provider_error_does_not_write(self, _, client):
        client.return_value.interactions.create.side_effect = TimeoutError("timed out")
        response = self.client.post(self.url, {"action": "request", "instruction": "Суды қос"})
        self.assertEqual(response.status_code, 200)
        self.item.refresh_from_db()
        self.assertEqual(self.item.recipe, self.original)
        self.assertNotIn(f"smartchef_revision_{self.item.pk}", self.client.session)

    def test_undo_only_last_accept_snapshot(self):
        first = self._seed_pending()
        self.client.post(self.url, {"action": "accept", "pending_token": first["token"]})
        self.item.refresh_from_db()
        first_accepted = self.item.recipe
        second = self._seed_pending(original=first_accepted)
        self.client.post(self.url, {"action": "accept", "pending_token": second["token"]})
        undo = self.client.session[f"smartchef_revision_undo_{self.item.pk}"]
        self.client.post(self.url, {"action": "undo", "pending_token": undo["token"]})
        self.item.refresh_from_db()
        self.assertEqual(self.item.recipe, first_accepted)

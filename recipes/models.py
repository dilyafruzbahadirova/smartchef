import uuid
from django.db import models


class UserMemory(models.Model):
    """
    Долгосрочная память SmartChef о пользователе.
    Пользователь определяется через Django session.
    """

    session_id = models.CharField(
        max_length=100,
        unique=True
    )

    preferred_language = models.CharField(
        max_length=2,
        default="kk"
    )

    vegetarian = models.BooleanField(
        default=False
    )

    preferences = models.TextField(
        blank=True,
        default=""
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    def __str__(self):
        return f"Memory: {self.session_id}"


class RecipeHistory(models.Model):
    """
    История успешно созданных рецептов пользователя.
    """

    session_id = models.CharField(
        max_length=100,
        db_index=True
    )

    products = models.TextField()

    minutes = models.CharField(
        max_length=2
    )

    vegetarian = models.BooleanField(
        default=False
    )

    language = models.CharField(
        max_length=2,
        default="kk"
    )

    recipe = models.TextField()

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Recipe: {self.session_id} | {self.created_at}"

class SavedRecipe(models.Model):
    token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    products = models.CharField(max_length=500)
    recipe = models.TextField()
    language = models.CharField(max_length=2, default="kk")
    minutes = models.PositiveSmallIntegerField(default=30)
    vegetarian = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at", "-id"]

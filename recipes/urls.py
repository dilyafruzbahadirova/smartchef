from django.urls import path
from . import views
app_name = "recipes"
urlpatterns = [
    path("", views.index, name="index"),
    path("save/", views.save_recipe, name="save_recipe"),
    path("saved/", views.saved_recipes, name="saved_recipes"),
    path("cook/", views.cook, name="cook"),
    path("saved/<uuid:token>/revise/", views.revise_recipe, name="revise_recipe"),
]

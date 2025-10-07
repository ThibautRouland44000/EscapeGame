from django.urls import path
from . import views

urlpatterns = [
    path("<uuid:team_uuid>/", views.museum_puzzle, name="museum_puzzle"),
]

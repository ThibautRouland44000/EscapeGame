from django.urls import path
from . import views

urlpatterns = [
    path("<uuid:team_uuid>/", views.museum_puzzle, name="museum_puzzle"),
    path("<uuid:team_uuid>/debrief/", views.museum_debrief, name="museum_debrief"),
]

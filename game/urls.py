from django.urls import path, include
from . import views

urlpatterns = [
    path("", views.start, name="start"),
    path("create/", views.create_team, name="create_team"),
    path("join/", views.join_team, name="join_team"),
    path("lobby/<uuid:team_uuid>/", views.lobby, name="lobby"),
    path("lock/<uuid:team_uuid>/validate/", views.lock_validate_codes, name="lock_validate"),
    path("gare/", include("gare.urls")),
]

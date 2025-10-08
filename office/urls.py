from django.urls import path
from . import views

urlpatterns = [
    path("<uuid:team_uuid>/", views.office_game, name="office_game"),
]



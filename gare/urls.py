from django.urls import path
from .views import rail_puzzle

urlpatterns = [
    path("rail/<uuid:team_uuid>/", rail_puzzle, name="rail_puzzle"),
]
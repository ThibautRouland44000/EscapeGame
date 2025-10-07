from django.urls import path
from . import views

urlpatterns = [
    path("<uuid:team_uuid>/", views.room_puzzle, name="hotel_room"),
]

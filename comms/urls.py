from django.urls import path
from . import views

urlpatterns = [
    path("<uuid:team_uuid>/fetch/", views.fetch, name="chat_fetch"),
    path("<uuid:team_uuid>/send/",  views.send,  name="chat_send"),
]
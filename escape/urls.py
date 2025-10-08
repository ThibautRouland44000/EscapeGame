from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("game.urls")),
    path("chat/", include("comms.urls")),
    path("museum/", include("museum.urls")),
    path("office/", include("office.urls")),
]


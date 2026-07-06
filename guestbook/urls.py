from django.urls import path

from . import views

app_name = "guestbook"

urlpatterns = [
    path("", views.index, name="index"),
    path("nytt/", views.create, name="create"),
    path("familjer/<slug:slug>/", views.family_entries, name="family_entries"),
]

from django.urls import path
from . import views

urlpatterns = [
    path("auth/login/", views.login, name="spotify-login"),
    path("auth/callback/", views.callback, name="spotify-callback"),
    path("playlists/", views.my_playlists, name="my-playlists"),
    path("merge/", views.merge_playlists, name="merge-playlists"),
    
]
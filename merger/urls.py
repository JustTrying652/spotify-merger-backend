from django.urls import path
from . import views

urlpatterns = [
    path("auth/login/", views.login, name="spotify-login"),
    path("auth/callback/", views.callback, name="spotify-callback"),
    path("playlists/", views.my_playlists, name="my-playlists"),
    path("merge/", views.merge_playlists, name="merge-playlists"),
    path("duplicates/", views.find_duplicates, name="find-duplicates"),
    path("preview/", views.preview_merge, name="preview-merge"),
    path("export/<str:playlist_id>/", views.export_playlist, name="export-playlist"),
    path("undo/<str:playlist_id>/", views.undo_merge, name="undo-merge"),
]
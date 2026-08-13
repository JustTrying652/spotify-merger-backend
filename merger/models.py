from django.db import models


class MergeHistory(models.Model):
    spotify_user_id = models.CharField(max_length=100)
    source_playlist_a_name = models.CharField(max_length=200)
    source_playlist_b_name = models.CharField(max_length=200)
    new_playlist_id = models.CharField(max_length=100)
    new_playlist_name = models.CharField(max_length=200)
    track_count = models.PositiveIntegerField()
    duplicates_removed = models.PositiveIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.new_playlist_name} ({self.track_count} tracks, {self.created_at:%Y-%m-%d})"
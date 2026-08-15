import os
import json
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

import spotipy
from django.conf import settings

# Paste a fresh access token here — grab it from your browser session or re-login and
# copy it from the Django debug page's "headers" section from any recent request, or
# simplest: add a print(access_token) temporarily in views.py and copy from the console.
ACCESS_TOKEN = "PASTE_A_FRESH_TOKEN_HERE"

sp = spotipy.Spotify(auth=ACCESS_TOKEN)
result = sp.current_user_playlists()
print(json.dumps(result["items"][0], indent=2))
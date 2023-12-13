import spotipy
from spotipy.oauth2 import SpotifyOAuth
from fastapi import FastAPI, Request
import toml

print('starting fastapi')
app = FastAPI()

client_info = toml.load('spotify_user_details.toml')

CLIENT_ID = client_info['SpotifyUser']['CLIENT_ID']
CLIENT_SECRET = client_info['SpotifyUser']['CLIENT_SECRET']
print(CLIENT_SECRET)
REDIRECT_URI = 'http://localhost:8000'
SCOPE = "user-library-read playlist-read-private"

@app.get('/login')
def login():
    sp_oauth = SpotifyOAuth(client_id=CLIENT_ID,
                           client_secret=CLIENT_SECRET,
                           redirect_uri=REDIRECT_URI,
                           scope=SCOPE)
    auth_url = sp_oauth.get_authorize_url()
    return {"Authorization URL": auth_url}

@app.get("/")
def home(request: Request):
    access_token = request.query_params.get("access_token")
    print(f'Here is the access token: {access_token}')
    if access_token:
        print('there is an access token')
        sp = spotipy.Spotify(auth=access_token)
        user_info = sp.current_user()
        return {"message": f"Welcome, {user_info['display_name']}! You have successfully authenticated with Spotify."}
    else:
        return {"message": "Welcome to the FastAPI home page! To authenticate with Spotify, go to /login."}
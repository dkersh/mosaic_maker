# artify
Create a mosaic from your favourite albums
![example](example.png)

## Usage
For a .csv file of albums:

```
client_info = toml.load('spotify_user_details.toml')
CLIENT_ID = client_info['SpotifyUser']['CLIENT_ID']
CLIENT_SECRET = client_info['SpotifyUser']['CLIENT_SECRET']

sp = spotipy.Spotify(
    auth_manager=SpotifyClientCredentials(
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET)
        )
mm = mosaic_maker.MosaicMaker(sp)
mm.get_albums('src/album_list.csv')
mm.sort_album_list(method='color')
mosaic = mm.create_mosaic()
```
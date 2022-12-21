import csv
from dataclasses import dataclass
from io import BytesIO

import numpy as np
import requests
import spotipy
import toml
from PIL import Image
from spotipy.oauth2 import SpotifyClientCredentials


@dataclass
class Album:
    artist: str
    album: str
    artwork: Image = None

    def __post_init__(self):
        search_query = "%s %s" % (self.artist, self.album)
        results = sp.search(q=search_query, type="album")
        items = results["albums"]["items"]
        url = items[0]["images"][0]["url"]
        response = requests.get(url)
        img = Image.open(BytesIO(response.content))
        self.artwork = img


class MosaicMaker:
    def __init__(
        self,
        sp_client: spotipy.client.Spotify,
        resolution: list = [1000, 1000],
        shape: str = "square",
    ):
        self.sp = sp_client
        self._resolution = resolution
        self._shape = shape
        self.album_list: list = []

    @property
    def resolution(self):
        return self._resolution

    @resolution.setter
    def resolution(self, val):
        if (self.shape == "square") and (val[0] != val[1]):
            raise ValueError("Resolution X and Y must be the same value")
        self._resolution = val

    @property
    def shape(self):
        return self._shape

    @shape.setter
    def shape(self, val):
        if val not in ["rectangle", "square"]:
            raise AttributeError("shape must be square and rectangle.")
        self._shape = val

    def get_albums(self, album_list: str):
        with open(album_list) as csvfile:
            reader = csv.reader(csvfile, delimiter=",")
            for row in reader:
                album = Album(row[0], row[1])
                try:
                    album.artwork = self.query_album_art(album)
                except:
                    print("Failed to grab artwork")
                    album.artwork = np.zeros((640, 640, 3))
                self.album_list += [album]

    def query_album_art(self, album: Album):
        search_query = "%s %s" % (album.artist, album.album)
        results = self.sp.search(q=search_query, type="album")
        items = results["albums"]["items"]
        url = items[0]["images"][0]["url"]
        response = requests.get(url)
        img = Image.open(BytesIO(response.content))
        if len(np.shape(img)) == 2:
            img = img.convert("RGB")
        return img

    def create_mosaic(self) -> Image:
        if not self.album_list:
            raise AttributeError("Album List is empty")

        # Some kind of sorting of the album list would be useful / cool
        sides = int(np.sqrt(len(self.album_list)))

        mosaic = Image.new("RGB", (sides * 640, sides * 640), (0, 0, 0))
        x = 0
        y = 0
        for im in self.album_list:
            mosaic.paste(
                im.artwork.resize((640, 640), Image.Resampling.BICUBIC), (x, y)
            )
            x += 640
            if x >= sides * 640:
                x = 0
                y += 640

        return mosaic

    def image_grouper(self):
        pass

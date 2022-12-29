import csv
from dataclasses import dataclass
from io import BytesIO

import numpy as np
import requests
import spotipy
from PIL import Image
from spotipy.oauth2 import SpotifyClientCredentials
import cv2
import PIL
from sklearn.preprocessing import MinMaxScaler
from sklearn.manifold import TSNE
from scipy.spatial.distance import cdist
from dateutil.parser import parse
from datetime import datetime
import lapjv


@dataclass
class Album:
    artist: str
    album: str
    date: datetime = None
    artwork: Image = None


class MosaicMaker:
    def __init__(
        self,
        sp_client: spotipy.client.Spotify,
        resolution: list = [1000, 1000],
        shape: str = "square",
    ):
        """Mosaic Maker class for grabbing albums from Spotify and arranging them in an aesthetically pleasing arrangement.
        TODO: Add support for shapes beyond square

        Args:
            sp_client (spotipy.client.Spotify): Spotipy client object (requires user authentication)
            resolution (list, optional): Mosaic Resolution. Defaults to [1000, 1000].
            shape (str, optional): Shape of mosaic. Defaults to "square".
        """
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
        """Look over the albums in the specified csvfile and query using the spotify API.

        Args:
            album_list (str): path to csv file containing list of albums.
        """
        self.album_list = []
        with open(album_list) as csvfile:
            reader = csv.reader(csvfile, delimiter=",")
            for row in reader:
                album = Album(row[0], row[1])
                try:
                    album.artwork, album.date = self.query_album(album)
                except:
                    print("Failed to grab artwork")
                    album.artwork = np.zeros((640, 640, 3))
                self.album_list += [album]
        self.album_list = np.array(self.album_list)

    def query_album(self, album: Album):
        """Use spotify API (spotipy) to send a query to spotify and grab the album art and date.

        Args:
            album (Album): album object with artist and album specified.

        Returns:
            Image, datetime: Artwork and Date of release
        """
        search_query = "%s %s" % (album.artist, album.album)
        results = self.sp.search(q=search_query, type="album")
        items = results["albums"]["items"]
        url = items[0]["images"][0]["url"]
        response = requests.get(url)
        img = Image.open(BytesIO(response.content))
        if len(np.shape(img)) == 2:
            img = img.convert("RGB")
        try:
            date = parse(items[0]['release_date'], fuzzy=True)
        except:
            date = None
        return img, date

    def sort_album_list(self, method='color'):
        """Match/Case method for sorting an album list.
        Color - Attempts to group album art by colour.
        Date - Attempts to sort albums by date.

        Args:
            method (str, optional): Sort method. Defaults to 'color'.
        """
        match method:
            case "color":
                print('sorting by color')
                # Use JV album to sort album list
                np.random.shuffle(self.album_list) # Shuffle to give different results
                self.album_list = cluster_artwork(self.album_list)

            case "date":
                print('sorting by date')
                all_dates = [m.date for m in self.album_list]
                ind = np.argsort(all_dates)
                self.album_list = self.album_list[ind]

    def create_mosaic(self) -> Image:
        """Create an album mosaic.
        TODO: Support non-square sizes.

        Raises:
            AttributeError: One of the albums in the album list isn't specified.

        Returns:
            Image: Album mosaic
        """
        if not np.all(self.album_list):
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

def album_art_feature_extraction(album_list):
    """_summary_

    Args:
        album_list (_type_): _description_

    Returns:
        _type_: _description_
    """
    all_feat = []
    for im in album_list:
        # Convert to HSV
        img = np.array(im.artwork.resize((64, 64), PIL.Image.Resampling.BICUBIC))
        img = cv2.cvtColor(img, cv2.COLOR_RGB2HSV)
        feat_vec = np.mean(np.mean(img, axis=0), axis=0)
        all_feat += [feat_vec]
    all_feat = np.array(all_feat)

    return all_feat

def cluster_artwork(album_list):
    """_summary_

    Args:
        album_list (_type_): _description_

    Returns:
        _type_: _description_
    """
    all_feat = album_art_feature_extraction(album_list)
    all_feat_norm = MinMaxScaler().fit_transform(all_feat)
    embedding = TSNE(n_components=2).fit_transform(all_feat_norm)
    embedding = MinMaxScaler().fit_transform(embedding)

    # https://github.com/kylemcdonald/CloudToGrid/blob/master/CloudToGrid.ipynb
    side = np.sqrt(len(album_list)).astype(int)
    xv, yv = np.meshgrid(np.linspace(0, 1, side), np.linspace(0, 1, side))
    grid = np.dstack((xv, yv)).reshape(-1, 2)

    cost = cdist(grid, embedding, 'sqeuclidean')
    cost = cost * (10000000. / cost.max())

    row_ind, col_ind, _ = lapjv.lapjv(cost)
    grid_hu = grid[col_ind]
    ind = np.lexsort((grid_hu[:, 1], grid_hu[:, 0]))
    album_list = np.array(album_list)[ind]

    return album_list
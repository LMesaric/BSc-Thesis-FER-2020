#    Zagreb GIS - Generate a Zagreb district model based on real data
#    Copyright (C) 2020  Luka Mesarić (luka.mesaric@fer.hr)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.

import io
import itertools
import os
import tempfile
from typing import Tuple
from zipfile import ZipFile

import bpy

from zagrebgis.maths.geoutils import Geolocation


class HeightmapMeta:

    def __init__(self, bottom_left: Geolocation, top_right: Geolocation,
                 path_to_file: str, min_height: float, max_height: float):
        self.bottom_left = bottom_left
        self.top_right = top_right
        self.path_to_file = path_to_file
        self.min_height = min_height
        self.max_height = max_height

    def __repr__(self):
        return str(self.__dict__)


def download_map(bottom_left: Geolocation, top_right: Geolocation, temp_dir: str = None) -> HeightmapMeta:
    """Downloads needed heightmap.

    :param bottom_left: Bottom-left (SW) corner
    :param top_right: Top-right (NE) corner
    :param temp_dir: Directory used to store files, uses `bpy.app.tempdir` if set to `None`
    :return: Path to heightmap image
    """

    if temp_dir is None:
        temp_dir = bpy.app.tempdir

    name = 'map'
    vertical_dist, horizontal_dist = bottom_left.span(top_right)
    map_dir = _download_map_unzip(bottom_left, top_right, temp_dir, name)
    best_map = _find_best_map(map_dir, name)
    extremes = _find_extreme_heights(map_dir, name)
    rescaled_map = _resize_map(best_map, temp_dir, horizontal_dist, vertical_dist)
    return HeightmapMeta(bottom_left, top_right, rescaled_map, extremes[0], extremes[1])


def _download_map_unzip(bottom_left: Geolocation, top_right: Geolocation, path: str, name: str) -> str:
    """Downloads and unzips requested heightmap and other files. Saves it in a new directory inside `path`.

    :param bottom_left: Bottom-left (SW) corner
    :param top_right: Top-right (NE) corner
    :param path: Path to directory
    :param name: Name of downloaded map
    :return: Path to new temporary directory inside `path`
    """

    r = _download_map_request(bottom_left, top_right, name)
    z = ZipFile(io.BytesIO(r.content))
    zip_dir = tempfile.mkdtemp(dir=path)
    z.extractall(zip_dir)

    return zip_dir


def _download_map_request(bottom_left: Geolocation, top_right: Geolocation, name: str):
    """Downloads requested heightmap. Does not change received data in any way. Times out after 40 seconds.

    :param bottom_left: Bottom-left (SW) corner
    :param top_right: Top-right (NE) corner
    :param name: Name of downloaded map
    :return: Response object
    :rtype: requests.Response
    """

    import requests
    # URL example: http://terrain.party/api/export?name=my_map&box=16.025063,45.843957,15.921900,45.772092
    base_url = r"http://terrain.party/api/export"
    payload = {'name': name, 'box': f'{top_right.long},{top_right.lat},{bottom_left.long},{bottom_left.lat}'}
    r = requests.get(base_url, payload, timeout=40)
    r.raise_for_status()
    return r


def _find_best_map(path: str, name: str) -> str:
    """Finds path to best (merged) heightmap.

    :param path: Path to directory containing maps
    :param name: Name of downloaded map
    :return: Path to best map
    """

    image_name = f'{name} Height Map (Merged).png'
    abs_path = os.path.join(path, image_name)
    if not os.path.isfile(abs_path):
        raise FileNotFoundError(f"Cannot find file: {abs_path}")
    return abs_path


def _find_extreme_heights(path: str, name: str) -> Tuple[float, float]:
    """Finds minimum and maximum height written in README file.

    :param path: Path to directory containing maps
    :param name: Name of downloaded map
    :return: Minimum and maximum height
    """

    readme_name = f'{name} README.txt'
    full_path = os.path.join(path, readme_name)

    with open(full_path, encoding='utf8') as fp:
        it = itertools.dropwhile(lambda l: not l.startswith('Elevation Adjustment'), fp)
        it = itertools.islice(it, 4, None)
        heights_line = next(it)

    return _parse_heights_from_line(heights_line)


def _parse_heights_from_line(line: str) -> Tuple[float, float]:
    """Extracts minimum and maximum height from a line.

    :param line: Line of text
    :return: Minimum and maximum height
    """

    # example line: "87 through 317 meters."
    nums = []
    for word in line.split():
        try:
            nums.append(float(word))
        except ValueError:
            pass

    if len(nums) != 2:
        raise RuntimeError(f"Could not extract heights: {line}")

    return nums[0], nums[1]


def _resize_map(input_path: str, output_dir: str, real_width_meters: float, real_height_meters: float) -> str:
    """Resizes image (changes aspect ratio) to reflect real-world size.

    :param input_path: Path to image to be rescaled
    :param output_dir: Directory in which rescaled image should be saved
    :param real_width_meters: Real-world width of the area in meters (E-W)
    :param real_height_meters: Real-world height of the area in meters (N-S)
    :return: Path to rescaled image
    """

    from PIL import Image
    im = Image.open(input_path)
    w, h = im.size
    new_w, new_h = w, h

    if real_width_meters > real_height_meters:
        new_w: int = round(1.0 * real_width_meters / real_height_meters * h)
    else:
        new_h: int = round(1.0 * real_height_meters / real_width_meters * w)

    _, image_path = tempfile.mkstemp(suffix='.png', dir=output_dir)
    im.resize((new_w, new_h), Image.BICUBIC).save(image_path)
    return image_path

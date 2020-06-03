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


from typing import List, Tuple

from zagrebgis.constants import NETWORK_TIMEOUT
from zagrebgis.location_finder import LocationFinder
from zagrebgis.maths.geoutils import Geolocation


class Tree:
    __slots__ = ['x', 'y']

    def __init__(self, lat: float, long: float, location_finder: LocationFinder):
        self.x, self.y = location_finder.location_to_xy(Geolocation(lat, long))


def get_all_trees(bottom_left: Geolocation, top_right: Geolocation,
                  location_finder: LocationFinder) -> List[Tree]:
    from pyproj import Transformer

    transformer_round_to_flat = Transformer.from_crs("epsg:4326", "epsg:3857")
    xx_left, yy_bottom = transformer_round_to_flat.transform(bottom_left.lat, bottom_left.long)
    xx_right, yy_top = transformer_round_to_flat.transform(top_right.lat, top_right.long)

    r = _download_trees_request(xx_left, yy_bottom, xx_right, yy_top)
    trees = _parse_trees_response(r.text, location_finder, Transformer.from_crs("epsg:3857", "epsg:4326"))
    return trees


def _download_trees_request(xx_left: float, yy_bottom: float, xx_right: float, yy_top: float):
    """
    Downloads trees in requested area. The only change applied to the received data
    is setting the encoding to utf-8. Times out after 40 seconds.

    :param xx_left: x-coordinate of bottom-left (SW) corner (epsg:3857)
    :param yy_bottom: y-coordinate of bottom-left (SW) corner (epsg:3857)
    :param xx_right: x-coordinate of top-right (NE) corner (epsg:3857)
    :param yy_top: y-coordinate of top-right (NE) corner (epsg:3857)
    :return: Response object
    :rtype: requests.Response
    """

    import requests

    # URL example: https://gis.zrinjevac.hr/stabla_geom.php?bbox=1780031.0284678135,5749293.04326744,1780852.4279397377,5749747.7838693075&srid=3857
    base_url = r"https://gis.zrinjevac.hr/stabla_geom.php"
    payload = {'bbox': f'{xx_left},{yy_bottom},{xx_right},{yy_top}', 'srid': 3857}
    r = requests.get(base_url, payload, timeout=NETWORK_TIMEOUT, verify=False)
    r.raise_for_status()
    r.encoding = 'utf-8'  # exceptional speed-up compared to self-detection
    return r


def _parse_trees_response(s: str, location_finder: LocationFinder, transformer) -> List[Tree]:
    import json

    parsed = json.loads(s)
    if parsed.get('type') != 'FeatureCollection':
        print(f"Unknown response type: {parsed.get('type')}")
        return []
    if 'features' not in parsed:
        print('Missing features in server response')
        return []

    features = parsed['features']

    trees: List[Tree] = []

    for feature in features:
        if feature.get('type') != 'Feature':
            print(f"Unknown feature type: {feature.get('type')}")
            continue

        geometry = feature.get('geometry')
        if geometry is None or not len(geometry):
            print(f'Bad geometry: {geometry}')
            continue

        if geometry.get('type') != 'Point':
            print(f"Unknown geometry type: {geometry.get('type')}")
            continue

        coords = geometry.get('coordinates')
        if coords is None or len(coords) != 2:
            print(f'Bad coordinates: {coords}')
            continue

        transformed: Tuple[float, float] = transformer.transform(*coords)
        try:
            trees.append(Tree(transformed[0], transformed[1], location_finder))
        except ValueError:
            pass

    return trees

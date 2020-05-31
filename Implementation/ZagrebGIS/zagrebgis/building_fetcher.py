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


import random
from typing import Callable, Dict, List, Tuple

from zagrebgis.constants import HEIGHT_PER_LEVEL, NETWORK_TIMEOUT
from zagrebgis.location_finder import LocationFinder
from zagrebgis.maths.geoutils import Geolocation


class Node:
    __slots__ = ['lat', 'long', 'xy']

    def __init__(self, lat: float, long: float, location_finder: LocationFinder):
        self.lat = lat
        self.long = long
        self.xy = location_finder.location_to_xy(Geolocation(lat, long))


class Building:
    __slots__ = ['nodes', 'height']

    def __init__(self, nodes: List[Node], height_random_func: Callable[[], float],
                 height: float = None, levels: float = None):
        self.nodes = nodes
        self.height = Building._get_height(height, levels, height_random_func)

    @staticmethod
    def _get_height(height: float, levels: float, height_random_func: Callable[[], float]) -> float:
        if height is not None:
            return height
        if levels is not None:
            return levels * HEIGHT_PER_LEVEL
        return height_random_func()


def get_all_buildings(bottom_left: Geolocation, top_right: Geolocation,
                      location_finder: LocationFinder) -> List[Building]:
    r = _download_buildings_request(bottom_left, top_right)
    nodes, ways = _parse_buildings_response(r.text, location_finder)
    buildings = _convert_buildings(nodes, ways)
    return buildings


def _download_buildings_request(bottom_left: Geolocation, top_right: Geolocation):
    """
    Downloads buildings in requested area. The only change applied to the received data
    is setting the encoding to utf-8. Times out after 40 seconds.

    :param bottom_left: Bottom-left (SW) corner
    :param top_right: Top-right (NE) corner
    :return: Response object
    :rtype: requests.Response
    """

    import requests

    bbox = f'{bottom_left.lat},{bottom_left.long},{top_right.lat},{top_right.long}'
    # query: any way or relation with any building tag
    query = f"""[out:json][timeout:{NETWORK_TIMEOUT}];
(
  way["building"]({bbox});
  relation["building"]({bbox});
);
out body;
>;
out skel qt;"""

    base_url = r"https://overpass-api.de/api/interpreter"
    payload = {'data': query}
    r = requests.post(base_url, data=payload, timeout=NETWORK_TIMEOUT)
    r.raise_for_status()
    r.encoding = 'utf-8'  # exceptional speed-up compared to self-detection
    return r


def _parse_buildings_response(s: str, location_finder: LocationFinder) \
        -> Tuple[Dict[int, Node], List[List[int]]]:
    import json

    elements = json.loads(s)['elements']

    nodes: Dict[int, Node] = {}
    ways: List[List[int]] = []

    for e in elements:
        element_type = e['type']

        if element_type == 'node':
            try:
                nodes[e['id']] = Node(e['lat'], e['lon'], location_finder)
            except ValueError:
                pass

        elif element_type == 'way':
            way_nodes: List[int] = e['nodes']

            if len(way_nodes) < 4:
                print(f'Nodes list too short: {way_nodes}')
                continue

            if way_nodes[0] != way_nodes[-1]:
                print(f'Nodes list does not form a loop: {way_nodes}')
                continue

            del way_nodes[-1]  # drop duplicate node since loop is implied

            ways.append(way_nodes)

        elif element_type == 'relation':
            pass

        else:
            print(f'Unknown type: {element_type}')

    return nodes, ways


def _convert_buildings(nodes: Dict[int, Node], ways: List[List[int]]) -> List[Building]:
    def random_height() -> float:
        return random.uniform(8, 25)

    buildings: List[Building] = []
    for way in ways:
        way_nodes_converted: List[Node] = []

        for node_id in way:
            node = nodes.get(node_id)
            if node is None:
                break
            way_nodes_converted.append(node)
        else:
            buildings.append(Building(nodes=way_nodes_converted, height_random_func=random_height))

    return buildings

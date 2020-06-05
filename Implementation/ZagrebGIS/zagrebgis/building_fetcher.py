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
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

from zagrebgis.constants import HEIGHT_PER_LEVEL, NETWORK_TIMEOUT
from zagrebgis.location_finder import LocationFinder
from zagrebgis.maths.geoutils import Geolocation


class Node:
    __slots__ = ['xy']

    def __init__(self, lat: float, long: float, location_finder: LocationFinder):
        self.xy = location_finder.location_to_xy(Geolocation(lat, long))


class WayRaw:
    __slots__ = ['way_id', 'node_ids', 'height', 'levels']

    def __init__(self, way_id: int, node_ids: List[int], height: Optional[float], levels: Optional[float]):
        self.way_id = way_id
        self.node_ids = node_ids
        self.height = height
        self.levels = levels


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
    # query: any way or relation with any building or building:part tag
    query = f"""[out:json][timeout:{NETWORK_TIMEOUT}];
(
  way["building"]({bbox});
  relation["building"]({bbox});
  way["building:part"]({bbox});
  relation["building:part"]({bbox});
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
        -> Tuple[Dict[int, Node], Dict[int, WayRaw]]:
    import json

    elements = json.loads(s).get('elements')

    nodes: Dict[int, Node] = {}
    ways: Dict[int, WayRaw] = {}

    for e in elements:
        element_type = e.get('type')

        if element_type == 'node':
            try:
                nodes[e['id']] = Node(e['lat'], e['lon'], location_finder)
            except ValueError:
                pass

        elif element_type == 'way':

            way_id = e.get('id')
            if way_id is None:
                print(f'Missing way ID: {e}')
                continue

            way_node_ids: Optional[List[int]] = e.get('nodes')
            if way_node_ids is None:
                print(f'Missing nodes in way: {e}')
                continue

            if len(way_node_ids) < 4:
                print(f'Nodes list too short: {way_node_ids}')
                continue

            if way_node_ids[0] != way_node_ids[-1]:
                print(f'Nodes list does not form a loop: {way_node_ids}')
                continue

            del way_node_ids[-1]  # drop duplicate node since loop is implied

            way_height: Optional[float] = None
            way_levels: Optional[float] = None
            way_tags: Optional[Dict[str, Any]] = e.get('tags')
            if way_tags is not None:
                way_height = _parse_height_tag(way_tags)
                way_levels = _parse_levels_tag(way_tags)

            ways[way_id] = WayRaw(way_id, way_node_ids, way_height, way_levels)

        elif element_type == 'relation':
            pass

        else:
            print(f'Unknown type: {e}')

    return nodes, ways


def _parse_height_tag(tags: Dict[str, Any]) -> Optional[float]:
    height_raw: Optional[Union[int, float, str]] = tags.get('height')
    if height_raw is None:
        height_raw = tags.get('building:height')

    if height_raw is None:
        return None

    try:
        return float(height_raw)
    except ValueError:
        # height_raw is probably something like '22 m'
        pass

    parts = height_raw.split()
    if len(parts) != 2 or parts[1] != 'm':
        print(f'Cannot parse height data: {height_raw}')
        return None

    try:
        return float(parts[0])
    except ValueError:
        print(f'Cannot parse height data: {height_raw}')
        return None


def _parse_levels_tag(tags: Dict[str, Any]) -> Optional[float]:
    levels_raw: Optional[Union[int, float]] = tags.get('levels')
    if levels_raw is None:
        levels_raw = tags.get('building:levels')

    if levels_raw is None:
        return None

    try:
        return float(levels_raw)
    except ValueError:
        print(f'Cannot parse levels data: {levels_raw}')
        return None


def _convert_buildings(nodes: Dict[int, Node], ways: Dict[int, WayRaw]) -> List[Building]:
    def random_height() -> float:
        return random.uniform(8, 25)

    buildings: List[Building] = []
    for way_id, way_raw in ways.items():
        way_nodes_converted: List[Node] = []

        for node_id in way_raw.node_ids:
            node = nodes.get(node_id)
            if node is None:
                break
            way_nodes_converted.append(node)
        else:
            buildings.append(
                Building(nodes=way_nodes_converted, height_random_func=random_height,
                         height=way_raw.height, levels=way_raw.levels))

    return buildings

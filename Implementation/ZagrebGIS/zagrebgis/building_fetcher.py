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
from itertools import chain
from typing import Any, Callable, Dict, Iterable, List, Optional, Set, Tuple, Union

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


class RelationRaw:
    __slots__ = ['positive_ways_ids', 'negative_ways_ids', 'height', 'levels']

    def __init__(self, positive_ways_ids: List[int], negative_ways_ids: List[int],
                 height: Optional[float], levels: Optional[float]):
        self.positive_ways_ids = positive_ways_ids
        self.negative_ways_ids = negative_ways_ids
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


class Relation:
    __slots__ = ['positive_buildings', 'negative_buildings']

    def __init__(self, positive_buildings: List[Building], negative_buildings: List[Building]):
        self.positive_buildings = positive_buildings
        self.negative_buildings = negative_buildings


def get_all_buildings(bottom_left: Geolocation, top_right: Geolocation,
                      location_finder: LocationFinder) \
        -> Tuple[List[Building], List[Relation]]:
    r = _download_buildings_request(bottom_left, top_right)
    nodes, ways_all, relations_raw = _parse_buildings_response(r.text, location_finder)
    _duplicate_height_level_data(ways_all, relations_raw)

    ways_in_relations_keys = _get_all_relations_ways(relations_raw) & ways_all.keys()
    simple_ways_keys = ways_all.keys() - ways_in_relations_keys

    _cleanup_ways(nodes, ways_in_relations_keys, ways_all)
    _cleanup_ways(nodes, simple_ways_keys, ways_all)

    relations_clean = _cleanup_relations(relations_raw, ways_in_relations_keys)

    buildings = _convert_ways_to_buildings(nodes, simple_ways_keys, ways_all)
    relations = _convert_raw_to_relations(nodes, relations_clean, ways_all)

    return buildings, relations


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
        -> Tuple[Dict[int, Node], Dict[int, WayRaw], List[RelationRaw]]:
    import json

    elements = json.loads(s).get('elements')

    nodes: Dict[int, Node] = {}
    ways: Dict[int, WayRaw] = {}
    relations: List[RelationRaw] = []

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

            way_height, way_levels = _parse_height_levels_from_element(e)
            ways[way_id] = WayRaw(way_id, way_node_ids, way_height, way_levels)

        elif element_type == 'relation':
            members: List[Dict[str, Any]] = e.get('members')
            if members is None:
                print(f'Relation missing members: {e}')
                continue

            positives, negatives = _parse_relation_members(members)
            if positives is None or negatives is None:
                continue

            relation_height, relation_levels = _parse_height_levels_from_element(e)
            relations.append(RelationRaw(positives, negatives, relation_height, relation_levels))

        else:
            print(f'Unknown type: {e}')

    return nodes, ways, relations


def _parse_height_levels_from_element(element: Dict[str, Any]) -> Tuple[Optional[float], Optional[float]]:
    way_tags: Optional[Dict[str, Any]] = element.get('tags')
    if way_tags is None:
        return None, None
    return _parse_height_tag(way_tags), _parse_levels_tags(way_tags)


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


def _parse_levels_tags(tags: Dict[str, Any]) -> Optional[float]:
    levels_raw: Optional[Union[int, float]] = tags.get('levels')
    if levels_raw is None:
        levels_raw = tags.get('building:levels')

    if levels_raw is None:
        return None

    levels_roof_raw: Optional[Union[int, float]] = tags.get('roof:levels')
    levels_roof_parsed = 0.0
    if levels_roof_raw is not None:
        try:
            levels_roof_parsed = float(levels_roof_raw)
        except ValueError:
            print(f'Cannot parse roof levels data: {levels_roof_raw}')

    try:
        return float(levels_raw) + levels_roof_parsed
    except ValueError:
        print(f'Cannot parse levels data: {levels_raw}')
        return None


def _duplicate_height_level_data(ways_all: Dict[int, WayRaw], relations_raw: List[RelationRaw]):
    for r in relations_raw:
        for way_id in chain(r.positive_ways_ids, r.negative_ways_ids):
            way_raw = ways_all[way_id]
            if way_raw.height is None:
                way_raw.height = r.height
            if way_raw.levels is None:
                way_raw.levels = r.levels


def _parse_relation_members(members: List[Dict[str, Any]]) -> Tuple[Optional[List[int]], Optional[List[int]]]:
    positives: List[int] = []
    negatives: List[int] = []

    for member in members:
        if member.get('type') != 'way':
            print(f'Expected way type: {member}')
            return None, None

        ref = member.get('ref')
        if ref is None:
            print(f'Missing relation way reference: {member}')
            return None, None

        role = member.get('role')
        if role is None:
            print(f'Missing relation way role: {member}')
            return None, None

        if role in ('outer', 'outline', 'part'):
            positives.append(ref)
        elif role == 'inner':
            negatives.append(ref)
        else:
            print(f'Unknown role: {member}')
            return None, None

    return positives, negatives


def _get_all_relations_ways(relations: List[RelationRaw]) -> Set[int]:
    return {way_id for r in relations for way_id in chain(r.positive_ways_ids, r.negative_ways_ids)}


def _cleanup_ways(nodes: Dict[int, Node], ways_keys: Set[int], all_ways: Dict[int, WayRaw]):
    ids_to_remove: Set[int] = set()

    for way_id in ways_keys:
        if any(((node_id not in nodes) for node_id in all_ways[way_id].node_ids)):
            ids_to_remove.add(way_id)

    ways_keys -= ids_to_remove


def _cleanup_relations(relations: List[RelationRaw], ways_keys: Set[int]) -> List[RelationRaw]:
    return [r for r in relations
            if all(((way_id in ways_keys) for way_id in chain(r.positive_ways_ids, r.negative_ways_ids)))]


def _random_height() -> float:
    return random.uniform(8, 25)


def _convert_way_to_building(way_id: int, nodes: Dict[int, Node], all_ways: Dict[int, WayRaw]) -> Building:
    way_raw = all_ways[way_id]
    way_nodes_converted = [nodes[node_id] for node_id in way_raw.node_ids]
    return Building(nodes=way_nodes_converted, height_random_func=_random_height,
                    height=way_raw.height, levels=way_raw.levels)


def _convert_ways_to_buildings(nodes: Dict[int, Node], ways_keys: Iterable[int], all_ways: Dict[int, WayRaw]) \
        -> List[Building]:
    return [_convert_way_to_building(way_id, nodes, all_ways) for way_id in ways_keys]


def _convert_raw_to_relations(nodes: Dict[int, Node], relations_raw: List[RelationRaw],
                              all_ways: Dict[int, WayRaw]) -> List[Relation]:
    relations: List[Relation] = []
    for r in relations_raw:
        positive_buildings = _convert_ways_to_buildings(nodes, r.positive_ways_ids, all_ways)
        negative_buildings = _convert_ways_to_buildings(nodes, r.negative_ways_ids, all_ways)
        relations.append(Relation(positive_buildings, negative_buildings))
    return relations

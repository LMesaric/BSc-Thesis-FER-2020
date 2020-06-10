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


from itertools import tee
from typing import Iterable, List, Tuple

from bpy.types import Object
from mathutils import Vector

from zagrebgis.constants import TERRAIN_CLOSE_THRESH
from zagrebgis.maths.geoutils import Geolocation


class LocationFinder:

    def __init__(self, obj: Object, bottom_left: Geolocation, top_right: Geolocation):
        self.bottom_left = bottom_left
        self.top_right = top_right
        global_coords: List[Vector] = [(obj.matrix_world @ v.co) for v in obj.data.vertices]
        self.vertices_grouped = LocationFinder._prepare_vertices(global_coords)
        self.x_min = min(global_coords, key=lambda v: v.x).x
        self.y_min = min(global_coords, key=lambda v: v.y).y

    def find_close_points(self, x: float, y: float) -> List[Vector]:
        return self._binary_search(x, y)

    def find_close_points_many(self, p: Iterable[Tuple[float, float]]) -> List[Vector]:
        # There will likely be some duplicates which is OK
        return [t for v in p for t in self.find_close_points(*v)]

    def find_lowest_height(self, x: float, y: float) -> float:
        return min(self.find_close_points(x, y), key=lambda v: v.z).z

    def find_lowest_and_highest_many(self, p: Iterable[Tuple[float, float]]) -> Tuple[float, float]:
        close_points = self.find_close_points_many(p)
        return (min(close_points, key=lambda v: v.z).z,
                max(close_points, key=lambda v: v.z).z)

    def location_to_xy(self, location: Geolocation) -> Tuple[float, float]:
        if not location.is_in_bounds(self.bottom_left, self.top_right):
            raise ValueError(f'Location out of bounds: {location}')
        y_from_corner, x_from_corner = self.bottom_left.span(location)
        return self.x_min + x_from_corner, self.y_min + y_from_corner

    @staticmethod
    def _prepare_vertices(vertices: List[Vector]) \
            -> List[Tuple[float, List[Vector]]]:
        vertices.sort(key=lambda v: v.x)
        a, b = tee(vertices)
        next(b, None)

        grouped_by_x: List[Tuple[float, List[Vector]]] = [(vertices[0].x, [vertices[0]])]
        for first, second in zip(a, b):
            if abs(first.x - second.x) > TERRAIN_CLOSE_THRESH:
                grouped_by_x.append((second.x, [second]))
            else:
                grouped_by_x[-1][1].append(second)

        for _, points in grouped_by_x:
            points.sort(key=lambda v: v.y)

        return grouped_by_x

    def _binary_search(self, x: float, y: float, tolerance: float = TERRAIN_CLOSE_THRESH) -> List[Vector]:
        close_points: List[Vector] = []
        for y_list in LocationFinder._binary_search_by_x(self.vertices_grouped, x, tolerance):
            close_points.extend(LocationFinder._binary_search_by_y(y_list, y, tolerance))
        return close_points

    @staticmethod
    def _binary_search_by_x(
            vertices_grouped: List[Tuple[float, List[Vector]]],
            x: float,
            tolerance: float = TERRAIN_CLOSE_THRESH) \
            -> List[List[Vector]]:
        low = const_low = 0
        high = const_high = len(vertices_grouped) - 1

        while low <= high:
            mid = (high + low) // 2

            if abs(vertices_grouped[mid][0] - x) < tolerance:
                res: List[List[Vector]] = [vertices_grouped[mid][1]]
                if mid - 1 >= const_low and abs(vertices_grouped[mid - 1][0] - x) < tolerance:
                    res.append(vertices_grouped[mid - 1][1])
                if mid + 1 <= const_high and abs(vertices_grouped[mid + 1][0] - x) < tolerance:
                    res.append(vertices_grouped[mid + 1][1])
                return res
            elif vertices_grouped[mid][0] < x:
                low = mid + 1
            elif vertices_grouped[mid][0] > x:
                high = mid - 1

        return []

    @staticmethod
    def _binary_search_by_y(
            y_list: List[Vector],
            y: float,
            tolerance: float = TERRAIN_CLOSE_THRESH) \
            -> List[Vector]:
        low = const_low = 0
        high = const_high = len(y_list) - 1

        while low <= high:
            mid = (high + low) // 2

            if abs(y_list[mid].y - y) < tolerance:
                res: List[Vector] = [y_list[mid]]
                if mid - 1 >= const_low and abs(y_list[mid - 1].y - y) < tolerance:
                    res.append(y_list[mid - 1])
                if mid + 1 <= const_high and abs(y_list[mid + 1].y - y) < tolerance:
                    res.append(y_list[mid + 1])
                return res
            elif y_list[mid].y < y:
                low = mid + 1
            elif y_list[mid].y > y:
                high = mid - 1

        return []

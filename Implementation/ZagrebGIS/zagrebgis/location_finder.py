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


from typing import Iterable, List, Tuple

from bpy.types import Object
from mathutils import Vector

from zagrebgis.constants import TERRAIN_CLOSE_THRESH
from zagrebgis.maths.geoutils import Geolocation


class LocationFinder:

    def __init__(self, obj: Object, bottom_left: Geolocation, top_right: Geolocation):
        self.bottom_left = bottom_left
        self.top_right = top_right
        self.global_coords: List[Vector] = [(obj.matrix_world @ v.co) for v in obj.data.vertices]
        self.x_min = min(self.global_coords, key=lambda v: v.x).x
        self.x_max = max(self.global_coords, key=lambda v: v.x).x
        self.y_min = min(self.global_coords, key=lambda v: v.y).y
        self.y_max = max(self.global_coords, key=lambda v: v.y).y

    def find_close_points(self, x: float, y: float) -> List[Vector]:
        return list(filter(lambda v: abs(x - v.x) < TERRAIN_CLOSE_THRESH and abs(y - v.y) < TERRAIN_CLOSE_THRESH,
                           self.global_coords))

    def find_close_points_many(self, p: Iterable[Tuple[float, float]]) -> List[Vector]:
        # There will likely be some duplicates which is OK
        return [t for v in p for t in self.find_close_points(*v)]

    def find_lowest_height(self, x: float, y: float) -> float:
        return min(self.find_close_points(x, y), key=lambda v: v.z).z

    def find_lowest_height_many(self, p: Iterable[Tuple[float, float]]) -> float:
        return min(self.find_close_points_many(p), key=lambda v: v.z).z

    def location_to_xy(self, location: Geolocation) -> Tuple[float, float]:
        if not location.is_in_bounds(self.bottom_left, self.top_right):
            raise ValueError(f'Location out of bounds: {location}')
        y_from_corner, x_from_corner = self.bottom_left.span(location)
        return self.x_min + x_from_corner, self.y_min + y_from_corner

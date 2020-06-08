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


from __future__ import annotations

from math import asin, atan2, cos, degrees, radians, sin, sqrt
from typing import Tuple

_R = 6371008.8
"""Earth's mean radius in meters."""


class Geolocation:
    """
    Geolocation with latitude and longitude in degrees.

    Uses mathematical formulas that can be found here:
    https://www.movable-type.co.uk/scripts/latlong.html
    """

    __slots__ = ['lat', 'long']

    def __init__(self, lat: float, long: float):
        self.lat = lat
        self.long = long

    def __repr__(self):
        return f"({self.lat}, {self.long})"

    def distance(self, p: Geolocation) -> float:
        """
        Calculates distance between `self` and `p` using the haversine formula.
        Order is irrelevant.

        :param p: Other point
        :return: Distance in meters
        """

        lat1 = radians(self.lat)
        long1 = radians(self.long)
        lat2 = radians(p.lat)
        long2 = radians(p.long)

        a = (1 - cos(lat1 - lat2)) / 2.0 + \
            cos(lat1) * cos(lat2) * (1 - cos(long1 - long2)) / 2.0
        c = 2 * atan2(sqrt(a), sqrt(1 - a))
        return _R * c

    def span(self, diagonal_corner: Geolocation) -> Tuple[float, float]:
        """
        Calculates dimensions of the rectangle defined by `self` and `diagonal_corner`.
        Order is irrelevant.

        :param diagonal_corner: Corner diagonally opposite of `self`
        :return: height and width
        """

        another_corner = Geolocation(diagonal_corner.lat, self.long)

        vertical_dist = self.distance(another_corner)
        diagonal_dist = self.distance(diagonal_corner)
        horizontal_dist = sqrt(diagonal_dist * diagonal_dist - vertical_dist * vertical_dist)

        return vertical_dist, horizontal_dist

    def is_in_bounds(self, bottom_left: Geolocation, top_right: Geolocation) -> bool:
        """
        Tests if `self` is inside rectangle defined by `bottom_left` and `top_right`.

        :param bottom_left: Bottom-left (SW) corner
        :param top_right: Top-right (NE) corner
        :return: `True` if in bounds, `False` otherwise
        """

        if self.lat < bottom_left.lat:
            return False
        if self.lat > top_right.lat:
            return False
        if self.long < bottom_left.long:
            return False
        if self.long > top_right.long:
            return False
        return True

    def destination(self, distance: float, bearing: float) -> Geolocation:
        """
        Calculates the destination point with `self` as the starting point.

        :param distance: Distance to travel, in meters
        :param bearing: Bearing in radians
        :return: Destination point
        """

        lat1 = radians(self.lat)
        long1 = radians(self.long)
        ang_dist = distance / _R

        lat2 = asin(sin(lat1) * cos(ang_dist) + cos(lat1) * sin(ang_dist) * cos(bearing))
        long2 = long1 + atan2(sin(bearing) * sin(ang_dist) * cos(lat1),
                              cos(ang_dist) - sin(lat1) * sin(lat2))

        return Geolocation(degrees(lat2), degrees((long2 + 540) % 360 - 180))

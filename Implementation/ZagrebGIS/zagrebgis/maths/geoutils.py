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
    """Geolocation with latitude and longitude in degrees.

    Uses mathematical formulas that can be found here:
    https://www.movable-type.co.uk/scripts/latlong.html
    """

    def __init__(self, lat: float, long: float):
        self.lat = lat
        self.long = long

    def __repr__(self):
        return f"({self.lat}, {self.long})"

    def distance(self, p: Geolocation) -> float:
        """Calculates distance between `self` and `p` using the haversine formula.

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

    def span(self, top_right: Geolocation) -> Tuple[float, float]:
        """Calculates dimensions of the defined rectangle with `self` as the bottom-left point.

        :param top_right: Rectangle's top-right point
        :return: height and width
        """

        top_left = Geolocation(top_right.lat, self.long)
        bottom_right = Geolocation(self.lat, top_right.long)

        vertical_dist = self.distance(top_left)
        horizontal_dist = self.distance(bottom_right)

        return vertical_dist, horizontal_dist

    def destination(self, distance: float, bearing: float) -> Geolocation:
        """Calculates the destination point with `self` as the starting point.

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

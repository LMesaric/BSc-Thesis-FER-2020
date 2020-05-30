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


TERRAIN_VERTICES_DISTANCE = 4
"""Expected distance between neighbouring vertices in terrain mesh."""

TERRAIN_CLOSE_THRESH = 0.72 * TERRAIN_VERTICES_DISTANCE
"""Threshold for determining which vertices are considered `close` to a given point."""
# slightly greater than sqrt(2)/2 which is max distance (square's middle)

HEIGHT_PER_LEVEL = 4
"""Estimated height of each floor in buildings"""

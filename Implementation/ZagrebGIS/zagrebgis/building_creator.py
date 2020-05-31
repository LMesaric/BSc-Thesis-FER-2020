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

import bpy
from mathutils import Matrix, Vector

from zagrebgis.building_fetcher import Building
from zagrebgis.location_finder import LocationFinder


def create_buildings_many(buildings: Iterable[Building], location_finder: LocationFinder):
    for building in buildings:
        create_building(building, location_finder)


def create_building(building: Building, location_finder: LocationFinder):
    verts = [n.xy for n in building.nodes]
    v, f, (x, y) = verts_and_faces_from_footprint(verts, building.height)
    z = location_finder.find_lowest_height_many(verts)
    add_mesh("Building", v, f, translate=(x, y, z))


def add_mesh(name: str, verts: List[Vector], faces: List[List[int]], edges=None,
             translate: Tuple[float, float, float] = None,
             col_name: str = "Collection",
             recalculate_normals: bool = True,
             select: bool = False):
    if edges is None:
        edges = []

    mesh = bpy.data.meshes.new(name=name)
    obj = bpy.data.objects.new(mesh.name, mesh)
    col = bpy.data.collections.get(col_name)
    col.objects.link(obj)
    bpy.context.view_layer.objects.active = obj
    mesh.from_pydata(verts, edges, faces)

    obj = bpy.context.object
    obj.matrix_world = Matrix.Translation(translate) @ obj.matrix_world

    if recalculate_normals:
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.normals_make_consistent()
        bpy.ops.object.mode_set(mode='OBJECT')

    if select:
        bpy.ops.object.select_all(action='DESELECT')
        obj.select_set(True)


def verts_and_faces_from_footprint(verts_xy_foot: List[Tuple[float, float]], height: float) \
        -> Tuple[List[Vector], List[List[int]], Tuple[float, float]]:
    n = len(verts_xy_foot)
    if n < 3:
        raise ValueError(f"Bad verts: {verts_xy_foot}")
    if height <= 0:
        raise ValueError(f"Bad height: {height}")

    midpoint_x, midpoint_y = _get_midpoint(verts_xy_foot)
    vb = [Vector((v[0] - midpoint_x, v[1] - midpoint_y, 0.0)) for v in verts_xy_foot]  # bottom
    vt = [Vector((v.x, v.y, height)) for v in vb]  # top

    return vb + vt, _generate_faces_indices(n), (midpoint_x, midpoint_y)


def _generate_faces_indices(n: int) -> List[List[int]]:
    faces: List[List[int]] = [[i, (i + 1) % n, n + (i + 1) % n, n + i] for i in range(n)]
    faces.append(list(range(n - 1, -1, -1)))
    faces.append(list(range(n, 2 * n)))
    return faces


def _get_midpoint(verts_xy_foot: List[Tuple[float, float]]) -> Tuple[float, float]:
    x_min = min(verts_xy_foot, key=lambda v: v[0])[0]
    x_max = max(verts_xy_foot, key=lambda v: v[0])[0]
    y_min = min(verts_xy_foot, key=lambda v: v[1])[1]
    y_max = max(verts_xy_foot, key=lambda v: v[1])[1]

    return (x_min + x_max) / 2, (y_min + y_max) / 2

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
from mathutils import Vector

from zagrebgis.building_fetcher import Building, Relation
from zagrebgis.location_finder import LocationFinder


def create_buildings_many(buildings: Iterable[Building], location_finder: LocationFinder):
    for building in buildings:
        create_building(building, location_finder)


def create_building(building: Building, location_finder: LocationFinder, height_delta: float = 0.0):
    verts = [n.xy for n in building.nodes]
    z_min, z_max = location_finder.find_lowest_and_highest_many(verts)
    terrain_z_delta = z_max - z_min
    total_height = building.height + terrain_z_delta + height_delta * 2
    v, f, (x, y) = verts_and_faces_from_footprint(verts, total_height)
    add_mesh("Building", v, f, location=(x, y, z_min - height_delta))


def create_relations_many(relations: Iterable[Relation], location_finder: LocationFinder):
    for relation in relations:
        create_relation(relation, location_finder)


def create_relation(relation: Relation, location_finder: LocationFinder):
    if not relation.positive_buildings:
        return

    positive_meshes_names: List[str] = []
    negative_meshes_names: List[str] = []

    for positive_building in relation.positive_buildings:
        create_building(positive_building, location_finder)
        positive_meshes_names.append(bpy.context.active_object.name)

    for negative_building in relation.negative_buildings:
        create_building(negative_building, location_finder, 30.0)
        negative_meshes_names.append(bpy.context.active_object.name)

    for negative_building_name in negative_meshes_names:
        for positive_building_name in positive_meshes_names:
            # noinspection PyTypeChecker
            bool_mod = bpy.data.objects[positive_building_name].modifiers.new(type="BOOLEAN", name="boolean_diff")
            # noinspection PyTypeChecker
            bool_mod.object = bpy.data.objects[negative_building_name]
            bool_mod.operation = 'DIFFERENCE'

            # noinspection PyTypeChecker
            bpy.context.view_layer.objects.active = bpy.data.objects[positive_building_name]
            bpy.ops.object.modifier_apply(apply_as='DATA', modifier=bool_mod.name)

        bpy.ops.object.select_all(action='DESELECT')
        # noinspection PyTypeChecker
        bpy.data.objects[negative_building_name].select_set(True)
        bpy.ops.object.delete()


def add_mesh(name: str, verts: List[Vector], faces: List[List[int]], edges=None,
             location: Tuple[float, float, float] = None,
             col_name: str = "Collection",
             recalculate_normals: bool = True):
    if edges is None:
        edges = []

    mesh = bpy.data.meshes.new(name=name)
    obj = bpy.data.objects.new(mesh.name, mesh)
    col = bpy.data.collections.get(col_name)
    col.objects.link(obj)
    bpy.context.view_layer.objects.active = obj
    mesh.from_pydata(verts, edges, faces)

    bpy.context.object.location = location

    if recalculate_normals:
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.normals_make_consistent()
        bpy.ops.object.mode_set(mode='OBJECT')


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
    faces = [[i, (i + 1) % n, n + (i + 1) % n, n + i] for i in range(n)]
    faces.append(list(range(n - 1, -1, -1)))
    faces.append(list(range(n, 2 * n)))
    return faces


def _get_midpoint(verts_xy_foot: List[Tuple[float, float]]) -> Tuple[float, float]:
    x_min = min(verts_xy_foot, key=lambda v: v[0])[0]
    x_max = max(verts_xy_foot, key=lambda v: v[0])[0]
    y_min = min(verts_xy_foot, key=lambda v: v[1])[1]
    y_max = max(verts_xy_foot, key=lambda v: v[1])[1]

    return (x_min + x_max) / 2, (y_min + y_max) / 2

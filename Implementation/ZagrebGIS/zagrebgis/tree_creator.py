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
from typing import Iterable

import bpy

from zagrebgis.location_finder import LocationFinder
from zagrebgis.tree_fetcher import Tree


def create_trees_many(trees: Iterable[Tree], location_finder: LocationFinder):
    for tree in trees:
        create_tree(tree, location_finder)


def create_tree(tree: Tree, location_finder: LocationFinder):
    z = location_finder.find_lowest_height(tree.x, tree.y)
    tree_type = random.randint(1, 3)

    h = _create_trunk(tree.x, tree.y, z)
    bpy.ops.object.mode_set(mode='EDIT')  # keep the crown and trunk in one 'Tree' mesh

    if tree_type == 1:
        crown_size = random.uniform(2.7, 8)
        # noinspection PyTypeChecker
        bpy.ops.mesh.primitive_cone_add(
            vertices=random.randint(7, 50),
            radius1=random.uniform(1.3, 2.1),
            radius2=0,
            depth=crown_size,
            location=(tree.x, tree.y, z + h + crown_size / 2 - 0.3))

    elif tree_type == 2:
        crown_radius = random.uniform(1.5, 2.5)
        # noinspection PyTypeChecker
        bpy.ops.mesh.primitive_ico_sphere_add(
            subdivisions=2,
            radius=crown_radius,
            location=(tree.x, tree.y, z + h + crown_radius - 0.3))

    else:
        crown_radius = random.uniform(1.5, 2.5)
        # noinspection PyTypeChecker
        bpy.ops.mesh.primitive_uv_sphere_add(
            segments=random.randint(7, 24),
            ring_count=random.randint(6, 14),
            radius=crown_radius,
            location=(tree.x, tree.y, z + h + crown_radius - 0.3))

    bpy.ops.object.mode_set(mode='OBJECT')


def _create_trunk(x: float, y: float, z: float) -> float:
    trunk_height = random.uniform(2, 4.4)
    bottom_radius = random.uniform(0.2, 0.35)
    top_radius = bottom_radius * 0.75

    # noinspection PyTypeChecker
    bpy.ops.mesh.primitive_cone_add(
        vertices=random.randint(7, 16),
        radius1=bottom_radius,
        radius2=top_radius,
        depth=trunk_height,
        location=(x, y, z + trunk_height / 2 - 0.2))

    bpy.context.active_object.name = "Tree"
    return trunk_height - 0.2

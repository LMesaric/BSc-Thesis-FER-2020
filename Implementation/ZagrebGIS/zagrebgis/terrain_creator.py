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


import ntpath
from typing import Tuple

import bmesh
import bpy
from mathutils import Matrix, Vector

from zagrebgis.constants import TERRAIN_VERTICES_DISTANCE
from zagrebgis.heightmap_fetcher import HeightmapMeta


def create_terrain(heightmap_meta: HeightmapMeta, scaling_factor: float):
    """
    Creates terrain from a Grid in 1:1 scale using given heightmap.

    :param heightmap_meta: Heightmap metadata
    :param scaling_factor: Height scaling factor
    """

    y_size, x_size = heightmap_meta.bottom_left.span(heightmap_meta.top_right)
    bigger_side = max(x_size, y_size)

    bpy.ops.mesh.primitive_grid_add(
        x_subdivisions=round(x_size / TERRAIN_VERTICES_DISTANCE),
        y_subdivisions=round(y_size / TERRAIN_VERTICES_DISTANCE),
        size=bigger_side)

    bpy.context.active_object.scale = (x_size / bigger_side, y_size / bigger_side, 1)

    # Clipping must be done even if map is not applied, otherwise
    # the terrain thinks it's a square for some unexplained reason.
    _clip_uv_edges()

    real_world_height = heightmap_meta.max_height - heightmap_meta.min_height
    scaled_real_world_height = real_world_height * scaling_factor
    if scaled_real_world_height <= 0.1:
        # No need to use the heightmap if area is completely flat (less than 10cm of elevation difference)
        # in order to avoid dividing very small numbers (or possibly 0) in height_scale_factor
        return

    bpy.data.images.load(heightmap_meta.path_to_file)
    height_tex = bpy.data.textures.new('Heightmap texture', type='IMAGE')
    # noinspection PyTypeChecker
    height_tex.image = bpy.data.images[_path_leaf(heightmap_meta.path_to_file)]

    disp_mod = bpy.context.active_object.modifiers.new("Displace", type='DISPLACE')
    disp_mod.texture = height_tex
    disp_mod.texture_coords = 'UV'
    disp_mod.mid_level = 0
    disp_mod.strength = 2500  # initial strength guess

    tmp_min, tmp_max = _local_min_max_mods_fake_applied()
    curr_height = tmp_max.z - tmp_min.z
    height_scale_factor = scaled_real_world_height / curr_height
    disp_mod.strength *= height_scale_factor

    bpy.ops.object.modifier_apply(apply_as='DATA', modifier=disp_mod.name)


def _clip_uv_edges(uv_scale_factor=0.999):
    """
    Slightly scales mesh in UV editor to remove artifacts and sharp walls along the edges.

    :param uv_scale_factor: Scaling factor
    """

    bpy.ops.object.mode_set(mode='EDIT')
    bm = bmesh.from_edit_mesh(bpy.context.active_object.data)
    uv_layer = bm.loops.layers.uv.verify()

    uv_translate_factor = (1 - uv_scale_factor) / 2
    scale_matrix = Matrix.Diagonal((uv_scale_factor, uv_scale_factor))

    for face in bm.faces:
        for loop in face.loops:
            loop_uv = loop[uv_layer]
            loop_uv.uv = loop_uv.uv @ scale_matrix + Vector((uv_translate_factor, uv_translate_factor))

    bmesh.update_edit_mesh(bpy.context.active_object.data)
    bpy.ops.object.mode_set(mode='OBJECT')


def _local_min_max_mods_fake_applied() -> Tuple[Vector, Vector]:
    """
    Finds coordinates of vertices with minimum and maximum values of `z` coordinate.
    Behaves as if all modifiers have been applied.

    :return: Coordinates with minimum and maximum value of `z`
    """

    depsgraph = bpy.context.evaluated_depsgraph_get()
    object_eval = bpy.context.object.evaluated_get(depsgraph)
    coords = [v.co for v in object_eval.data.vertices]
    return min(coords, key=lambda v: v.z), max(coords, key=lambda v: v.z)


def _path_leaf(path) -> str:
    """
    Parses `path` and returns the last part. Ignores trailing slashes.

    :param path: Path to parse
    :return: The final part of `path`
    """

    head, tail = ntpath.split(path)
    return tail or ntpath.basename(head)

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


import bpy
from bpy.props import FloatProperty

from zagrebgis.zagreb_gis import VIEW3D_OT_ZagrebGIS


class VIEW3D_PT_ZagrebGISPanel(bpy.types.Panel):
    bl_idname = "VIEW3D_PT_ZagrebGISPanel"
    bl_label = "Generate Zagreb"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "ZagrebGIS"
    bl_context = "objectmode"

    def draw(self, context):
        layout = self.layout
        scene = context.scene

        layout.label(text="Bottom-left coordinates:")
        layout.row().prop(scene, "global_lat_bottom_left", text="Latitude:")
        layout.row().prop(scene, "global_long_bottom_left", text="Longitude:")

        layout.row().separator()

        layout.label(text="Top-right coordinates:")
        layout.row().prop(scene, "global_lat_top_right", text="Latitude:")
        layout.row().prop(scene, "global_long_top_right", text="Longitude:")

        layout.row().separator()

        layout.label(text="Terrain height scaling:")
        layout.row().prop(scene, "global_terrain_height_scale", text="Factor:")

        layout.row().separator()
        layout.row().separator()

        row = layout.row()
        row.scale_y = 1.33

        props = row.operator(VIEW3D_OT_ZagrebGIS.bl_idname)
        props.lat_bottom_left = scene.global_lat_bottom_left
        props.long_bottom_left = scene.global_long_bottom_left
        props.lat_top_right = scene.global_lat_top_right
        props.long_top_right = scene.global_long_top_right
        props.terrain_height_scale = scene.global_terrain_height_scale


def register():
    bpy.utils.register_class(VIEW3D_PT_ZagrebGISPanel)
    s = bpy.types.Scene
    s.global_lat_bottom_left = FloatProperty(default=45.807212, min=-90.0, max=90.0, step=1, precision=6)
    s.global_long_bottom_left = FloatProperty(default=15.971431, min=-180.0, max=180.0, step=1, precision=6)
    s.global_lat_top_right = FloatProperty(default=45.809590, min=-90.0, max=90.0, step=1, precision=6)
    s.global_long_top_right = FloatProperty(default=15.977082, min=-180.0, max=180.0, step=1, precision=6)
    s.global_terrain_height_scale = FloatProperty(default=1, min=0, soft_max=3, step=1, precision=3)


# noinspection PyUnresolvedReferences
def unregister():
    s = bpy.types.Scene
    del s.global_terrain_height_scale
    del s.global_long_top_right
    del s.global_lat_top_right
    del s.global_long_bottom_left
    del s.global_lat_bottom_left
    bpy.utils.unregister_class(VIEW3D_PT_ZagrebGISPanel)

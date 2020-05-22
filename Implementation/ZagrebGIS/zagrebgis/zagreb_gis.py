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


class VIEW3D_OT_ZagrebGIS(bpy.types.Operator):
    bl_idname = "view3d.zagreb_gis"
    bl_label = "Generate Zagreb"
    bl_options = {"REGISTER", "UNDO"}

    lat_bottom_left: bpy.props.FloatProperty(options={'HIDDEN'})
    long_bottom_left: bpy.props.FloatProperty(options={'HIDDEN'})
    lat_top_right: bpy.props.FloatProperty(options={'HIDDEN'})
    long_top_right: bpy.props.FloatProperty(options={'HIDDEN'})

    def execute(self, context):
        if not self.check_input():
            return {'CANCELLED'}

        # noinspection PyTypeChecker
        bpy.ops.mesh.primitive_cube_add(
            location=(self.lat_bottom_left, self.long_bottom_left, self.lat_top_right),
            size=self.long_top_right)

        # TODO Use for notifications: self.report({'INFO'}, "message")
        #  {'DEBUG', 'INFO', 'OPERATOR', 'PROPERTY', 'WARNING', 'ERROR',
        #  'ERROR_INVALID_INPUT', 'ERROR_INVALID_CONTEXT', 'ERROR_OUT_OF_MEMORY'}

        return {'FINISHED'}  # TODO {'CANCELLED', 'FINISHED'}

    def check_input(self) -> bool:
        threshold = 0.2  # roughly 15-20 km
        delta_lat = self.lat_top_right - self.lat_bottom_left
        delta_long = self.long_top_right - self.long_bottom_left

        if delta_lat <= 0:
            self.report({'ERROR_INVALID_INPUT'}, 'Bad latitude interval')
            return False
        if delta_lat > threshold:
            self.report({'ERROR_INVALID_INPUT'}, 'Latitude interval too large')
            return False

        if delta_long <= 0:
            self.report({'ERROR_INVALID_INPUT'}, 'Bad longitude interval')
            return False
        if delta_long > threshold:
            self.report({'ERROR_INVALID_INPUT'}, 'Longitude interval too large')
            return False

        return True


def register():
    bpy.utils.register_class(VIEW3D_OT_ZagrebGIS)


def unregister():
    bpy.utils.unregister_class(VIEW3D_OT_ZagrebGIS)

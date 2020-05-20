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
        # noinspection PyTypeChecker
        bpy.ops.mesh.primitive_cube_add(
            location=(self.lat_bottom_left, self.long_bottom_left, self.lat_top_right),
            size=self.long_top_right)

        # TODO Use for notifications: self.report({'INFO'}, "message")
        return {"FINISHED"}  # TODO {'CANCELLED', 'FINISHED'}


def register():
    bpy.utils.register_class(VIEW3D_OT_ZagrebGIS)


def unregister():
    bpy.utils.unregister_class(VIEW3D_OT_ZagrebGIS)

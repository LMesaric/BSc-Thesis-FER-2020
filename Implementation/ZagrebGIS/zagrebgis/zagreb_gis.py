import bpy


class VIEW3D_OT_ZagrebGIS(bpy.types.Operator):
    bl_idname = "view3d.zagreb_gis"
    bl_label = "Generate Zagreb"
    bl_options = {"REGISTER", "UNDO"}

    lat_left: bpy.props.FloatProperty()
    long_left: bpy.props.FloatProperty()
    lat_right: bpy.props.FloatProperty()
    long_right: bpy.props.FloatProperty()

    def execute(self, context):
        # noinspection PyTypeChecker
        bpy.ops.mesh.primitive_cube_add(
            location=(self.lat_left, self.long_left, self.lat_right),
            size=self.long_right)

        # TODO Use for notifications: self.report({'INFO'}, "message")
        return {"FINISHED"}  # TODO {'CANCELLED', 'FINISHED'}


def register():
    bpy.utils.register_class(VIEW3D_OT_ZagrebGIS)


def unregister():
    bpy.utils.unregister_class(VIEW3D_OT_ZagrebGIS)

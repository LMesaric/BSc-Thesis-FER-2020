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
        layout.row().separator()

        row = layout.row()
        row.scale_y = 1.33

        props = row.operator(VIEW3D_OT_ZagrebGIS.bl_idname)
        props.lat_bottom_left = scene.global_lat_bottom_left
        props.long_bottom_left = scene.global_long_bottom_left
        props.lat_top_right = scene.global_lat_top_right
        props.long_top_right = scene.global_long_top_right


def register():
    bpy.utils.register_class(VIEW3D_PT_ZagrebGISPanel)
    s = bpy.types.Scene
    s.global_lat_bottom_left = FloatProperty(default=45.807489, min=-90.0, max=90.0, step=1, precision=6)
    s.global_long_bottom_left = FloatProperty(default=15.968137, min=-180.0, max=180.0, step=1, precision=6)
    s.global_lat_top_right = FloatProperty(default=45.809628, min=-90.0, max=90.0, step=1, precision=6)
    s.global_long_top_right = FloatProperty(default=15.972560, min=-180.0, max=180.0, step=1, precision=6)


# noinspection PyUnresolvedReferences
def unregister():
    s = bpy.types.Scene
    del s.global_long_top_right
    del s.global_lat_top_right
    del s.global_long_bottom_left
    del s.global_lat_bottom_left
    bpy.utils.unregister_class(VIEW3D_PT_ZagrebGISPanel)

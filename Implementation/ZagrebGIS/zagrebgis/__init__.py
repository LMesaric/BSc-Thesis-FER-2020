# Copyright 2020 Luka Mesarić
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


bl_info = {
    "name": "Zagreb GIS",
    "description": "Generates a Zagreb district model based on real data.",
    "author": "Luka Mesarić",
    "version": (0, 1),
    "blender": (2, 82, 0),  # TODO Check compatibility
    "location": "View3D > Sidebar > ZagrebGIS Tab",
    "tracker_url": "https://github.com/LMesaric/BSc-Thesis-FER-2020/issues",
    "warning": "",
    "support": "COMMUNITY",
    "category": "3D View",
}

if "bpy" in locals():
    import importlib

    if "zagreb_gis" in locals():
        # noinspection PyUnresolvedReferences,PyUnboundLocalVariable
        importlib.reload(zagreb_gis)
    if "zagreb_gis_panel" in locals():
        # noinspection PyUnresolvedReferences,PyUnboundLocalVariable
        importlib.reload(zagreb_gis_panel)
else:
    from zagrebgis import zagreb_gis
    from zagrebgis import zagreb_gis_panel

# noinspection PyUnresolvedReferences
import bpy


def register():
    zagreb_gis.register()
    zagreb_gis_panel.register()


def unregister():
    zagreb_gis_panel.unregister()
    zagreb_gis.unregister()

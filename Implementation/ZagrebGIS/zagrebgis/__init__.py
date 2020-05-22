#    Zagreb GIS - Generates a Zagreb district model based on real data
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

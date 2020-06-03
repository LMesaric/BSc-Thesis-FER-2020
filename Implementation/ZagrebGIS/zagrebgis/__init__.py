#    Zagreb GIS - Generate a Zagreb district model based on real data
#    Copyright (C) 2020  Luka Mesarić (luka.mesaric@fer.hr), Robert Guetzkow
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


# Original code written by Robert Guetzkow is available here:
# https://github.com/robertguetzkow/blender-python-examples/blob/master/add-ons/install-dependencies/install-dependencies.py


bl_info = {
    "name": "Zagreb GIS",
    "description": "Generates a Zagreb district model based on real data.",
    "author": "Luka Mesarić",
    "version": (0, 4),
    "blender": (2, 82, 0),  # TODO Check compatibility
    "location": "View3D > Sidebar > ZagrebGIS Tab",
    "tracker_url": "https://github.com/LMesaric/BSc-Thesis-FER-2020/issues",
    "warning": "Requires installation of dependencies",
    "support": "COMMUNITY",
    "category": "3D View",
}

import subprocess
from collections import namedtuple

Dependency = namedtuple("Dependency", ["module", "package", "name"])
dependencies = (Dependency(module="PIL", package="Pillow", name=None),
                Dependency(module="requests", package=None, name=None),
                Dependency(module="pyproj", package=None, name=None))

dependencies_installed = False

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

import bpy


def import_module(module_name, global_name=None):
    """
    Import a module.
    :param module_name: Module to import.
    :param global_name: (Optional) Name under which the module is imported. If None the module_name will be used.
       This allows to import under a different name with the same effect as e.g. "import numpy as np" where "np" is
       the global_name under which the module can be accessed.
    :raises: ImportError and ModuleNotFoundError
    """

    import importlib

    if global_name is None:
        global_name = module_name

    # Attempt to import the module and assign it to globals dictionary. This allows to access the module under
    # the given name, just like the regular import would.
    globals()[global_name] = importlib.import_module(module_name)


def import_dependency(dep: Dependency):
    import_module(module_name=dep.module, global_name=dep.name)


def install_pip():
    """
    Installs pip if not already present. Please note that ensurepip.bootstrap() also calls pip, which adds the
    environment variable PIP_REQ_TRACKER. After ensurepip.bootstrap() finishes execution, the directory doesn't exist
    anymore. However, when subprocess is used to call pip, in order to install a package, the environment variables
    still contain PIP_REQ_TRACKER with the now nonexistent path. This is a problem since pip checks if PIP_REQ_TRACKER
    is set and if it is, attempts to use it as temp directory. This would result in an error because the
    directory can't be found. Therefore, PIP_REQ_TRACKER needs to be removed from environment variables.
    """

    try:
        # Check if pip is already installed
        subprocess.run([bpy.app.binary_path_python, "-m", "pip", "--version"], check=True)
    except subprocess.CalledProcessError:
        import os
        import ensurepip

        ensurepip.bootstrap()
        os.environ.pop("PIP_REQ_TRACKER", None)


def install_and_import_module(module_name, package_name=None, global_name=None):
    """
    Installs the package through pip and attempts to import the installed module.
    :param module_name: Module to import.
    :param package_name: (Optional) Name of the package that needs to be installed. If None it is assumed to be equal
       to the module_name.
    :param global_name: (Optional) Name under which the module is imported. If None the module_name will be used.
       This allows to import under a different name with the same effect as e.g. "import numpy as np" where "np" is
       the global_name under which the module can be accessed.
    :raises: subprocess.CalledProcessError and ImportError
    """

    if package_name is None:
        package_name = module_name

    if global_name is None:
        global_name = module_name

    # Try to install the package. This may fail with subprocess.CalledProcessError
    subprocess.run([bpy.app.binary_path_python, "-m", "pip", "install", package_name], check=True)

    # The installation succeeded, attempt to import the module again
    import_module(module_name, global_name)


class VIEW3D_PT_ZagrebGIS_warning_panel(bpy.types.Panel):
    bl_label = "Warning: Missing Dependencies"
    bl_category = "ZagrebGIS"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"

    @classmethod
    def poll(cls, _):
        return not dependencies_installed

    def draw(self, context):
        lines = [f"Please install the missing dependencies for the \"{bl_info.get('name')}\" add-on.",
                 f"1. Open the preferences (Edit > Preferences > Add-ons).",
                 f"2. Search for the \"{bl_info.get('name')}\" add-on.",
                 f"3. Open the details section of the add-on.",
                 f"4. Click on the \"{VIEW3D_OT_ZagrebGIS_install_dependencies.bl_label}\" button.",
                 f"   This will download and install the missing Python packages, if Blender has the required",
                 f"   permissions. If you see an error, try starting Blender with Administrator powers.",
                 f"If you're attempting to run the add-on from the text editor, you won't see the options",
                 f"described above. Please install the add-on properly through the preferences.",
                 f"1. Open the add-on preferences (Edit > Preferences > Add-ons).",
                 f"2. Press the \"Install\" button.",
                 f"3. Search for the add-on file.",
                 f"4. Confirm the selection by pressing the \"Install Add-on\" button in the file browser."]

        for line in lines:
            self.layout.label(text=line)


class VIEW3D_OT_ZagrebGIS_install_dependencies(bpy.types.Operator):
    bl_idname = "view3d.zagreb_gis_install_dependencies"
    bl_label = "Install dependencies"
    bl_description = ("Downloads and installs the required Python packages for this add-on. "
                      "Internet connection is required. Blender may have to be started with "
                      "elevated permissions in order to install the package.")
    bl_options = {"REGISTER", "INTERNAL"}

    @classmethod
    def poll(cls, _):
        # Deactivate when dependencies have been installed
        return not dependencies_installed

    def execute(self, context):
        try:
            install_pip()
            for dependency in dependencies:
                install_and_import_module(module_name=dependency.module,
                                          package_name=dependency.package,
                                          global_name=dependency.name)
        except (subprocess.CalledProcessError, ImportError) as err:
            self.report({"ERROR"}, str(err))
            return {"CANCELLED"}

        global dependencies_installed
        dependencies_installed = True

        # Register the panels, operators, etc. since dependencies are installed
        for module in modules:
            module.register()

        return {"FINISHED"}


class VIEW3D_ZagrebGIS_preferences(bpy.types.AddonPreferences):
    bl_idname = __name__

    def draw(self, _):
        self.layout.operator(VIEW3D_OT_ZagrebGIS_install_dependencies.bl_idname, icon="CONSOLE")


modules = (zagreb_gis,
           zagreb_gis_panel)

preference_classes = (VIEW3D_PT_ZagrebGIS_warning_panel,
                      VIEW3D_OT_ZagrebGIS_install_dependencies,
                      VIEW3D_ZagrebGIS_preferences)


def register():
    global dependencies_installed
    dependencies_installed = False

    for cls in preference_classes:
        bpy.utils.register_class(cls)

    try:
        for dependency in dependencies:
            import_dependency(dependency)
        dependencies_installed = True
    except ModuleNotFoundError:
        # Don't register other panels, operators etc.
        return

    for module in modules:
        module.register()


def unregister():
    for cls in preference_classes:
        bpy.utils.unregister_class(cls)

    if dependencies_installed:
        for module in modules:
            module.unregister()


if __name__ == "__main__":
    register()

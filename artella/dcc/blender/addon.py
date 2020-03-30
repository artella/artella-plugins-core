#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains Artella Blender Addon implementation
"""

from __future__ import print_function, division, absolute_import

import bpy

import artella


blender_version = bpy.app.version
if blender_version[0] < 2:
    artella.log_warning('Versions of Blender lower than 2 are not supported!')
else:
    if blender_version[1] <= 79:
        def artella_menu_items(self, context):
            l = (('SAVE_TO_CLOUD', 'Save to Cloud', 'Save file to cloud'),
                 ('GET_DEPENDENCIES', 'Get Dependencies', 'Get Dependencies'))
            artella_menu_items.lookup = {id: name for id, name, desc in l}
            return l


        class ArtellaAddon(bpy.types.Operator):
            bl_idname = "artella.addon"
            bl_label = "Artella"
            info = bpy.props.StringProperty()

            artella_items = bpy.props.EnumProperty(items=artella_menu_items)

            def execute(self, context):
                sel_item_text = artella_menu_items.lookup[self.artella_items]
                if sel_item_text == 'Save to Cloud':
                    self.report({'INFO'}, 'Artella - Saving to Cloud')
                    artella.Plugin().make_new_version()
                elif sel_item_text == 'Get Dependencies':
                    self.report({'INFO'}, 'Artella - Get dependencies')
                    artella.Plugin().get_dependencies()

                return {'FINISHED'}


        def artella_menu(self, context):
            layout = self.layout
            layout.operator_menu_enum(ArtellaAddon.bl_idname, "artella_items", text=ArtellaAddon.bl_label)
    else:

        class SaveToCloudProps(bpy.types.PropertyGroup):

            comment : bpy.props.StringProperty(
                name="Comment: ", description="Comment used for new version", default="")

        class SaveToCloudOperator(bpy.types.Operator):
            bl_idname = "artella.save_to_cloud"
            bl_label = "Save to Cloud"
            bl_description = 'Creates a new version of current opened file in Artella'

            def execute(self, context):
                artella.Plugin().make_new_version()

                return {'FINISHED'}

        class GetDependencies(bpy.types.Operator):
            bl_idname = "artella.get_deps"
            bl_label = "Get Dependencies"

            def execute(self, context):
                artella.Plugin().get_dependencies()

                return {'FINISHED'}

        class ArtellaPanel(bpy.types.Panel):

            bl_space_type = "VIEW_3D"
            bl_region_type = "UI"
            bl_category = "Artella"
            bl_options = {"DEFAULT_CLOSED"}
            bl_idname = "Artella_Panel"
            bl_label = "Artella"

            def draw(self, context):
                layout = self.layout
                save_to_cloud_props = context.scene.SaveToCloudProps
                layout.operator("artella.save_to_cloud")
                layout.prop(save_to_cloud_props, "comment")
                layout.separator()
                layout.operator("artella.get_deps")


if blender_version[0] >= 2:
    if blender_version[1] <= 79:
        def register():
            bpy.utils.register_class(ArtellaAddon)
            bpy.types.INFO_HT_header.append(artella_menu)

        def unregister():
            bpy.utils.unregister_class(ArtellaAddon)
            bpy.types.INFO_HT_header.remove(artella_menu)
    else:
        def register():
            bpy.utils.register_class(SaveToCloudOperator)
            bpy.utils.register_class(GetDependencies)
            bpy.utils.register_class(ArtellaPanel)
            bpy.utils.register_class(SaveToCloudProps)
            bpy.types.Scene.SaveToCloudProps = bpy.props.PointerProperty(type=SaveToCloudProps)

        def unregister():
            bpy.utils.unregister_class(SaveToCloudOperator)
            bpy.utils.register_class(GetDependencies)
            bpy.utils.unregister_class(ArtellaPanel)
            bpy.utils.unregister_class(SaveToCloudProps)
            del bpy.types.Scene.SaveToCloudProps

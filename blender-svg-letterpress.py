# UI Based on excelent post:
# https://blender.stackexchange.com/questions/57306/how-to-create-a-custom-ui

bl_info = {
    "name": "3D Letterpress Add-on",
    "description": "",
    "author": "borisjerenec",
    "version": (0, 0, 1),
    "blender": (2, 90, 0),
    "location": "3D View > Letterpress",
    "warning": "", # used for warning icon and text in addons panel
    "wiki_url": "",
    "tracker_url": "",
    "category": "Development"
}


import bpy

from bpy.props import (StringProperty,
                       BoolProperty,
                       IntProperty,
                       FloatProperty,
                       FloatVectorProperty,
                       EnumProperty,
                       PointerProperty,
                       )
from bpy.types import (Panel,
                       Menu,
                       Operator,
                       PropertyGroup,
                       )


# ------------------------------------------------------------------------
#    Scene Properties
# ------------------------------------------------------------------------

class MyProperties(PropertyGroup):


    type_height: FloatProperty(
        name = "Type height",
        description = "Type high for your letterpress machine in mm",
        default = 23.32,
        min = 0.01,
        max = 50.0
        )
        
    head_height: FloatProperty(
        name = "Head height",
        description = "Extruded head height in mm",
        default = 1.5,
        min = 0.01,
        max = 5
        )
        
    chasebase_height: FloatProperty(
        name = "Chase base height",
        description = "Chase base height in mm (0 if not used)",
        default = 0,
        min = 0.00,
        max = 30
        )
        
    base_margin: FloatProperty(
        name = "Base margin",
        description = "Base margin in mm",
        default = 1,
        min = 0.00,
        max = 30
        )
        
    mirror: BoolProperty(
        name="Mirror graphics",
        description="",
        default = False
        )


# ------------------------------------------------------------------------
#    Operators
# ------------------------------------------------------------------------

class WM_OT_Transform(Operator):
    bl_label = "Transform"
    bl_idname = "wm.transform"
    
    @classmethod
    def poll(cls, context):
        obj = context.active_object
        objs = context.selected_objects
        
        if len(objs) == 0: 
            return False
        if obj.type == 'CURVE': 
            return True
        
        return False

    def execute(self, context):
        scene = context.scene
        mytool = scene.my_tool

        # in mm
        type_height = mytool.type_height                        # type high / full height of final object

        full_height = type_height - mytool.chasebase_height     # will it be mounted on chase base?
        head_height = mytool.head_height                        # final height of the extruded face
        plate_margin = 1                                        # additional frame padding   

        mirror = mytool.mirror
         
        # calculate others
        plate_height = full_height - head_height                # plate/shoulder height
        extrude_height = head_height                            # half of the extrusion will be in body plate (to union)


        plate_translate_z = plate_height / 2                    # to move plate to z=0
        extrude_translate_z = plate_height


        # svg is selected
        svg = bpy.context.object

        # SCALE, this seems to work correctly for exports from Illustrator
        svg.scale[0] = 1250
        svg.scale[1] = 1250
        svg.scale[2] = 1000 # keep at 1000x to easier calculate height ...

        # CLEAR SCALE TRANSFORMS
        #bpy.ops.object.parent_clear(type='CLEAR_KEEP_TRANSFORM')

        # EXTRUDE
        svg.data.extrude = extrude_height / 1000

        # CENTER AND MOVE UP
        bpy.ops.object.origin_set(type='GEOMETRY_ORIGIN', center='BOUNDS')
        bpy.ops.transform.translate(value=(0, 0, extrude_translate_z), orient_type='GLOBAL', orient_matrix=((1, 0, 0), (0, 1, 0), (0, 0, 1)), orient_matrix_type='GLOBAL', constraint_axis=(False, False, True), mirror=True, use_proportional_edit=False, proportional_edit_falloff='SMOOTH', proportional_size=1, use_proportional_connected=False, use_proportional_projected=False, release_confirm=True)

        # CONVERT TO MESH
        bpy.ops.object.convert(target='MESH')

        # CREATE BOX, USE SVG DIMENSIONS
        x_scale = (svg.dimensions[0] + plate_margin) * 2
        y_scale = (svg.dimensions[1] + plate_margin) * 2
        z_scale = plate_height * 2

        bpy.ops.mesh.primitive_cube_add(size=1, enter_editmode=False, align='WORLD', location=(0, 0, 0), scale=(x_scale, y_scale, z_scale))
        bpy.ops.transform.translate(value=(0, 0, plate_translate_z), orient_type='GLOBAL', orient_matrix=((1, 0, 0), (0, 1, 0), (0, 0, 1)), orient_matrix_type='GLOBAL', constraint_axis=(False, False, True), mirror=True, use_proportional_edit=False, proportional_edit_falloff='SMOOTH', proportional_size=1, use_proportional_connected=False, use_proportional_projected=False)
        cube = bpy.context.object


        # UNION CUBE AND SVG EXTRUDED MESH
        bpy.ops.object.modifier_add(type='BOOLEAN')
        bpy.context.object.modifiers["Boolean"].operation = 'UNION'
        bpy.context.object.modifiers["Boolean"].object = bpy.data.objects["Curve"]
        bpy.ops.object.modifier_apply(modifier="Boolean")

        # MIROR IF NEEDED
        if mirror:
            bpy.ops.transform.mirror(orient_type='GLOBAL', orient_matrix=((1, 0, 0), (0, 1, 0), (0, 0, 1)), orient_matrix_type='GLOBAL', constraint_axis=(True, False, False), use_proportional_edit=False, proportional_edit_falloff='SMOOTH', proportional_size=1, use_proportional_connected=False, use_proportional_projected=False)


        # DELETE SVG EXTRUDED MESH
        bpy.data.objects.remove(svg)

        return {'FINISHED'}
    
    
    
class WM_OT_Presets(Operator):
    bl_label = "Presets"
    bl_idname = "wm.presets"
    preset_num = IntProperty(default=0)

    def execute(self, context):
        scene = context.scene
        mytool = scene.my_tool
        
        if self.preset_num == 0:
            mytool.chasebase_height = 0.0
            mytool.type_height = 23.32
            
        elif self.preset_num == 1:
            mytool.chasebase_height = 0.0
            mytool.type_height = 23.57
            
        elif self.preset_num == 2:
            mytool.chasebase_height = 19.0
            mytool.type_height = 23.32

        return {'FINISHED'}

# ------------------------------------------------------------------------
#    Menus
# ------------------------------------------------------------------------

class OBJECT_MT_CustomMenu(bpy.types.Menu):
    bl_label = "Select"
    bl_idname = "OBJECT_MT_custom_menu"

    def draw(self, context):
        layout = self.layout

        # Built-in operators
        layout.operator("wm.presets", text="UK/USA 0.918\" (23.32 mm)").preset_num = 0
        layout.operator("wm.presets", text="Europe 0.928\" (23.57 mm)").preset_num = 1
        layout.operator("wm.presets", text="UK/USA + 19 mm base").preset_num = 2

# ------------------------------------------------------------------------
#    Panel in Object Mode
# ------------------------------------------------------------------------

class OBJECT_PT_CustomPanel(Panel):
    bl_label = "3D letterpress"
    bl_idname = "OBJECT_PT_custom_panel"
    bl_space_type = "VIEW_3D"   
    bl_region_type = "UI"
    bl_category = "Letterpress"
    bl_context = "objectmode"   


    @classmethod
    def poll(self,context):
        return context.object is not None

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        mytool = scene.my_tool

        layout.label(text="Import and select SVG curve.")

        layout.prop(mytool, "type_height")
        layout.prop(mytool, "head_height")
        
        layout.separator()
        layout.prop(mytool, "base_margin")        
        layout.prop(mytool, "chasebase_height")
        
        layout.separator()
        
        layout.menu(OBJECT_MT_CustomMenu.bl_idname, text="Presets", icon="MENU_PANEL")

        layout.separator()
        layout.prop(mytool, "mirror")
        
        layout.operator("wm.transform")

# ------------------------------------------------------------------------
#    Registration
# ------------------------------------------------------------------------

classes = (
    MyProperties,
    WM_OT_Transform,
    WM_OT_Presets,
    OBJECT_MT_CustomMenu,
    OBJECT_PT_CustomPanel
)

def register():
    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)

    bpy.types.Scene.my_tool = PointerProperty(type=MyProperties)

def unregister():
    from bpy.utils import unregister_class
    for cls in reversed(classes):
        unregister_class(cls)
    del bpy.types.Scene.my_tool


if __name__ == "__main__":
    register()
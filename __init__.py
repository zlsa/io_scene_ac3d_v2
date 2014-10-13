
bl_info = {
  "name":        "AC3D (.ac)",
  "category":    "Import-Export",
  "author":      "ZLSA",
  "description": "Import and export AC3D files",
  "location":    "File > Import/Export > AC3D",
  "version":     (0, 1),
  "blender":     (2, 72, 0),
  "warning":     "Alpha",
}

import bmesh
import time
import bpy
from bpy.props import *
import math
from bpy_extras.io_utils import ExportHelper
import os

# TRIANGULATE

def mesh_triangulate(input_mesh):
  bm = bmesh.new()
  bm.from_mesh(input_mesh)
  bmesh.ops.triangulate(bm, faces = bm.faces)
  bm.to_mesh(input_mesh)
  bm.free()

# EXPORT

def export(limit_render_layers = True,
           limit_selection     = False):
  out  = ""

  out += "AC3Db\n"

  scene = bpy.context.scene

  objects = []

  # first, get a list of objects that will be exported
  for o in scene.objects:
    slots = o.material_slots

    # only go ahead if there are any materials
    if len(slots) == 0: continue
    for slot in slots: materials.append(slot.material)

  # then, get all materials
  materials = []
  for o in objects:
    slots = o.material_slots

    # only go ahead if there are any materials
    if len(slots) == 0: continue
    for slot in slots: materials.append(slot.material)

  # now print out all of them
  for material in materials:
    diffuse      = material.diffuse_color
    ambient      = material.ambient * material.diffuse_color
    emission     = material.emit * material.diffuse_color
    specular     = material.specular_color
    shininess    = material.specular_intensity
    transparency = 1 - material.alpha

    mat = {
      "name":         material.name,
      "rgb":          " ".join([str(round(x, 4)) for x in diffuse]),
      "amb":          " ".join([str(round(x, 4)) for x in ambient]),
      "emission":     " ".join([str(round(x, 4)) for x in emission]),
      "specular":     " ".join([str(round(x, 4)) for x in specular]),
      "shininess":    str(round(shininess, 4)),
      "transparency": str(round(transparency, 4))
    }
    out += """MATERIAL "{name}" rgb {rgb} amb {amb} emis {emission} spec {specular} shi {shininess} trans {transparency}  \n""".format(**mat)

  material_indexes = {}
  i = 0
  for material in materials:
    material_indexes[material.name] = i
    i += 1

  out += "OBJECT world\n"
  out += "name {name}\n".format(name = scene.world.name)
  out += "kids {children}\n".format(children = str(len(scene)))

  for obj in scene.objects:
    obj_out  = ""
    obj_out += "OBJECT {name}\n".format(name = obj.name)

    if obj.type != "MESH": continue; # will have to fix to allow parenting to empties
    mesh = obj.to_mesh(bpy.context.scene, True, "RENDER")

  return out

class ExportAC3D(bpy.types.Operator,ExportHelper):
  """Exports the file as an AC3D model"""
  bl_idname     = "export_scene.ac3d"
  bl_label      = "Export AC3D (test)"
  filename_ext  = ".ac"
 
  LimitRenderLayers = bpy.props.BoolProperty(
    name        = "Limit to render layers",
    description = "Limits export to objects on render layers",
    default     = True)

  LimitSelection = bpy.props.BoolProperty(
    name        = "Limit to selection",
    description = "Limits export to selected objects",
    default     = False)

  FaceMaterials = bpy.props.BoolProperty(
    name        = "Face materials",
    description = "Use face materials when exporting",
    default     = False)

  def execute(self,context):
    filepath=self.filepath
    e=export(
      limit_render_layers = self.LimitRenderLayers,
      limit_selection     = self.LimitSelection
    )
    open(filepath,"w").write(e)
    return {"FINISHED"}

  def invoke(self,context,event):
    wm = context.window_manager
    wm.fileselect_add(self)
    return {"RUNNING_MODAL"}

def menu_func(self,context):
  self.layout.operator(ExportAC3D.bl_idname, text = "AC3D (test) (.ac)")

def register():
  bpy.utils.register_module(__name__)
  bpy.types.INFO_MT_file_export.append(menu_func)

def unregister():
  bpy.utils.unregister_module(__name__)
  bpy.types.INFO_MT_file_export.remove(menu_func)


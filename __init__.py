
bl_info = {
  "name":        "AC3D v2 (.ac)",
  "category":    "Import-Export",
  "author":      "ZLSA",
  "description": "Import and export AC3D files",
  "location":    "File > Import/Export > AC3D v2",
  "version":     (0, 1),
  "blender":     (2, 72, 0),
  "warning":     "Alpha",
}

import bpy
from bpy.props import *
import math
from bpy_extras.io_utils import ExportHelper
import os

# Export

def export(forwards            = "+Z",
           up                  = "+Y",
           limit_render_layers = True,
           limit_selection     = False):
  out  = ""

  out += "AC3Db\n"

  scene = bpy.context.scene

  objects = []

  def transform_xyz(v):
    ix, iy, iz = v
    return ix, iz, -iy

  def should_export(obj):
    if limit_render_layers:
      on_render_layer = False
      for layer in range(len(scene.layers)):
        if scene.layers[layer] and obj.layers[layer]:
          on_render_layer = True
          break
      if not on_render_layer: return False
    if limit_selection and not obj.select: return False
    return True

  # first, get a list of objects that will be exported
  for obj in scene.objects:
    if not obj.parent and should_export(obj):
      objects.append(obj)

  # then, get all materials
  materials = []
  for obj in scene.objects:
    slots = obj.material_slots

    # only go ahead if there are any materials
    if len(slots) == 0 or not should_export(obj): continue
    for slot in slots: 
      if slot.material not in materials:
        materials.append(slot.material)

  # Default material
  out += """MATERIAL "DefaultWhite" rgb 1.0 1.0 1.0 amb 0.2 0.2 0.2 emis 0.0 0.0 0.0 spec 0.2 0.2 0.2 shi 0.6 trans 0\n"""
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
    out += """MATERIAL "{name}" rgb {rgb} amb {amb} emis {emission} spec {specular} shi {shininess} trans {transparency}\n""".format(**mat)

  material_indexes = {}
  i = 1
  for material in materials:
    material_indexes[material.name] = i
    i += 1

  out += "OBJECT world\n"
  out += "name \"{name}\"\n".format(name = scene.world.name)
  out += "kids {children}\n".format(children = str(len(objects)))

  def export_object(obj):
    obj_out  = ""

    obj_type = "group"
    if obj.type == "MESH": obj_type = "poly"

    obj_out += "OBJECT {obj_type}\n".format(obj_type = obj_type)
    obj_out += "name \"{name}\"\n".format(name = obj.name)

    # get child number
    children = 0
    for o in obj.children:
      if should_export(o):
        children += 1

    # location
    x, y, z  = transform_xyz(obj.matrix_local.to_translation())
    obj_out += "loc {:5.10f} {:5.10f} {:5.10f}\n".format(x, y, z)

    # rotation
    matrix   = obj.matrix_local.to_quaternion().to_matrix()
    obj_out += "rot"
    for x in range(0, 3):
      x, y, z  = matrix[x]
      obj_out += " {:5.10f} {:5.10f} {:5.10f}".format(x, y, z)
    obj_out += "\n"

    # export mesh data
    if obj.type == "MESH":
      mesh = obj.to_mesh(scene, True, "RENDER")
      slots = obj.material_slots

      vertex_number = len(mesh.vertices)
      face_number   = len(mesh.polygons)

      # handle vertices
      obj_out += "numvert {vertex_number}\n".format(vertex_number = str(vertex_number))
      for vertex in mesh.vertices:
        x, y, z = transform_xyz(vertex.co)
        obj_out += "{:5.10f} {:5.10f} {:5.10f}\n".format(x, y, z)

      # handle faces
      obj_out += "numsurf {face_number}\n".format(face_number = str(face_number))
      for poly in mesh.polygons:
        shading = 0
        if mesh.show_double_sided: shading &= 1<<2
        obj_out += "SURF 0X{shading}\n".format(shading = str(shading << 4))
        if len(slots) == 0:
          obj_out += "mat 0\n"
        else:
          obj_out += "mat {index}\n".format(index = str(material_indexes[slots[poly.material_index].name]))
        obj_out += "refs {vertices}\n".format(vertices = str(len(poly.vertices)))
        for vertex in poly.vertices:
          obj_out += "{vertex} 0 0\n".format(vertex = str(vertex))

    # handle children
    obj_out += "kids {children}\n".format(children = str(children))
    
    for o in obj.children:
      if should_export(o):
        obj_out += export_object(o)

    return obj_out

  for obj in objects:
    out += export_object(obj)

  return out


# Export operator

class ExportAC3D(bpy.types.Operator,ExportHelper):
  """Exports the file as an AC3D model (v2)"""
  bl_idname     = "export_scene.ac3d_v2"
  bl_label      = "Export AC3D v2"

  filename_ext  = ".ac"
  filter_glob = StringProperty(
    default = "*.ac",
    options = {"HIDDEN"},
  )
 
  # Forwards = bpy.props.EnumProperty(
  #   name        = "Forward",
  #   description = "Transforms Blender's native +Y",
  #   items       = [
  #     ("+X", "+X", "Positive X"),
  #     ("+Y", "+Y", "Positive Y"),
  #     ("+Z", "+Z", "Positive Z"),
  #     ("-X", "-X", "Negative X"),
  #     ("-Y", "-Y", "Negative Y"),
  #     ("-Z", "-Z", "Negative Z"),
  #   ],
  #   default     = "+Z")

  # Up = bpy.props.EnumProperty(
  #   name        = "Up",
  #   description = "Transforms Blender's native +Z",
  #   items       = [
  #     ("+X", "+X", "Positive X"),
  #     ("+Y", "+Y", "Positive Y"),
  #     ("+Z", "+Z", "Positive Z"),
  #     ("-X", "-X", "Negative X"),
  #     ("-Y", "-Y", "Negative Y"),
  #     ("-Z", "-Z", "Negative Z"),
  #   ],
  #   default     = "+Y")

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
    filepath = self.filepath
    text     = export(
#      forwards            = self.Forwards,
#      up                  = self.Up,
      limit_render_layers = self.LimitRenderLayers,
      limit_selection     = self.LimitSelection
    )
    open(filepath,"w").write(text)
    return {"FINISHED"}

  def invoke(self,context,event):
    wm = context.window_manager
    wm.fileselect_add(self)
    return {"RUNNING_MODAL"}

def menu_func(self,context):
  self.layout.operator(ExportAC3D.bl_idname, text = "AC3D (.ac) v2")

def register():
  bpy.utils.register_module(__name__)
  bpy.types.INFO_MT_file_export.append(menu_func)

def unregister():
  bpy.utils.unregister_module(__name__)
  bpy.types.INFO_MT_file_export.remove(menu_func)


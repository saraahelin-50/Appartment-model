"""Build a movable, provisional L-shaped wardrobe component."""

import bpy


COLLECTION_NAME = "Wardrobe Component"
ROOT_OBJECT_NAME = "Wardrobe - Move as one"

# Confirmed plan dimensions; the height and board thickness are provisional.
MAIN_RUN_WIDTH_M = 1.50
BAY_COUNT = 3
NOMINAL_BAY_WIDTH_M = MAIN_RUN_WIDTH_M / BAY_COUNT
SHELF_DEPTH_M = 0.35
RETURN_LENGTH_M = 0.60
MIRROR_WIDTH_M = 0.50
WARDROBE_HEIGHT_M = 2.10
PANEL_THICKNESS_M = 0.018

# Place the component beside, not on top of, the apartment in the combined scene.
SCENE_PLACEMENT = (12.0, 0.0, 0.0)


def make_material(name, color, roughness):
    material = bpy.data.materials.get(name)
    if material is None:
        material = bpy.data.materials.new(name)
    material.diffuse_color = color
    material.roughness = roughness
    if material.node_tree:
        principled = material.node_tree.nodes.get("Principled BSDF")
        if principled:
            principled.inputs["Base Color"].default_value = color
            principled.inputs["Roughness"].default_value = roughness
            if name == "Wardrobe - Mirror":
                principled.inputs["Metallic"].default_value = 0.85
    return material


def add_box(name, center, dimensions, material, collection, parent):
    x, y, z = center
    dx, dy, dz = dimensions
    vertices = [
        (x - dx / 2, y - dy / 2, z - dz / 2),
        (x + dx / 2, y - dy / 2, z - dz / 2),
        (x + dx / 2, y + dy / 2, z - dz / 2),
        (x - dx / 2, y + dy / 2, z - dz / 2),
        (x - dx / 2, y - dy / 2, z + dz / 2),
        (x + dx / 2, y - dy / 2, z + dz / 2),
        (x + dx / 2, y + dy / 2, z + dz / 2),
        (x - dx / 2, y + dy / 2, z + dz / 2),
    ]
    faces = (
        (0, 3, 2, 1),
        (4, 5, 6, 7),
        (0, 1, 5, 4),
        (1, 2, 6, 5),
        (2, 3, 7, 6),
        (3, 0, 4, 7),
    )
    mesh = bpy.data.meshes.new(name + " Mesh")
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    collection.objects.link(obj)
    obj.parent = parent
    obj.data.materials.append(material)
    return obj


old_collection = bpy.data.collections.get(COLLECTION_NAME)
if old_collection:
    for obj in list(old_collection.objects):
        bpy.data.objects.remove(obj, do_unlink=True)
    bpy.data.collections.remove(old_collection, do_unlink=True)

collection = bpy.data.collections.new(COLLECTION_NAME)
apartment_collection = bpy.data.collections.get("Apartment Model - Provisional")
furniture_collection = bpy.data.collections.get("Furniture")
if furniture_collection is None:
    bpy.context.scene.collection.children.link(collection)
else:
    furniture_collection.children.link(collection)

root = bpy.data.objects.new(ROOT_OBJECT_NAME, None)
root.empty_display_type = "CUBE"
root.empty_display_size = 0.15
root.location = SCENE_PLACEMENT if apartment_collection else (0.0, 0.0, 0.0)
collection.objects.link(root)

white = make_material("Wardrobe - Warm White", (0.91, 0.89, 0.85, 1.0), 0.78)
mirror = make_material("Wardrobe - Mirror", (0.48, 0.56, 0.60, 1.0), 0.12)
shadow = make_material("Wardrobe - Drawer Recess", (0.12, 0.12, 0.11, 1.0), 0.68)

width = MAIN_RUN_WIDTH_M
depth = SHELF_DEPTH_M
height = WARDROBE_HEIGHT_M
thickness = PANEL_THICKNESS_M
bay_width = NOMINAL_BAY_WIDTH_M
main_front_y = -depth
main_back_y = 0.0
main_center_y = (main_front_y + main_back_y) / 2
main_shelf_y = (main_front_y + thickness + main_back_y - thickness) / 2

# Main three-bay shelving run. Overall width is 150 cm; vertical panels sit
# within that span, so clear openings are slightly narrower than 50 cm.
add_box(
    "Main run back panel",
    (width / 2, -thickness / 2, height / 2),
    (width, thickness, height),
    white,
    collection,
    root,
)
for index, x in enumerate((thickness / 2, width - thickness / 2)):
    add_box(
        "Main run end panel " + str(index + 1),
        (x, main_center_y, height / 2),
        (thickness, depth, height),
        white,
        collection,
        root,
    )
for index in range(1, BAY_COUNT):
    add_box(
        "Main run divider " + str(index),
        (index * bay_width, main_center_y, height / 2),
        (thickness, depth, height),
        white,
        collection,
        root,
    )
for name, z in (
    ("Main run bottom", thickness / 2),
    ("Main run top", height - thickness / 2),
):
    add_box(
        name,
        (width / 2, main_center_y, z),
        (width, depth, thickness),
        white,
        collection,
        root,
    )

drawer_height = 0.18
drawer_pitch = 0.21
drawer_count = 4
drawer_top = 0.90
for bay_index in range(BAY_COUNT):
    bay_center_x = (bay_index + 0.5) * bay_width
    for drawer_index in range(drawer_count):
        z = drawer_top - drawer_height / 2 - drawer_index * drawer_pitch
        drawer_width = bay_width - 0.035
        add_box(
            "Main bay %d drawer %d front" % (bay_index + 1, drawer_index + 1),
            (bay_center_x, main_front_y - thickness / 2, z),
            (drawer_width, thickness, drawer_height),
            white,
            collection,
            root,
        )
        add_box(
            "Main bay %d drawer %d finger recess" % (bay_index + 1, drawer_index + 1),
            (bay_center_x, main_front_y - thickness - 0.001, z + drawer_height / 2 - 0.025),
            (drawer_width - 0.04, 0.006, 0.012),
            shadow,
            collection,
            root,
        )

for bay_index in range(BAY_COUNT):
    bay_center_x = (bay_index + 0.5) * bay_width
    for shelf_index, z in enumerate((0.93, 1.30, 1.67, height - thickness / 2)):
        add_box(
            "Main bay %d shelf %d" % (bay_index + 1, shelf_index + 1),
            (bay_center_x, main_shelf_y, z),
            (bay_width - thickness, depth - 2 * thickness, thickness),
            white,
            collection,
            root,
        )

# Perpendicular 60 cm return with open shelves above broad lower drawers.
return_depth = depth
return_width = RETURN_LENGTH_M
return_x0 = width - return_depth
return_center_x = width - return_depth / 2
return_y0 = main_front_y
return_y1 = return_y0 - return_width
return_center_y = (return_y0 + return_y1) / 2
add_box(
    "Return outer back panel",
    (width - thickness / 2, return_center_y, height / 2),
    (thickness, return_width, height),
    white,
    collection,
    root,
)
for index, y in enumerate((return_y0 - thickness / 2, return_y1 + thickness / 2)):
    add_box(
        "Return end panel " + str(index + 1),
        (return_center_x, y, height / 2),
        (return_depth, thickness, height),
        white,
        collection,
        root,
    )
for name, z in (
    ("Return bottom", thickness / 2),
    ("Return top", height - thickness / 2),
    ("Return shelf 1", 0.93),
    ("Return shelf 2", 1.30),
    ("Return shelf 3", 1.67),
):
    add_box(
        name,
        (return_center_x, return_center_y, z),
        (return_depth - thickness, return_width - 2 * thickness, thickness),
        white,
        collection,
        root,
    )

return_drawer_height = 0.22
for drawer_index in range(4):
    z = 0.13 + drawer_index * 0.23 + return_drawer_height / 2
    add_box(
        "Return drawer %d front" % (drawer_index + 1),
        (return_x0 - thickness / 2, return_center_y, z),
        (thickness, return_width - 0.04, return_drawer_height),
        white,
        collection,
        root,
    )
    add_box(
        "Return drawer %d finger recess" % (drawer_index + 1),
        (return_x0 - thickness - 0.001, return_center_y, z + return_drawer_height / 2 - 0.025),
        (0.006, return_width - 0.08, 0.012),
        shadow,
        collection,
        root,
    )

# The 50 cm mirror is a separate framed panel on the outer face of the return.
mirror_center_x = width + thickness / 2
mirror_center_z = height / 2
add_box(
    "Mirror section backing",
    (mirror_center_x, return_center_y, mirror_center_z),
    (thickness, MIRROR_WIDTH_M, height),
    white,
    collection,
    root,
)
add_box(
    "Mirror section reflective face",
    (width + thickness + 0.003, return_center_y, mirror_center_z),
    (0.006, MIRROR_WIDTH_M - 0.05, height - 0.06),
    mirror,
    collection,
    root,
)

root["component"] = "Movable L-shaped wardrobe"
root["main_run_width_m"] = MAIN_RUN_WIDTH_M
root["nominal_bay_width_m"] = NOMINAL_BAY_WIDTH_M
root["bay_count"] = BAY_COUNT
root["shelf_depth_m"] = SHELF_DEPTH_M
root["return_length_m"] = RETURN_LENGTH_M
root["mirror_width_m"] = MIRROR_WIDTH_M
root["overall_height_m"] = height
root["panel_thickness_estimate_m"] = thickness
root["dimensions_note"] = (
    "Main run is 1.50 m overall with three nominal 0.50 m bays; "
    "the 0.35 m shelf depth, 0.60 m return, and 0.50 m mirror width are user-provided. "
    "Height (2.10 m) and panel thickness (0.018 m) are provisional estimates."
)
collection["source_script"] = "blender/wardrobe_component.py"
collection["placement_note"] = (
    "Placed beside the apartment model when present, otherwise at the origin. "
    "Move the root empty to reposition."
)

# Keep the root easy to select and move as one unit in the Outliner or viewport.
bpy.ops.object.select_all(action="DESELECT")
root.select_set(True)
bpy.context.view_layer.objects.active = root

print(
    "Wardrobe component built:",
    "3 bays x 50 cm nominal;",
    "35 cm shelf depth;",
    "60 cm return;",
    "50 cm mirror;",
    "provisional height",
    height,
    "m; added to the current Blender scene.",
)

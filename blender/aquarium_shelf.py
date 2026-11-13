"""Build a provisional, editable aquarium and shelf asset in Blender."""

import bpy


COLLECTION_NAME = "Aquarium + Shelf - 95x45x95cm"
WIDTH_M = 0.95
DEPTH_M = 0.45
TOTAL_HEIGHT_M = 0.95

# The total height is user-provided; the split is provisional and easy to revise.
STAND_HEIGHT_M = 0.40
TANK_HEIGHT_M = TOTAL_HEIGHT_M - STAND_HEIGHT_M
WOOD_THICKNESS_M = 0.018
DECK_THICKNESS_M = 0.024
GLASS_THICKNESS_M = 0.008
WATER_HEIGHT_M = 0.44


def make_material(name, color, roughness=0.5, transmission=0.0, alpha=1.0):
    material = bpy.data.materials.get(name)
    if material is None:
        material = bpy.data.materials.new(name)
    material.diffuse_color = (*color[:3], alpha)
    material.roughness = roughness
    material.use_nodes = True
    shader = material.node_tree.nodes.get("Principled BSDF")
    shader.inputs["Base Color"].default_value = (*color[:3], alpha)
    shader.inputs["Roughness"].default_value = roughness
    shader.inputs["Alpha"].default_value = alpha
    shader.inputs["Transmission Weight"].default_value = transmission
    if alpha < 1.0:
        material.surface_render_method = "DITHERED"
    return material


def add_box(name, location, dimensions, material, collection, parent):
    dx, dy, dz = dimensions
    vertices = [
        (-dx / 2, -dy / 2, -dz / 2),
        (dx / 2, -dy / 2, -dz / 2),
        (dx / 2, dy / 2, -dz / 2),
        (-dx / 2, dy / 2, -dz / 2),
        (-dx / 2, -dy / 2, dz / 2),
        (dx / 2, -dy / 2, dz / 2),
        (dx / 2, dy / 2, dz / 2),
        (-dx / 2, dy / 2, dz / 2),
    ]
    faces = [
        (0, 3, 2, 1),
        (4, 5, 6, 7),
        (0, 1, 5, 4),
        (1, 2, 6, 5),
        (2, 3, 7, 6),
        (3, 0, 4, 7),
    ]
    mesh = bpy.data.meshes.new(name + " Mesh")
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    collection.objects.link(obj)
    obj.location = location
    obj.parent = parent
    obj.data.materials.append(material)
    return obj


def remove_existing_asset():
    old_collection = bpy.data.collections.get(COLLECTION_NAME)
    if old_collection is None:
        return
    for obj in list(old_collection.all_objects):
        bpy.data.objects.remove(obj, do_unlink=True)
    for collection in list(old_collection.children_recursive):
        bpy.data.collections.remove(collection, do_unlink=True)
    bpy.data.collections.remove(old_collection, do_unlink=True)


def build_aquarium_shelf():
    remove_existing_asset()
    scene = bpy.context.scene

    root_collection = bpy.data.collections.new(COLLECTION_NAME)
    furniture_collection = bpy.data.collections.get("Furniture")
    if furniture_collection is None:
        scene.collection.children.link(root_collection)
    else:
        furniture_collection.children.link(root_collection)
    stand_collection = bpy.data.collections.new("Shelf Stand")
    tank_collection = bpy.data.collections.new("Aquarium Tank")
    root_collection.children.link(stand_collection)
    root_collection.children.link(tank_collection)

    root = bpy.data.objects.new("Aquarium + Shelf (95 x 45 x 95 cm)", None)
    root_collection.objects.link(root)
    root.empty_display_type = "CUBE"
    root.empty_display_size = 0.12
    root["overall_width_m"] = WIDTH_M
    root["overall_depth_m"] = DEPTH_M
    root["overall_height_m"] = TOTAL_HEIGHT_M
    root["tank_height_m"] = TANK_HEIGHT_M
    root["stand_height_m"] = STAND_HEIGHT_M
    root["dimension_basis"] = (
        "Overall width, depth and height are user-provided. The 40 cm stand / "
        "55 cm tank split and all component thicknesses are provisional."
    )

    wood = make_material("Aquarium stand - light neutral wood", (0.48, 0.34, 0.22), 0.65)
    glass = make_material(
        "Aquarium - clear glass",
        (0.76, 0.91, 0.94),
        roughness=0.08,
        transmission=0.9,
        alpha=0.16,
    )
    water = make_material(
        "Aquarium - water",
        (0.18, 0.53, 0.62),
        roughness=0.12,
        transmission=0.35,
        alpha=0.72,
    )

    # Open storage stand with a top, bottom and intermediate shelf.
    side_x = WIDTH_M / 2 - WOOD_THICKNESS_M / 2
    add_box(
        "Stand - left side",
        (-side_x, 0, STAND_HEIGHT_M / 2),
        (WOOD_THICKNESS_M, DEPTH_M, STAND_HEIGHT_M),
        wood,
        stand_collection,
        root,
    )
    add_box(
        "Stand - right side",
        (side_x, 0, STAND_HEIGHT_M / 2),
        (WOOD_THICKNESS_M, DEPTH_M, STAND_HEIGHT_M),
        wood,
        stand_collection,
        root,
    )
    shelf_width = WIDTH_M - 2 * WOOD_THICKNESS_M
    add_box(
        "Stand - top support",
        (0, 0, STAND_HEIGHT_M - DECK_THICKNESS_M / 2),
        (WIDTH_M, DEPTH_M, DECK_THICKNESS_M),
        wood,
        stand_collection,
        root,
    )
    add_box(
        "Stand - bottom shelf",
        (0, 0, WOOD_THICKNESS_M / 2),
        (shelf_width, DEPTH_M, WOOD_THICKNESS_M),
        wood,
        stand_collection,
        root,
    )
    add_box(
        "Stand - middle shelf",
        (0, 0, STAND_HEIGHT_M / 2),
        (shelf_width, DEPTH_M, WOOD_THICKNESS_M),
        wood,
        stand_collection,
        root,
    )

    # Glass base and four separate walls keep the tank independently editable.
    tank_bottom = STAND_HEIGHT_M
    glass_bottom = tank_bottom + GLASS_THICKNESS_M / 2
    wall_height = TANK_HEIGHT_M - GLASS_THICKNESS_M
    wall_center_z = tank_bottom + GLASS_THICKNESS_M + wall_height / 2
    inner_width = WIDTH_M - 2 * GLASS_THICKNESS_M
    inner_depth = DEPTH_M - 2 * GLASS_THICKNESS_M
    add_box(
        "Tank - glass base",
        (0, 0, glass_bottom),
        (WIDTH_M, DEPTH_M, GLASS_THICKNESS_M),
        glass,
        tank_collection,
        root,
    )
    for side, y in (
        ("front", -DEPTH_M / 2 + GLASS_THICKNESS_M / 2),
        ("back", DEPTH_M / 2 - GLASS_THICKNESS_M / 2),
    ):
        add_box(
            "Tank - " + side + " glass",
            (0, y, wall_center_z),
            (inner_width, GLASS_THICKNESS_M, wall_height),
            glass,
            tank_collection,
            root,
        )
    for side, x in (
        ("left", -WIDTH_M / 2 + GLASS_THICKNESS_M / 2),
        ("right", WIDTH_M / 2 - GLASS_THICKNESS_M / 2),
    ):
        add_box(
            "Tank - " + side + " glass",
            (x, 0, wall_center_z),
            (GLASS_THICKNESS_M, inner_depth, wall_height),
            glass,
            tank_collection,
            root,
        )

    add_box(
        "Tank - water volume (provisional)",
        (0, 0, tank_bottom + GLASS_THICKNESS_M + WATER_HEIGHT_M / 2),
        (inner_width - GLASS_THICKNESS_M, inner_depth - GLASS_THICKNESS_M, WATER_HEIGHT_M),
        water,
        tank_collection,
        root,
    )
    return root_collection


def export_aquarium_asset(filepath):
    collection = bpy.data.collections.get(COLLECTION_NAME)
    if collection is None:
        raise RuntimeError("Build the aquarium asset before exporting it.")
    previous_selection = list(bpy.context.selected_objects)
    previous_active = bpy.context.view_layer.objects.active
    for obj in previous_selection:
        obj.select_set(False)
    for obj in collection.all_objects:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = bpy.data.objects[
        "Aquarium + Shelf (95 x 45 x 95 cm)"
    ]
    bpy.ops.export_scene.gltf(
        filepath=filepath,
        export_format="GLB",
        use_selection=True,
    )
    for obj in bpy.context.selected_objects:
        obj.select_set(False)
    for obj in previous_selection:
        if obj.name in bpy.context.view_layer.objects:
            obj.select_set(True)
    if previous_active and previous_active.name in bpy.context.view_layer.objects:
        bpy.context.view_layer.objects.active = previous_active


build_aquarium_shelf()

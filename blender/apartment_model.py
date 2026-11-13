"""Build a provisional, editable apartment shell from the supplied plan."""

import bpy
import math


COLLECTION_NAME = "Apartment Model - Provisional"
FURNITURE_COMPONENT_COLLECTIONS = (
    "Aquarium + Shelf - 95x45x95cm",
    "Wardrobe Component",
)
AREA_TARGET_M2 = 53.0
WALL_HEIGHT_M = 2.40
EXTERIOR_WALL_M = 0.12
INTERIOR_WALL_M = 0.10
BED_MATTRESS_WIDTH_M = 1.60
BED_MATTRESS_LENGTH_M = 2.00
BED_MATTRESS_THICKNESS_M = 0.22
BED_SLEEPING_SURFACE_HEIGHT_M = 0.60
BED_FRAME_HEIGHT_M = 0.20
BED_SUPPORT_WIDTH_M = 0.08
BED_VERTICAL_OFFSET_M = BED_SLEEPING_SURFACE_HEIGHT_M - (0.35 + BED_MATTRESS_THICKNESS_M / 2)

# These traced image coordinates preserve the plan's topology only; the drawing
# explicitly says it is not to scale.
LEFT, RIGHT = 142.0, 1641.0
TOP, STEP_Y, STEP_X, BOTTOM = 169.0, 790.0, 807.0, 1030.0
PLAN_OUTLINE = [
    (LEFT, TOP),
    (RIGHT, TOP),
    (RIGHT, STEP_Y),
    (STEP_X, STEP_Y),
    (STEP_X, BOTTOM),
    (LEFT, BOTTOM),
]
HALL_STORAGE_DOOR_START_Y, HALL_STORAGE_DOOR_END_Y = 637.0, 747.0


def polygon_area(points):
    return abs(
        sum(
            points[i][0] * points[(i + 1) % len(points)][1]
            - points[(i + 1) % len(points)][0] * points[i][1]
            for i in range(len(points))
        )
    ) * 0.5


def get_interior_area(scale):
    inset = EXTERIOR_WALL_M / 2.0
    right = (RIGHT - LEFT) * scale
    step_x = (STEP_X - LEFT) * scale
    step_y = (BOTTOM - STEP_Y) * scale
    top = (BOTTOM - TOP) * scale
    inner = [
        (inset, inset),
        (step_x - inset, inset),
        (step_x - inset, step_y + inset),
        (right - inset, step_y + inset),
        (right - inset, top - inset),
        (inset, top - inset),
    ]
    return polygon_area(inner)


low, high = 0.001, 0.02
for _ in range(80):
    scale = (low + high) * 0.5
    if get_interior_area(scale) < AREA_TARGET_M2:
        low = scale
    else:
        high = scale
PIXEL_TO_M = (low + high) * 0.5


def px_to_x(px):
    return (px - LEFT) * PIXEL_TO_M


def px_to_y(py):
    return (BOTTOM - py) * PIXEL_TO_M


def make_material(name, color, roughness=0.82):
    material = bpy.data.materials.get(name)
    if material is None:
        material = bpy.data.materials.new(name)
    material.diffuse_color = color
    material.roughness = roughness
    principled = material.node_tree.nodes.get("Principled BSDF") if material.node_tree else None
    if principled:
        principled.inputs["Base Color"].default_value = color
        principled.inputs["Roughness"].default_value = roughness
    return material


def link_mesh(name, vertices, faces, material, collection):
    mesh = bpy.data.meshes.new(name + " Mesh")
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    collection.objects.link(obj)
    if material:
        obj.data.materials.append(material)
    return obj


def add_box(name, location, dimensions, material, collection):
    dx, dy, dz = dimensions
    x, y, z = location
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
    faces = [
        (0, 3, 2, 1),
        (4, 5, 6, 7),
        (0, 1, 5, 4),
        (1, 2, 6, 5),
        (2, 3, 7, 6),
        (3, 0, 4, 7),
    ]
    return link_mesh(name, vertices, faces, material, collection)


def add_floor(name, x0, x1, y0, y1, material, collection):
    return add_box(
        name,
        ((x0 + x1) / 2, (y0 + y1) / 2, -0.04),
        (x1 - x0, y1 - y0, 0.08),
        material,
        collection,
    )


def add_box_mosaic(name, boxes, materials, collection):
    vertices = []
    faces = []
    material_indices = []
    cube_faces = (
        (0, 3, 2, 1),
        (4, 5, 6, 7),
        (0, 1, 5, 4),
        (1, 2, 6, 5),
        (2, 3, 7, 6),
        (3, 0, 4, 7),
    )
    for location, dimensions, material_index in boxes:
        x, y, z = location
        dx, dy, dz = dimensions
        offset = len(vertices)
        vertices.extend(
            (
                (x - dx / 2, y - dy / 2, z - dz / 2),
                (x + dx / 2, y - dy / 2, z - dz / 2),
                (x + dx / 2, y + dy / 2, z - dz / 2),
                (x - dx / 2, y + dy / 2, z - dz / 2),
                (x - dx / 2, y - dy / 2, z + dz / 2),
                (x + dx / 2, y - dy / 2, z + dz / 2),
                (x + dx / 2, y + dy / 2, z + dz / 2),
                (x - dx / 2, y + dy / 2, z + dz / 2),
            )
        )
        faces.extend(tuple(offset + index for index in face) for face in cube_faces)
        material_indices.extend([material_index] * len(cube_faces))
    mesh = bpy.data.meshes.new(name + " Mesh")
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    for material in materials:
        mesh.materials.append(material)
    for polygon, material_index in zip(mesh.polygons, material_indices):
        polygon.material_index = material_index
    obj = bpy.data.objects.new(name, mesh)
    collection.objects.link(obj)
    return obj


def add_tiled_wall(
    name,
    axis,
    start,
    end,
    fixed_face,
    direction,
    materials,
    grout_material,
    collection,
    z0=0.0,
    z1=None,
    tile_size=0.30,
    tile_gap=0.004,
):
    backing_thickness, tile_thickness = 0.004, 0.008
    if z1 is None:
        z1 = WALL_HEIGHT_M
    if axis == "V":
        backing_location = (
            fixed_face + direction * backing_thickness / 2,
            (start + end) / 2,
            (z0 + z1) / 2,
        )
        backing_dimensions = (backing_thickness, end - start, z1 - z0)
    elif axis == "H":
        backing_location = (
            (start + end) / 2,
            fixed_face + direction * backing_thickness / 2,
            (z0 + z1) / 2,
        )
        backing_dimensions = (end - start, backing_thickness, z1 - z0)
    else:
        raise ValueError("Bathroom wall axis must be H or V")
    add_box(name + " grout backing", backing_location, backing_dimensions, grout_material, collection)
    boxes = []
    first_column = math.floor(start / tile_size)
    last_column = math.ceil(end / tile_size)
    first_row = math.floor(z0 / tile_size)
    last_row = math.ceil(z1 / tile_size)
    for column in range(first_column, last_column):
        tile_start = max(start, column * tile_size) + tile_gap / 2
        tile_end = min(end, (column + 1) * tile_size) - tile_gap / 2
        if tile_end <= tile_start:
            continue
        for row in range(first_row, last_row):
            tile_bottom = max(z0, row * tile_size) + tile_gap / 2
            tile_top = min(z1, (row + 1) * tile_size) - tile_gap / 2
            if tile_top <= tile_bottom:
                continue
            offset = direction * (backing_thickness + tile_thickness / 2)
            center_z = (tile_bottom + tile_top) / 2
            if axis == "V":
                location = (fixed_face + offset, (tile_start + tile_end) / 2, center_z)
                dimensions = (tile_thickness, tile_end - tile_start, tile_top - tile_bottom)
            else:
                location = ((tile_start + tile_end) / 2, fixed_face + offset, center_z)
                dimensions = (tile_end - tile_start, tile_thickness, tile_top - tile_bottom)
            boxes.append((location, dimensions, (column * 3 + row * 5) % len(materials)))
    add_box_mosaic(name + " tiles", boxes, materials, collection)


def add_wall_finish_panel(name, axis, start, end, fixed_face, direction, z0, z1, material, collection):
    thickness = 0.003
    if axis == "V":
        location = (fixed_face + direction * thickness / 2, (start + end) / 2, (z0 + z1) / 2)
        dimensions = (thickness, end - start, z1 - z0)
    elif axis == "H":
        location = ((start + end) / 2, fixed_face + direction * thickness / 2, (z0 + z1) / 2)
        dimensions = (end - start, thickness, z1 - z0)
    else:
        raise ValueError("Wall finish panel axis must be H or V")
    return add_box(name, location, dimensions, material, collection)


def add_wall_piece(axis, a, b, fixed, thickness, z0, z1, material, name, collection):
    if b <= a or z1 <= z0:
        return
    if axis == "H":
        x0, x1 = px_to_x(a), px_to_x(b)
        location = ((x0 + x1) / 2, px_to_y(fixed), (z0 + z1) / 2)
        dimensions = (x1 - x0, thickness, z1 - z0)
    else:
        y0, y1 = px_to_y(a), px_to_y(b)
        location = (px_to_x(fixed), (y0 + y1) / 2, (z0 + z1) / 2)
        dimensions = (thickness, y0 - y1, z1 - z0)
    add_box(name, location, dimensions, material, collection)


def add_window(axis, a, b, fixed, thickness, sill, head, frame, glass, name, collection):
    trim = 0.04
    inset_px = trim / (2.0 * PIXEL_TO_M)
    if axis == "H":
        middle_x = (px_to_x(a) + px_to_x(b)) / 2
        location = (middle_x, px_to_y(fixed), (sill + head) / 2)
        dimensions = (px_to_x(b) - px_to_x(a) - trim, 0.018, head - sill - trim)
    else:
        middle_y = (px_to_y(a) + px_to_y(b)) / 2
        location = (px_to_x(fixed), middle_y, (sill + head) / 2)
        dimensions = (0.018, px_to_y(a) - px_to_y(b) - trim, head - sill - trim)
    add_box(name + " Glass", location, dimensions, glass, collection)
    add_wall_piece(axis, a, a + inset_px, fixed, thickness, sill, head, frame, name + " Jamb A", collection)
    add_wall_piece(axis, b - inset_px, b, fixed, thickness, sill, head, frame, name + " Jamb B", collection)
    add_wall_piece(axis, a, b, fixed, thickness, sill - trim / 2, sill + trim / 2, frame, name + " Sill", collection)
    add_wall_piece(axis, a, b, fixed, thickness, head - trim / 2, head + trim / 2, frame, name + " Head", collection)


def add_wall(axis, start, end, fixed, thickness, name, collection, wall_material, frame_material, glass_material, openings=()):
    cursor = start
    for opening_start, opening_end, opening_type in sorted(openings):
        add_wall_piece(
            axis,
            cursor,
            opening_start,
            fixed,
            thickness,
            0.0,
            WALL_HEIGHT_M,
            wall_material,
            name + " Wall",
            collection,
        )
        if opening_type == "window":
            sill, head = 0.78, 2.02
            add_wall_piece(axis, opening_start, opening_end, fixed, thickness, 0.0, sill, wall_material, name + " Window Sill Wall", collection)
            add_wall_piece(axis, opening_start, opening_end, fixed, thickness, head, WALL_HEIGHT_M, wall_material, name + " Window Header Wall", collection)
            add_window(axis, opening_start, opening_end, fixed, thickness, sill, head, frame_material, glass_material, name + " Window", collection)
        else:
            add_wall_piece(axis, opening_start, opening_end, fixed, thickness, 2.02, WALL_HEIGHT_M, wall_material, name + " Door Header", collection)
        cursor = opening_end
    add_wall_piece(
        axis,
        cursor,
        end,
        fixed,
        thickness,
        0.0,
        WALL_HEIGHT_M,
        wall_material,
        name + " Wall",
        collection,
    )


def add_text(name, body, location, size, material, collection):
    curve = bpy.data.curves.new(name + " Text", "FONT")
    curve.body = body
    curve.size = size
    curve.align_x = "CENTER"
    curve.align_y = "CENTER"
    obj = bpy.data.objects.new(name, curve)
    obj.location = location
    curve.materials.append(material)
    collection.objects.link(obj)
    return obj


def add_floor_arrow(name, start, end, width, material, collection):
    dx, dy = end[0] - start[0], end[1] - start[1]
    length = math.hypot(dx, dy)
    ux, uy = dx / length, dy / length
    px, py = -uy, ux
    head_length = min(length * 0.42, 0.16)
    neck = (end[0] - ux * head_length, end[1] - uy * head_length)
    shaft_half_width = width / 2
    head_half_width = width * 1.8
    points = [
        (start[0] + px * shaft_half_width, start[1] + py * shaft_half_width),
        (neck[0] + px * shaft_half_width, neck[1] + py * shaft_half_width),
        (neck[0] + px * head_half_width, neck[1] + py * head_half_width),
        end,
        (neck[0] - px * head_half_width, neck[1] - py * head_half_width),
        (neck[0] - px * shaft_half_width, neck[1] - py * shaft_half_width),
        (start[0] - px * shaft_half_width, start[1] - py * shaft_half_width),
    ]
    return link_mesh(
        name,
        [(x, y, 0.022) for x, y in points],
        [tuple(range(len(points)))],
        material,
        collection,
    )


def add_beveled_box(name, location, dimensions, material, collection, bevel_width):
    obj = add_box(name, location, dimensions, material, collection)
    bevel = obj.modifiers.new(name + " Soft Edges", "BEVEL")
    bevel.width = bevel_width
    bevel.segments = 3
    return obj


scene = bpy.context.scene
old_collection = bpy.data.collections.get(COLLECTION_NAME)


def remove_collection_tree(collection):
    for child in list(collection.children):
        remove_collection_tree(child)
    for old_obj in list(collection.objects):
        bpy.data.objects.remove(old_obj, do_unlink=True)
    bpy.data.collections.remove(collection)


if old_collection:
    component_collections = [
        bpy.data.collections.get(name)
        for name in FURNITURE_COMPONENT_COLLECTIONS
    ]
    for component_collection in component_collections:
        if component_collection is None:
            continue
        for parent_collection in bpy.data.collections:
            if parent_collection.children.get(component_collection.name) is component_collection:
                parent_collection.children.unlink(component_collection)
        if scene.collection.children.get(component_collection.name) is component_collection:
            scene.collection.children.unlink(component_collection)
        scene.collection.children.link(component_collection)
    remove_collection_tree(old_collection)

root = bpy.data.collections.new(COLLECTION_NAME)
scene.collection.children.link(root)
collections = {}
for name in (
    "Floors",
    "Wall Finishes",
    "Shell",
    "Windows",
    "Doors",
    "Built-ins",
    "Fixtures",
    "Furniture",
    "Annotations",
):
    child = bpy.data.collections.new(name)
    root.children.link(child)
    collections[name] = child

for component_name in FURNITURE_COMPONENT_COLLECTIONS:
    component_collection = bpy.data.collections.get(component_name)
    if component_collection is None:
        continue
    for parent_collection in bpy.data.collections:
        if parent_collection.children.get(component_collection.name) is component_collection:
            parent_collection.children.unlink(component_collection)
    if scene.collection.children.get(component_collection.name) is component_collection:
        scene.collection.children.unlink(component_collection)
    collections["Furniture"].children.link(component_collection)

floor_mat = make_material("Apartment - oak floor joints", (0.47, 0.35, 0.24, 1.0))
wall_mat = make_material("Apartment - warm white walls", (0.84, 0.82, 0.76, 1.0))
kitchen_wall_mat = make_material("Apartment - warm greige kitchen walls", (0.52, 0.46, 0.39, 1.0))
frame_mat = make_material("Apartment - window frames", (0.16, 0.20, 0.22, 1.0))
glass_mat = make_material("Apartment - provisional glazing", (0.24, 0.52, 0.66, 1.0), 0.25)
wood_mat = make_material("Apartment - built-in wood", (0.47, 0.32, 0.20, 1.0))
fixture_mat = make_material("Apartment - fixture blockouts", (0.88, 0.89, 0.86, 1.0))
appliance_mat = make_material("Apartment - appliance blockouts", (0.48, 0.53, 0.56, 1.0))
appliance_marking_mat = make_material("Apartment - appliance markings", (0.10, 0.10, 0.09, 1.0))
metal_mat = make_material("Apartment - kitchen stainless", (0.62, 0.65, 0.66, 1.0), 0.35)
cooktop_mat = make_material("Apartment - cooktop glass", (0.08, 0.09, 0.10, 1.0), 0.28)

half_wall = EXTERIOR_WALL_M / 2
right_x = px_to_x(RIGHT)
notch_x = px_to_x(STEP_X)
step_y = px_to_y(STEP_Y)
top_y = px_to_y(TOP)
bottom_y = px_to_y(BOTTOM)
left_inside = half_wall
right_inside = right_x - half_wall
notch_inside = notch_x - half_wall
top_inside = top_y - half_wall
step_inside = step_y + half_wall
bottom_inside = half_wall

add_floor("Main apartment floor", left_inside, right_inside, step_inside, top_inside, floor_mat, collections["Floors"])
add_floor("Kitchen and entry floor", left_inside, notch_inside, bottom_inside, step_inside, floor_mat, collections["Floors"])

wood_floor_materials = [
    make_material("Apartment - light oak plank", (0.70, 0.56, 0.40, 1.0), 0.78),
    make_material("Apartment - natural oak plank", (0.66, 0.51, 0.36, 1.0), 0.78),
    make_material("Apartment - pale oak plank", (0.73, 0.59, 0.43, 1.0), 0.78),
]
tile_materials = [
    make_material("Bathroom - light gray floor tile", (0.67, 0.68, 0.66, 1.0), 0.74),
    make_material("Bathroom - gray floor tile variation", (0.63, 0.65, 0.64, 1.0), 0.74),
    make_material("Bathroom - pale floor tile variation", (0.71, 0.71, 0.69, 1.0), 0.74),
]
grout_mat = make_material("Bathroom - floor grout", (0.43, 0.45, 0.44, 1.0), 0.9)
wall_tile_materials = [
    make_material("Bathroom - warm white wall tile", (0.83, 0.81, 0.77, 1.0), 0.68),
    make_material("Bathroom - ivory wall tile variation", (0.85, 0.83, 0.79, 1.0), 0.68),
    make_material("Bathroom - pale wall tile variation", (0.80, 0.79, 0.76, 1.0), 0.68),
]
wall_grout_mat = make_material("Bathroom - wall tile grout", (0.58, 0.57, 0.54, 1.0), 0.9)
kitchen_backsplash_materials = [
    make_material("Kitchen - warm gray beige backsplash tile", (0.58, 0.52, 0.45, 1.0), 0.62),
    make_material("Kitchen - taupe backsplash tile variation", (0.54, 0.48, 0.42, 1.0), 0.62),
    make_material("Kitchen - pale backsplash tile variation", (0.62, 0.56, 0.49, 1.0), 0.62),
]
kitchen_backsplash_grout = make_material("Kitchen - backsplash grout", (0.39, 0.36, 0.32, 1.0), 0.9)
bath_x0 = px_to_x(747) + INTERIOR_WALL_M / 2
bath_x1 = px_to_x(937) - INTERIOR_WALL_M / 2
bath_y_south = px_to_y(622) + INTERIOR_WALL_M / 2
bath_floor_south = px_to_y(622)
bath_y_north = px_to_y(199) - INTERIOR_WALL_M / 2
wood_regions = (
    (left_inside, right_inside, step_inside, bath_floor_south),
    (left_inside, right_inside, bath_y_north, top_inside),
    (left_inside, bath_x0, bath_floor_south, bath_y_north),
    (bath_x1, right_inside, bath_floor_south, bath_y_north),
    (left_inside, notch_inside, bottom_inside, step_inside),
)
plank_width, plank_length, plank_gap = 0.14, 1.20, 0.003
plank_bottom, plank_thickness = 0.001, 0.011
wood_boxes = []
for region_x0, region_x1, region_y0, region_y1 in wood_regions:
    first_column = math.floor((region_x0 - left_inside) / plank_width)
    last_column = math.ceil((region_x1 - left_inside) / plank_width)
    for column in range(first_column, last_column):
        cell_x0 = left_inside + column * plank_width
        board_x0 = max(region_x0, cell_x0) + plank_gap / 2
        board_x1 = min(region_x1, cell_x0 + plank_width) - plank_gap / 2
        stagger = 0.0 if column % 2 == 0 else plank_length / 2
        first_row = math.floor((region_y0 - bottom_inside - stagger) / plank_length)
        last_row = math.ceil((region_y1 - bottom_inside - stagger) / plank_length)
        for row in range(first_row, last_row):
            cell_y0 = bottom_inside + stagger + row * plank_length
            board_y0 = max(region_y0, cell_y0) + plank_gap / 2
            board_y1 = min(region_y1, cell_y0 + plank_length) - plank_gap / 2
            if board_x1 > board_x0 and board_y1 > board_y0:
                wood_boxes.append(
                    (
                        (
                            (board_x0 + board_x1) / 2,
                            (board_y0 + board_y1) / 2,
                            plank_bottom + plank_thickness / 2,
                        ),
                        (board_x1 - board_x0, board_y1 - board_y0, plank_thickness),
                        (column * 5 + row * 3) % len(wood_floor_materials),
                    )
                )
add_box_mosaic("Wood plank floors", wood_boxes, wood_floor_materials, collections["Floors"])

tile_size, tile_gap = 0.30, 0.004
add_box(
    "Bathroom tile grout bed",
    ((bath_x0 + bath_x1) / 2, (bath_floor_south + bath_y_north) / 2, 0.001),
    (bath_x1 - bath_x0, bath_y_north - bath_floor_south, 0.002),
    grout_mat,
    collections["Floors"],
)
tile_boxes = []
column = 0
tile_x0 = bath_x0
while tile_x0 < bath_x1:
    tile_x1 = min(tile_x0 + tile_size, bath_x1)
    cell_y0 = bath_floor_south
    row = 0
    while cell_y0 < bath_y_north:
        cell_y1 = min(cell_y0 + tile_size, bath_y_north)
        tile_boxes.append(
            (
                ((tile_x0 + tile_x1) / 2, (cell_y0 + cell_y1) / 2, 0.007),
                (tile_x1 - tile_x0 - tile_gap, cell_y1 - cell_y0 - tile_gap, 0.010),
                (column * 2 + row) % len(tile_materials),
            )
        )
        cell_y0 += tile_size
        row += 1
    tile_x0 += tile_size
    column += 1
add_box_mosaic("Bathroom floor tiles", tile_boxes, tile_materials, collections["Floors"])

add_tiled_wall(
    "Bathroom west tiled wall",
    "V",
    bath_y_south,
    px_to_y(TOP) - EXTERIOR_WALL_M / 2,
    bath_x0,
    1,
    wall_tile_materials,
    wall_grout_mat,
    collections["Wall Finishes"],
)
add_tiled_wall(
    "Bathroom east tiled wall",
    "V",
    bath_y_south,
    px_to_y(TOP) - EXTERIOR_WALL_M / 2,
    bath_x1,
    -1,
    wall_tile_materials,
    wall_grout_mat,
    collections["Wall Finishes"],
)
bath_north_face = px_to_y(TOP) - EXTERIOR_WALL_M / 2
add_tiled_wall(
    "Bathroom north tiled wall",
    "H",
    px_to_x(747),
    px_to_x(937),
    bath_north_face,
    -1,
    wall_tile_materials,
    wall_grout_mat,
    collections["Wall Finishes"],
)
for segment_start, segment_end, name in (
    (px_to_x(747), px_to_x(805), "Bathroom threshold west tile"),
    (px_to_x(907), px_to_x(937), "Bathroom threshold east tile"),
):
    add_tiled_wall(
        name,
        "H",
        segment_start,
        segment_end,
        bath_y_south,
        1,
        wall_tile_materials,
        wall_grout_mat,
        collections["Wall Finishes"],
    )

# Exterior walls: window and entrance dimensions are provisional interpretations
# of the drawn symbols, not verified construction measurements.
add_wall("H", LEFT, RIGHT, TOP, EXTERIOR_WALL_M, "North facade", collections["Shell"], wall_mat, frame_mat, glass_mat)
add_wall("V", TOP, STEP_Y, RIGHT, EXTERIOR_WALL_M, "East facade", collections["Shell"], wall_mat, frame_mat, glass_mat, [(289, 664, "window")])
add_wall("H", STEP_X, RIGHT, STEP_Y, EXTERIOR_WALL_M, "Living room facade", collections["Shell"], wall_mat, frame_mat, glass_mat)
add_wall("V", STEP_Y, BOTTOM, STEP_X, EXTERIOR_WALL_M, "Entry return", collections["Shell"], wall_mat, frame_mat, glass_mat)
add_wall("H", LEFT, STEP_X, BOTTOM, EXTERIOR_WALL_M, "Entrance facade", collections["Shell"], wall_mat, frame_mat, glass_mat, [(662, 778, "door")])
add_wall("V", TOP, BOTTOM, LEFT, EXTERIOR_WALL_M, "West facade", collections["Shell"], wall_mat, frame_mat, glass_mat, [(347, 539, "window"), (768, 956, "window")])

# Internal partitions and open passage locations follow the plan's visible breaks.
add_wall("V", 169, 622, 747, INTERIOR_WALL_M, "Bedroom bathroom partition", collections["Shell"], wall_mat, frame_mat, glass_mat)
add_wall("V", 169, 622, 937, INTERIOR_WALL_M, "Bathroom living partition", collections["Shell"], wall_mat, frame_mat, glass_mat)
west_wall_inner_face_px = LEFT + EXTERIOR_WALL_M / (2 * PIXEL_TO_M)
add_wall("H", west_wall_inner_face_px, 747, 622, INTERIOR_WALL_M, "Bedroom hall partition", collections["Shell"], wall_mat, frame_mat, glass_mat, [(654, 747, "door")])
add_wall("H", 747, 805, 622, INTERIOR_WALL_M, "Bathroom threshold west", collections["Shell"], wall_mat, frame_mat, glass_mat)
add_wall("H", 907, 937, 622, INTERIOR_WALL_M, "Bathroom threshold east", collections["Shell"], wall_mat, frame_mat, glass_mat)
add_wall("H", west_wall_inner_face_px, 637, 637, INTERIOR_WALL_M, "Kitchen hall north partition", collections["Shell"], wall_mat, frame_mat, glass_mat)
add_wall("V", 637, 747, 497, INTERIOR_WALL_M, "Kitchen hall west partition", collections["Shell"], wall_mat, frame_mat, glass_mat)
add_wall("H", 497, 637, 747, INTERIOR_WALL_M, "Hall storage south return", collections["Shell"], wall_mat, frame_mat, glass_mat)
add_wall(
    "V",
    637,
    747,
    637,
    INTERIOR_WALL_M,
    "Hall storage east wall",
    collections["Shell"],
    wall_mat,
    frame_mat,
    glass_mat,
    [(HALL_STORAGE_DOOR_START_Y, HALL_STORAGE_DOOR_END_Y, "door")],
)
add_wall("V", 747, 839, 637, INTERIOR_WALL_M, "Hall storage east return", collections["Shell"], wall_mat, frame_mat, glass_mat)
add_wall("V", 926, 1016, 637, INTERIOR_WALL_M, "Kitchen refrigerator east return", collections["Shell"], wall_mat, frame_mat, glass_mat)

# Floor labels show provisional clear lengths of the four living-room boundary walls.
living_west_face = px_to_x(937) + INTERIOR_WALL_M / 2
living_east_face = right_inside
living_north_face = top_inside
living_south_face = step_inside
living_mid_x = (living_west_face + living_east_face) / 2
living_mid_y = (living_north_face + living_south_face) / 2
living_west_mid_y = (px_to_y(TOP) + px_to_y(622)) / 2
living_wall_lengths = {
    "north": living_east_face - living_west_face,
    "east": living_north_face - living_south_face,
    "south": living_east_face - (px_to_x(STEP_X) + INTERIOR_WALL_M / 2),
    "west partition": px_to_y(TOP) - px_to_y(622) - (EXTERIOR_WALL_M + INTERIOR_WALL_M) / 2,
}
measurement_mat = make_material("Apartment - measurement annotations", (0.03, 0.03, 0.03, 1.0), 0.7)
living_wall_annotations = (
    (
        "North",
        living_wall_lengths["north"],
        (living_mid_x, living_north_face - 0.62, 0.02),
        (living_mid_x, living_north_face - 0.36),
        (living_mid_x, living_north_face - 0.03),
    ),
    (
        "East",
        living_wall_lengths["east"],
        (living_east_face - 0.68, living_mid_y, 0.02),
        (living_east_face - 0.36, living_mid_y),
        (living_east_face - 0.03, living_mid_y),
    ),
    (
        "South",
        living_wall_lengths["south"],
        (living_mid_x, living_south_face + 0.65, 0.02),
        (living_mid_x, living_south_face + 0.36),
        (living_mid_x, living_south_face + 0.03),
    ),
    (
        "West partition",
        living_wall_lengths["west partition"],
        (living_west_face + 0.68, living_west_mid_y, 0.02),
        (living_west_face + 0.36, living_west_mid_y),
        (living_west_face + 0.03, living_west_mid_y),
    ),
)
for wall_name, length, text_location, arrow_start, arrow_end in living_wall_annotations:
    add_text(
        "Living room " + wall_name + " wall estimate",
        "~" + format(length, ".1f") + " m",
        text_location,
        0.17,
        measurement_mat,
        collections["Annotations"],
    )
    add_floor_arrow(
        "Living room " + wall_name + " wall arrow",
        arrow_start,
        arrow_end,
        0.045,
        measurement_mat,
        collections["Annotations"],
    )

# The user uses the living room as a bedroom; keep this bed movable as one parent object.
bed_center_x = living_mid_x
bed_center_y = living_mid_y
bed_collection = bpy.data.collections.new("Movable Bed")
collections["Furniture"].children.link(bed_collection)
bed_frame_mat = make_material("Bedroom - walnut bed frame", (0.32, 0.22, 0.15, 1.0))
mattress_mat = make_material("Bedroom - ivory mattress", (0.88, 0.86, 0.81, 1.0))
duvet_mat = make_material("Bedroom - muted sage duvet", (0.36, 0.49, 0.45, 1.0))
pillow_mat = make_material("Bedroom - ivory pillows", (0.96, 0.94, 0.89, 1.0))
bed_parts = [
    add_beveled_box(
        "Movable Bed - Frame",
        (bed_center_x, bed_center_y, 0.14 + BED_VERTICAL_OFFSET_M),
        (BED_MATTRESS_WIDTH_M + 0.12, BED_MATTRESS_LENGTH_M + 0.16, BED_FRAME_HEIGHT_M),
        bed_frame_mat,
        bed_collection,
        0.035,
    ),
    add_beveled_box(
        "Movable Bed - Mattress 160 x 200 cm",
        (bed_center_x, bed_center_y, 0.35 + BED_VERTICAL_OFFSET_M),
        (BED_MATTRESS_WIDTH_M, BED_MATTRESS_LENGTH_M, BED_MATTRESS_THICKNESS_M),
        mattress_mat,
        bed_collection,
        0.045,
    ),
    add_beveled_box(
        "Movable Bed - Duvet",
        (bed_center_x, bed_center_y - 0.31, 0.50 + BED_VERTICAL_OFFSET_M),
        (BED_MATTRESS_WIDTH_M - 0.06, BED_MATTRESS_LENGTH_M * 0.67, 0.075),
        duvet_mat,
        bed_collection,
        0.035,
    ),
    add_beveled_box(
        "Movable Bed - Headboard",
        (bed_center_x, bed_center_y + BED_MATTRESS_LENGTH_M / 2 + 0.12, 0.67 + BED_VERTICAL_OFFSET_M),
        (BED_MATTRESS_WIDTH_M + 0.20, 0.12, 0.94),
        bed_frame_mat,
        bed_collection,
        0.035,
    ),
]
for index, x_offset in enumerate((-0.38, 0.38), start=1):
    bed_parts.append(
        add_beveled_box(
            "Movable Bed - Pillow " + str(index),
            (bed_center_x + x_offset, bed_center_y + 0.72, 0.52 + BED_VERTICAL_OFFSET_M),
            (0.72, 0.44, 0.15),
            pillow_mat,
            bed_collection,
            0.065,
        )
    )

bed_support_height = 0.14 + BED_VERTICAL_OFFSET_M - BED_FRAME_HEIGHT_M / 2
for x_offset in (
    -(BED_MATTRESS_WIDTH_M / 2 + 0.06 - BED_SUPPORT_WIDTH_M / 2),
    BED_MATTRESS_WIDTH_M / 2 + 0.06 - BED_SUPPORT_WIDTH_M / 2,
):
    for y_offset in (
        -(BED_MATTRESS_LENGTH_M / 2 + 0.08 - BED_SUPPORT_WIDTH_M / 2),
        BED_MATTRESS_LENGTH_M / 2 + 0.08 - BED_SUPPORT_WIDTH_M / 2,
    ):
        bed_parts.append(
            add_beveled_box(
                "Movable Bed - Support",
                (bed_center_x + x_offset, bed_center_y + y_offset, bed_support_height / 2),
                (BED_SUPPORT_WIDTH_M, BED_SUPPORT_WIDTH_M, bed_support_height),
                bed_frame_mat,
                bed_collection,
                0.01,
            )
        )

bed_root = bpy.data.objects.new("Movable Bed - 160 x 200 cm", None)
bed_collection.objects.link(bed_root)
bed_root.location = (bed_center_x, bed_center_y, 0.0)
bed_root.empty_display_type = "CUBE"
bed_root.empty_display_size = 0.25
bed_root["mattress_width_m"] = BED_MATTRESS_WIDTH_M
bed_root["mattress_length_m"] = BED_MATTRESS_LENGTH_M
bed_root["sleeping_surface_height_m"] = BED_SLEEPING_SURFACE_HEIGHT_M
bed_root["placement"] = "Living room, used as the bedroom at the user's request."
bed_root["how_to_move"] = "Select this parent object in the Movable Bed collection and move it; parts are selection-locked."
for part in bed_parts:
    for vertex in part.data.vertices:
        vertex.co.x -= bed_center_x
        vertex.co.y -= bed_center_y
    part.parent = bed_root
    part.hide_select = True

# Keep the hall storage enclosure empty and align its closed door with the marked wall.
storage_door_width = px_to_y(HALL_STORAGE_DOOR_START_Y) - px_to_y(HALL_STORAGE_DOOR_END_Y)
storage_door_height = 2.02
storage_frame_width = 0.04
storage_wall_x = px_to_x(637)
for side, pixel_y in (("north", HALL_STORAGE_DOOR_START_Y), ("south", HALL_STORAGE_DOOR_END_Y)):
    add_box(
        "Hall storage door " + side + " jamb",
        (storage_wall_x, px_to_y(pixel_y), storage_door_height / 2),
        (INTERIOR_WALL_M, storage_frame_width, storage_door_height),
        wall_mat,
        collections["Doors"],
    )
add_box(
    "Hall storage door head",
    (
        storage_wall_x,
        (px_to_y(HALL_STORAGE_DOOR_START_Y) + px_to_y(HALL_STORAGE_DOOR_END_Y)) / 2,
        storage_door_height - storage_frame_width / 2,
    ),
    (INTERIOR_WALL_M, storage_door_width, storage_frame_width),
    wall_mat,
    collections["Doors"],
)

# Bedroom built-in storage marked G in the drawing; each unit remains separate.
for index, (a, b) in enumerate(((199, 285), (286, 366), (367, 439), (440, 526)), start=1):
    x0, x1 = px_to_x(674), px_to_x(747)
    y0, y1 = px_to_y(b), px_to_y(a)
    add_box(
        "Bedroom built-in G" + str(index),
        ((x0 + x1) / 2, (y0 + y1) / 2, 1.08),
        (x1 - x0, y1 - y0, 2.16),
        wood_mat,
        collections["Built-ins"],
    )

# Keep the kitchen run on its plan position and extend its west end to the interior wall face.
kitchen_wall_face = px_to_y(637) - INTERIOR_WALL_M / 2
kitchen_x0 = px_to_x(LEFT) + EXTERIOR_WALL_M / 2 + 0.02
kitchen_x1 = px_to_x(497)
west_kitchen_face = px_to_x(LEFT) + EXTERIOR_WALL_M / 2
add_wall_finish_panel(
    "Kitchen north wall greige finish",
    "H",
    kitchen_x0,
    kitchen_x1,
    kitchen_wall_face,
    -1,
    0.0,
    WALL_HEIGHT_M,
    kitchen_wall_mat,
    collections["Wall Finishes"],
)
west_window_y0, west_window_y1 = px_to_y(956), px_to_y(768)
for panel_name, panel_y0, panel_y1, panel_z0, panel_z1 in (
    ("Kitchen west wall lower window-side finish", px_to_y(BOTTOM), west_window_y0, 0.0, WALL_HEIGHT_M),
    ("Kitchen west wall upper window-side finish", west_window_y1, px_to_y(637), 0.0, WALL_HEIGHT_M),
    ("Kitchen west wall window sill finish", west_window_y0, west_window_y1, 0.0, 0.78),
    ("Kitchen west wall window header finish", west_window_y0, west_window_y1, 2.02, WALL_HEIGHT_M),
):
    add_wall_finish_panel(
        panel_name,
        "V",
        panel_y0,
        panel_y1,
        west_kitchen_face,
        1,
        panel_z0,
        panel_z1,
        kitchen_wall_mat,
        collections["Wall Finishes"],
    )
add_wall_finish_panel(
    "Kitchen hall partition greige finish",
    "V",
    px_to_y(747),
    px_to_y(637),
    px_to_x(497) - INTERIOR_WALL_M / 2,
    -1,
    0.0,
    WALL_HEIGHT_M,
    kitchen_wall_mat,
    collections["Wall Finishes"],
)
counter_depth = 0.58
counter_front = kitchen_wall_face - counter_depth
kitchen_center_x = (kitchen_x0 + kitchen_x1) / 2
counter_center_y = (kitchen_wall_face + counter_front) / 2
add_box(
    "Kitchen fitted base cabinets",
    (kitchen_center_x, counter_center_y, 0.42),
    (kitchen_x1 - kitchen_x0, counter_depth, 0.84),
    wall_mat,
    collections["Built-ins"],
)
add_box(
    "Kitchen fitted countertop",
    (kitchen_center_x, kitchen_wall_face - (counter_depth + 0.04) / 2, 0.87),
    (kitchen_x1 - kitchen_x0 + 0.04, counter_depth + 0.04, 0.06),
    wood_mat,
    collections["Built-ins"],
)
add_tiled_wall(
    "Kitchen backsplash",
    "H",
    kitchen_x0,
    kitchen_x1,
    kitchen_wall_face,
    -1,
    kitchen_backsplash_materials,
    kitchen_backsplash_grout,
    collections["Wall Finishes"],
    z0=0.90,
    z1=1.58,
    tile_size=0.15,
    tile_gap=0.003,
)

# Hall-side base cabinet and counter fill the user's marked return area; sizing is provisional.
hall_return_x0 = px_to_x(497) + INTERIOR_WALL_M / 2 + 0.02
hall_return_x1 = px_to_x(637) - INTERIOR_WALL_M / 2 - 0.02
hall_return_back_y = px_to_y(747) - INTERIOR_WALL_M / 2
hall_return_front_y = px_to_y(839)
hall_return_center_x = (hall_return_x0 + hall_return_x1) / 2
hall_return_center_y = (hall_return_back_y + hall_return_front_y) / 2
add_box(
    "Kitchen hall return base cabinet",
    (hall_return_center_x, hall_return_center_y, 0.42),
    (hall_return_x1 - hall_return_x0, hall_return_back_y - hall_return_front_y, 0.84),
    wall_mat,
    collections["Built-ins"],
)
add_box(
    "Kitchen hall return countertop",
    (hall_return_center_x, (hall_return_back_y + hall_return_front_y - 0.02) / 2, 0.87),
    (hall_return_x1 - hall_return_x0 + 0.04, hall_return_back_y - hall_return_front_y + 0.02, 0.06),
    wood_mat,
    collections["Built-ins"],
)
hall_return_upper_depth = 0.34
hall_return_upper_height = 0.72
hall_return_upper_width = hall_return_x1 - hall_return_x0 - 0.015
hall_return_wall_face_y = px_to_y(747) - INTERIOR_WALL_M / 2
add_box(
    "Kitchen hall return upper cabinet",
    (hall_return_center_x, hall_return_wall_face_y - hall_return_upper_depth / 2, 1.94),
    (hall_return_upper_width, hall_return_upper_depth, hall_return_upper_height),
    wall_mat,
    collections["Built-ins"],
)
hall_return_cabinet_front_y = hall_return_wall_face_y - hall_return_upper_depth
hall_return_door_height = hall_return_upper_height - 0.08
hall_return_door_width = (hall_return_upper_width - 0.08) / 2
hall_return_door_center_offset = (hall_return_door_width + 0.04) / 2
for side, door_center_x in (
    ("left", hall_return_center_x - hall_return_door_center_offset),
    ("right", hall_return_center_x + hall_return_door_center_offset),
):
    add_box(
        "Kitchen hall return upper cabinet " + side + " glass door",
        (door_center_x, hall_return_cabinet_front_y - 0.008, 1.94),
        (hall_return_door_width, 0.012, hall_return_door_height),
        glass_mat,
        collections["Built-ins"],
    )
for side, frame_x in (
    ("left", hall_return_center_x - hall_return_upper_width / 2 + 0.012),
    ("center", hall_return_center_x),
    ("right", hall_return_center_x + hall_return_upper_width / 2 - 0.012),
):
    add_box(
        "Kitchen hall return upper cabinet " + side + " frame stile",
        (frame_x, hall_return_cabinet_front_y - 0.018, 1.94),
        (0.024, 0.03, hall_return_upper_height),
        wall_mat,
        collections["Built-ins"],
    )
for side, rail_z in (
    ("top", 1.94 + hall_return_upper_height / 2 - 0.012),
    ("bottom", 1.94 - hall_return_upper_height / 2 + 0.012),
):
    add_box(
        "Kitchen hall return upper cabinet " + side + " frame rail",
        (hall_return_center_x, hall_return_cabinet_front_y - 0.018, rail_z),
        (hall_return_upper_width, 0.03, 0.024),
        wall_mat,
        collections["Built-ins"],
    )
for side, handle_x in (
    ("left", hall_return_center_x - 0.018),
    ("right", hall_return_center_x + 0.018),
):
    add_box(
        "Kitchen hall return upper cabinet " + side + " handle",
        (handle_x, hall_return_cabinet_front_y - 0.034, 1.94),
        (0.012, 0.02, 0.07),
        frame_mat,
        collections["Built-ins"],
    )

upper_depth = 0.34
upper_y = kitchen_wall_face - upper_depth / 2
first_upper_start = LEFT + (EXTERIOR_WALL_M / 2 + 0.02) / PIXEL_TO_M
for index, (a, b) in enumerate(((first_upper_start, 250), (250, 330), (330, 412), (412, 497)), start=1):
    x0, x1 = px_to_x(a), px_to_x(b)
    add_box(
        "Kitchen wall cabinet " + str(index),
        ((x0 + x1) / 2, upper_y, 1.94),
        (x1 - x0 - 0.015, upper_depth, 0.72),
        wall_mat,
        collections["Built-ins"],
    )

# Inset sink and tap, positioned on the counter's west/left half.
sink_center_x = px_to_x(282)
add_box("Kitchen sink rim", (sink_center_x, counter_center_y, 0.914), (0.52, 0.40, 0.025), metal_mat, collections["Fixtures"])
add_box("Kitchen sink basin", (sink_center_x, counter_center_y, 0.918), (0.39, 0.28, 0.018), cooktop_mat, collections["Fixtures"])
add_box("Kitchen sink tap stem", (sink_center_x, kitchen_wall_face - 0.065, 0.99), (0.035, 0.035, 0.15), metal_mat, collections["Fixtures"])
add_box("Kitchen sink tap spout", (sink_center_x, kitchen_wall_face - 0.15, 1.055), (0.035, 0.17, 0.035), metal_mat, collections["Fixtures"])

# Built-in oven and hob share a cabinet bay; no freestanding dining furniture is added.
oven_center_x = px_to_x(367)
oven_width = 0.58
add_box("Kitchen built-in oven", (oven_center_x, counter_center_y, 0.40), (oven_width, counter_depth - 0.04, 0.64), appliance_mat, collections["Built-ins"])
add_box("Kitchen oven front", (oven_center_x, counter_front - 0.012, 0.41), (oven_width - 0.04, 0.024, 0.58), cooktop_mat, collections["Built-ins"])
add_box("Kitchen oven window", (oven_center_x, counter_front - 0.027, 0.36), (oven_width - 0.16, 0.012, 0.26), frame_mat, collections["Built-ins"])
add_box("Kitchen oven handle", (oven_center_x, counter_front - 0.035, 0.66), (oven_width - 0.12, 0.035, 0.035), metal_mat, collections["Built-ins"])
add_box("Kitchen cooktop", (oven_center_x, counter_center_y, 0.914), (0.58, 0.48, 0.022), cooktop_mat, collections["Fixtures"])


def add_burner(name, center, radius, material, collection, segments=24):
    vertices = [
        (center[0] + radius * math.cos(2 * math.pi * i / segments),
         center[1] + radius * math.sin(2 * math.pi * i / segments),
         center[2])
        for i in range(segments)
    ]
    return link_mesh(name, vertices, [tuple(range(segments))], material, collection)


for index, (dx, dy) in enumerate(((-0.15, -0.12), (0.15, -0.12), (-0.15, 0.12), (0.15, 0.12)), start=1):
    add_burner("Kitchen hob burner " + str(index), (oven_center_x + dx, counter_center_y + dy, 0.928), 0.055, metal_mat, collections["Fixtures"])

# K and F in the drawing identify separate tall kyl (fridge) and frys (freezer) units.
fridge_back_y = px_to_y(BOTTOM) + EXTERIOR_WALL_M / 2
fridge_depth = 0.62
for label, a, b, name in (("K", 484, 557, "Kyl - refrigerator"), ("F", 557, 630, "Frys - freezer")):
    x0, x1 = px_to_x(a), px_to_x(b)
    width = x1 - x0 - 0.02
    center_x = (x0 + x1) / 2
    center_y = fridge_back_y + fridge_depth / 2
    material = appliance_mat if label == "K" else metal_mat
    add_box(name, (center_x, center_y, 0.92), (width, fridge_depth, 1.84), material, collections["Fixtures"])
    add_box(name + " door", (center_x, fridge_back_y + fridge_depth - 0.012, 0.92), (width - 0.035, 0.024, 1.78), wall_mat, collections["Fixtures"])
    handle_x = x1 - 0.06 if label == "K" else x0 + 0.06
    add_box(name + " handle", (handle_x, fridge_back_y + fridge_depth + 0.005, 0.98), (0.025, 0.035, 0.62), frame_mat, collections["Fixtures"])
    add_text("Kitchen marker " + label, label, (center_x, center_y, 1.85), 0.20, appliance_marking_mat, collections["Annotations"])

def add_ellipsoid(name, location, dimensions, material, collection, segments=24, rings=12):
    x, y, z = location
    rx, ry, rz = (dimension / 2 for dimension in dimensions)
    vertices = []
    for ring in range(rings + 1):
        latitude = -math.pi / 2 + math.pi * ring / rings
        for segment in range(segments):
            angle = 2 * math.pi * segment / segments
            vertices.append(
                (
                    x + rx * math.cos(latitude) * math.cos(angle),
                    y + ry * math.cos(latitude) * math.sin(angle),
                    z + rz * math.sin(latitude),
                )
            )
    faces = []
    for ring in range(rings):
        for segment in range(segments):
            next_segment = (segment + 1) % segments
            faces.append(
                (
                    ring * segments + segment,
                    ring * segments + next_segment,
                    (ring + 1) * segments + next_segment,
                    (ring + 1) * segments + segment,
                )
            )
    return link_mesh(name, vertices, faces, material, collection)


def add_oval_surface(name, center, radii, z, material, collection, segments=32):
    vertices = [
        (center[0] + radii[0] * math.cos(2 * math.pi * i / segments),
         center[1] + radii[1] * math.sin(2 * math.pi * i / segments),
         z)
        for i in range(segments)
    ]
    return link_mesh(name, vertices, [tuple(range(segments))], material, collection)


def add_oval_ring(name, center, outer_radii, inner_radii, z, material, collection, segments=32):
    vertices = []
    for radii in (outer_radii, inner_radii):
        vertices.extend(
            (center[0] + radii[0] * math.cos(2 * math.pi * i / segments),
             center[1] + radii[1] * math.sin(2 * math.pi * i / segments),
             z)
            for i in range(segments)
        )
    faces = [
        (i, (i + 1) % segments, segments + (i + 1) % segments, segments + i)
        for i in range(segments)
    ]
    return link_mesh(name, vertices, faces, material, collection)


def add_shower_sector(center_px, center_py, radius_x_px, radius_y_px):
    cx, cy = px_to_x(center_px), px_to_y(center_py)
    radius_x = px_to_x(center_px + radius_x_px) - cx
    radius_y = cy - px_to_y(center_py + radius_y_px)
    segments = 24
    arc = [
        (
            cx + radius_x * math.cos(math.pi * i / (2 * segments)),
            cy - radius_y * math.sin(math.pi * i / (2 * segments)),
        )
        for i in range(segments + 1)
    ]
    vertices = [(cx, cy, 0.015)] + [(x, y, 0.015) for x, y in arc]
    faces = [(0, i + 1, i + 2) for i in range(segments)]
    link_mesh("Bathroom curved shower tray", vertices, faces, fixture_mat, collections["Fixtures"])

    thickness = 0.022
    inset_x, inset_y = thickness, thickness
    angles = [math.pi * i / (2 * segments) for i in range(segments + 1)]
    vertices = []
    for angle in angles:
        for rx, ry, z in (
            (radius_x, radius_y, 0.02),
            (radius_x, radius_y, 1.95),
            (radius_x - inset_x, radius_y - inset_y, 0.02),
            (radius_x - inset_x, radius_y - inset_y, 1.95),
        ):
            vertices.append((cx + rx * math.cos(angle), cy - ry * math.sin(angle), z))
    faces = []
    for i in range(segments):
        a, b = 4 * i, 4 * (i + 1)
        faces.extend(
            (
                (a, b, b + 1, a + 1),
                (a + 2, a + 3, b + 3, b + 2),
                (a + 1, b + 1, b + 3, a + 3),
                (a + 2, b + 2, b, a),
            )
        )
    faces.extend(((0, 1, 3, 2), (4 * segments, 4 * segments + 2, 4 * segments + 3, 4 * segments + 1)))
    link_mesh("Bathroom curved shower screen", vertices, faces, glass_mat, collections["Fixtures"])


# The plan fixes the positions; the photo informs the fixture forms and facing.
# Align each fixture's back edge to the modeled interior wall face.
bath_west_face = px_to_x(747) + INTERIOR_WALL_M / 2
bath_east_face = px_to_x(937) - INTERIOR_WALL_M / 2
bath_north_face = px_to_y(TOP) - EXTERIOR_WALL_M / 2
bath_west_pixel = LEFT + bath_west_face / PIXEL_TO_M
bath_north_pixel = BOTTOM - bath_north_face / PIXEL_TO_M
add_shower_sector(bath_west_pixel, bath_north_pixel, 110, 114)

# Vanity and vessel basin on the left wall, between the shower and toilet.
sink_x0 = bath_west_face
sink_x1 = sink_x0 + px_to_x(826) - px_to_x(779)
sink_y0, sink_y1 = px_to_y(473), px_to_y(402)
sink_center = ((sink_x0 + sink_x1) / 2, (sink_y0 + sink_y1) / 2)
add_box("Bathroom vanity cabinet", (sink_center[0], sink_center[1], 0.37), (sink_x1 - sink_x0, sink_y1 - sink_y0, 0.74), wall_mat, collections["Fixtures"])
add_box("Bathroom vanity countertop", (sink_center[0] + 0.03, sink_center[1], 0.77), (sink_x1 - sink_x0 + 0.06, sink_y1 - sink_y0 + 0.06, 0.06), fixture_mat, collections["Fixtures"])
add_ellipsoid("Bathroom vessel basin", (sink_center[0], sink_center[1], 0.88), (0.30, 0.40, 0.12), fixture_mat, collections["Fixtures"])
add_oval_surface("Bathroom basin interior", sink_center, (0.105, 0.15), 0.934, glass_mat, collections["Fixtures"])
add_box("Bathroom basin tap", (sink_x0 + 0.045, sink_center[1], 0.95), (0.045, 0.045, 0.08), frame_mat, collections["Fixtures"])

# Wall-mounted mirror cabinet above the vanity, based on the bathroom doorway reference.
mirror_cabinet_depth = 0.12
mirror_cabinet_width = sink_y1 - sink_y0 + 0.08
mirror_cabinet_height = 1.10
mirror_cabinet_center_z = 1.72
mirror_cabinet_front_x = bath_west_face + mirror_cabinet_depth
mirror_mat = make_material("Apartment - mirror surface", (0.72, 0.78, 0.81, 1.0), 0.12)
add_box(
    "Bathroom mirror cabinet",
    (bath_west_face + mirror_cabinet_depth / 2, sink_center[1], mirror_cabinet_center_z),
    (mirror_cabinet_depth, mirror_cabinet_width, mirror_cabinet_height),
    wall_mat,
    collections["Fixtures"],
)
mirror_door_height = mirror_cabinet_height - 0.06
mirror_door_width = (mirror_cabinet_width - 0.06) / 2
mirror_door_offset = (mirror_door_width + 0.04) / 2
for side, door_center_y in (
    ("left", sink_center[1] - mirror_door_offset),
    ("right", sink_center[1] + mirror_door_offset),
):
    add_box(
        "Bathroom mirror cabinet " + side + " mirrored door",
        (mirror_cabinet_front_x + 0.008, door_center_y, mirror_cabinet_center_z),
        (0.012, mirror_door_width, mirror_door_height),
        mirror_mat,
        collections["Fixtures"],
    )
for side, frame_y in (
    ("near", sink_center[1] - mirror_cabinet_width / 2 + 0.012),
    ("center", sink_center[1]),
    ("far", sink_center[1] + mirror_cabinet_width / 2 - 0.012),
):
    add_box(
        "Bathroom mirror cabinet " + side + " frame stile",
        (mirror_cabinet_front_x + 0.015, frame_y, mirror_cabinet_center_z),
        (0.03, 0.024, mirror_cabinet_height),
        wall_mat,
        collections["Fixtures"],
    )
for side, rail_z in (
    ("top", mirror_cabinet_center_z + mirror_cabinet_height / 2 - 0.012),
    ("bottom", mirror_cabinet_center_z - mirror_cabinet_height / 2 + 0.012),
):
    add_box(
        "Bathroom mirror cabinet " + side + " frame rail",
        (mirror_cabinet_front_x + 0.015, sink_center[1], rail_z),
        (0.03, mirror_cabinet_width, 0.024),
        wall_mat,
        collections["Fixtures"],
    )
for side, handle_y in (
    ("near", sink_center[1] - 0.022),
    ("far", sink_center[1] + 0.022),
):
    add_box(
        "Bathroom mirror cabinet " + side + " handle",
        (mirror_cabinet_front_x + 0.032, handle_y, mirror_cabinet_center_z),
        (0.02, 0.012, 0.07),
        frame_mat,
        collections["Fixtures"],
    )

# The toilet faces into the room from the west wall, close to the entry.
toilet_x0 = bath_west_face
toilet_x1 = toilet_x0 + px_to_x(856) - px_to_x(773)
toilet_y0, toilet_y1 = px_to_y(581), px_to_y(532)
toilet_center = ((toilet_x0 + toilet_x1) / 2, (toilet_y0 + toilet_y1) / 2)
cistern_x0 = bath_west_face
cistern_x1 = cistern_x0 + px_to_x(798) - px_to_x(773)
cistern_y0, cistern_y1 = px_to_y(566), px_to_y(532)
add_box(
    "Bathroom toilet cistern",
    ((cistern_x0 + cistern_x1) / 2, (cistern_y0 + cistern_y1) / 2, 0.39),
    (cistern_x1 - cistern_x0, cistern_y1 - cistern_y0, 0.78),
    fixture_mat,
    collections["Fixtures"],
)
toilet_bowl_width = px_to_x(856) - px_to_x(795)
toilet_bowl_center = (cistern_x1 + toilet_bowl_width / 2 - 0.02, toilet_center[1])
add_ellipsoid("Bathroom toilet bowl", (toilet_bowl_center[0], toilet_bowl_center[1], 0.24), (toilet_bowl_width, 0.31, 0.40), fixture_mat, collections["Fixtures"])
add_oval_ring("Bathroom toilet seat", toilet_bowl_center, (0.205, 0.145), (0.125, 0.078), 0.445, fixture_mat, collections["Fixtures"])
add_oval_surface("Bathroom toilet opening", toilet_bowl_center, (0.122, 0.075), 0.446, glass_mat, collections["Fixtures"])

# Washer follows the TM symbol on the right wall, with its control/front toward the entry.
washer_x1 = bath_east_face
washer_x0 = washer_x1 - px_to_x(936) + px_to_x(875)
washer_y0, washer_y1 = px_to_y(325), px_to_y(228)
washer_center = ((washer_x0 + washer_x1) / 2, (washer_y0 + washer_y1) / 2)
add_box("Bathroom washing machine TM", (washer_center[0], washer_center[1], 0.43), (washer_x1 - washer_x0, washer_y1 - washer_y0, 0.86), fixture_mat, collections["Fixtures"])
washer_top_width = washer_x1 - washer_x0 - 0.03
add_box("Bathroom washer top", (washer_x1 - washer_top_width / 2, washer_center[1], 0.875), (washer_top_width, washer_y1 - washer_y0 - 0.03, 0.03), wall_mat, collections["Fixtures"])
add_box("Bathroom washer control panel", (washer_center[0], washer_y1 - 0.055, 0.89), (washer_x1 - washer_x0 - 0.06, 0.07, 0.018), appliance_mat, collections["Fixtures"])

# Remove only the untouched default cube; keep the user's camera and light.
default_cube = bpy.data.objects.get("Cube")
if default_cube and default_cube.type == "MESH":
    bpy.data.objects.remove(default_cube, do_unlink=True)

scene.unit_settings.system = "METRIC"
scene.unit_settings.scale_length = 1.0
scene["apartment_floor_area_target_m2"] = AREA_TARGET_M2
scene["apartment_floor_area_basis"] = "53 m2 clear floor area; scaled from the non-scale drawing outline"
scene["apartment_wall_height_m"] = WALL_HEIGHT_M
scene["apartment_assumptions"] = (
    "Provisional visualization only. The plan is explicitly not to scale. "
    "Only 53 m2 apartment area and 2.40 m height were supplied. "
    "Wall thicknesses, exterior dimensions, opening widths/heights, window levels, "
    "fixture sizes, and room proportions are estimates; verify before construction."
)
scene["apartment_fixture_reference"] = (
    "Bathroom fixture positions follow the floor-plan symbols. A supplementary bathroom photo "
    "informed the curved shower screen, vanity basin, toilet form, and washer orientation; "
    "a mirror cabinet is added above the vanity based on bathroom/01-from-door.png. Fixtures are "
    "aligned to modeled interior wall faces. The photo is not a measured source; added dimensions "
    "are provisional."
)
scene["apartment_floor_reference"] = (
    "Non-bathroom floors use provisional staggered light-oak plank geometry informed by the room "
    "photos. The bathroom has provisional gray floor tiles and grout. Plank and tile sizes are "
    "visual estimates, not measured dimensions; the bathroom boundary is inferred from the "
    "not-to-scale floor plan."
)
scene["apartment_wall_tile_reference"] = (
    "Bathroom wall finishes use provisional warm-white square tiles with light-gray grout on the "
    "modeled interior wall faces, guided by bathroom/01-from-door.png. Tile size, color, and grout "
    "width are visual estimates, not measured specifications."
)
scene["apartment_bathroom_wall_connection_reference"] = (
    "The two long bathroom side partitions meet the north facade, closing the user's marked gap on "
    "both sides. The south bathroom doorway opening and outer apartment outline remain unchanged."
)
scene["apartment_kitchen_reference"] = (
    "Kitchen photos inform the wall-connected counter, sink, oven/hob, and cabinets. K/F in the "
    "floor plan are modeled as separate refrigerator and freezer appliances against the south wall. "
    "No dining table or other freestanding furniture is included; dimensions are provisional."
)
scene["apartment_bed_reference"] = (
    "The user uses the living room as their bedroom. A separate movable bed is placed there; "
    "its mattress is exactly 1.60 x 2.00 m, with a provisional 0.60 m sleeping-surface height. "
    "Frame, supports, duvet, and pillow sizes are provisional."
)
scene["apartment_kitchen_finish_reference"] = (
    "Kitchen-facing wall panels use provisional warm greige, and the backsplash uses muted gray-beige "
    "square tiles with grout, guided by kitchen/01-from-dining.png and kitchen/02-counter-and-appliances.png. "
    "Bedroom and living-room walls remain warm white. Colors and tile dimensions are visual estimates."
)
scene["apartment_kitchen_hall_wall_reference"] = (
    "Kitchen/hall partition returns follow the user's red-marked floor-plan correction. Their traced "
    "locations and thickness remain provisional because the plan is not to scale. The hall storage "
    "enclosure is empty, with an open doorway and frame on the red-marked upper east wall above the "
    "short divider; the lower east return remains solid. No storage fittings are modeled."
)
scene["apartment_bedroom_hall_opening_reference"] = (
    "The bedroom-to-hall opening was widened through the full short wall return marked by the user. "
    "Its traced extent remains provisional because the floor plan is not to scale."
)
scene["apartment_kitchen_counter_alignment_reference"] = (
    "The kitchen run remains on its kitchen-side wall position. Its west end is extended to the interior "
    "face of the west wall to fill the marked gap; no apartment shell or room boundary was moved."
)
scene["apartment_bedroom_kitchen_wall_reference"] = (
    "The bedroom-kitchen partition extends to the interior face of the west facade to close the marked "
    "gap. Its doorway and the apartment outline remain unchanged."
)
scene["apartment_kitchen_north_wall_reference"] = (
    "The kitchen-side partition also extends to the west facade's interior face. Its wall line and the "
    "apartment outline remain unchanged; only the marked end gap is closed."
)
scene["apartment_kitchen_sink_clearance_reference"] = (
    "The sink and tap are shifted left from the cooktop to create a small provisional counter gap; "
    "the cooktop and apartment layout remain unchanged."
)
scene["apartment_kitchen_hall_counter_reference"] = (
    "Provisional base and upper cabinets with a countertop fill the user's marked return beside the hall "
    "opening, guided by kitchen/04-toward-hall.png. The upper cabinet has paired framed glass doors. "
    "Exact sizes and finishes are not confirmed."
)
scene["apartment_scale_m_per_plan_pixel"] = PIXEL_TO_M
scene["apartment_living_room_wall_estimates_m"] = (
    "north={north:.2f}; east={east:.2f}; south={south:.2f}; "
    "west partition={west:.2f}".format(
        north=living_wall_lengths["north"],
        east=living_wall_lengths["east"],
        south=living_wall_lengths["south"],
        west=living_wall_lengths["west partition"],
    )
)
scene["apartment_living_room_wall_estimates_basis"] = (
    "Provisional clear lengths from the traced, not-to-scale floor plan after scaling the "
    "apartment outline to the supplied 53 m2 area. Replace with verified measurements."
)
scene["apartment_outer_outline_area_estimate_m2"] = polygon_area(
    [((x - LEFT) * PIXEL_TO_M, (BOTTOM - y) * PIXEL_TO_M) for x, y in PLAN_OUTLINE]
)

# Configure a useful plan view and camera while retaining existing scene objects.
center_x = right_x / 2
center_y = (top_y + bottom_y) / 2
camera = scene.camera
if camera is None:
    camera_data = bpy.data.cameras.new("Apartment Plan Camera")
    camera = bpy.data.objects.new("Apartment Plan Camera", camera_data)
    scene.collection.objects.link(camera)
    scene.camera = camera
camera.location = (center_x, center_y, 13.0)
camera.rotation_euler = (0.0, 0.0, 0.0)
camera.data.type = "ORTHO"
camera.data.ortho_scale = right_x * 1.15
scene.render.resolution_x = 1600
scene.render.resolution_y = 900
scene.render.resolution_percentage = 100

light = bpy.data.objects.get("Light")
if light and light.type == "LIGHT":
    light.data.type = "AREA"
    light.data.energy = 1800
    light.data.shape = "DISK"
    light.data.size = 9.0
    light.location = (center_x, center_y, 8.0)

for screen in bpy.data.screens:
    for area in screen.areas:
        if area.type == "VIEW_3D":
            region = area.spaces.active.region_3d
            region.view_perspective = "ORTHO"
            region.view_location = (center_x, center_y, 1.1)
            region.view_distance = right_x * 1.38
            region.view_rotation = (1.0, 0.0, 0.0, 0.0)
            area.spaces.active.shading.color_type = "MATERIAL"
            area.spaces.active.overlay.show_extras = False
            area.spaces.active.overlay.show_cursor = False

print(
    "Apartment model built:",
    round(get_interior_area(PIXEL_TO_M), 2),
    "m2 clear floor target;",
    round(scene["apartment_outer_outline_area_estimate_m2"], 2),
    "m2 outer outline estimate;",
    round(PIXEL_TO_M, 6),
    "m per reference pixel.",
)

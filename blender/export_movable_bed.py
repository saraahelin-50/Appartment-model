"""Export the apartment's movable bed as an appendable Blender collection."""

from pathlib import Path

import bpy


PROJECT_ROOT = Path(__file__).resolve().parent.parent
APARTMENT_FILE = PROJECT_ROOT / "apartment.blend"
ASSET_FILE = Path(__file__).resolve().with_name("movable_bed_160x200.blend")
FURNITURE_COLLECTION_NAME = "Furniture"
BED_COLLECTION_NAME = "Movable Bed"
BED_ROOT_NAME = "Movable Bed - 160 x 200 cm"
MATTRESS_NAME = "Movable Bed - Mattress 160 x 200 cm"

if not APARTMENT_FILE.is_file():
    raise FileNotFoundError("Generate apartment.blend before exporting the bed asset.")

bpy.ops.wm.open_mainfile(filepath=str(APARTMENT_FILE))

furniture = bpy.data.collections.get(FURNITURE_COLLECTION_NAME)
bed_collection = bpy.data.collections.get(BED_COLLECTION_NAME)
bed_root = bpy.data.objects.get(BED_ROOT_NAME)
mattress = bpy.data.objects.get(MATTRESS_NAME)
if furniture is None or bed_collection is None or bed_root is None or mattress is None:
    raise RuntimeError("The apartment model is missing the movable bed collection or objects.")
if (
    furniture.children.get(BED_COLLECTION_NAME) is not bed_collection
    or bed_collection.objects.get(BED_ROOT_NAME) is not bed_root
    or mattress.parent is not bed_root
):
    raise RuntimeError("The movable bed must be in Furniture and its mattress parented to the bed root.")

bed_root.location = (0.0, 0.0, 0.0)
bed_root["placement"] = "At the asset origin; append it to an apartment and move it into place."
bpy.data.libraries.write(str(ASSET_FILE), {bed_collection}, fake_user=True, compress=True)
print("Wrote appendable bed asset:", ASSET_FILE)

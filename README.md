# Apartment Model

This project creates a revisable three-dimensional apartment model from the supplied floor plan. The architectural shell is being built first, with fixtures and built-ins kept separate so they can be refined independently. The current modeling workflow uses Blender 5.3 and the editable Python source in [`blender/apartment_model.py`](blender/apartment_model.py).

## Apartment layout

The supplied Swedish floor plan shows:

- **Sovrum** — bedroom
- **Badrum** — bathroom, with a shower, sink, toilet, and washing machine marked
- **Vardagsrum** — living room
- **Kök** — kitchen
- **Hall** — entrance hall

The drawing also marks built-in storage (`G`), kitchen appliances (`K` and `F`), windows, and the entrance. Preserve these features in the architectural model where they are legible.

## Reference and accuracy

Use [`assets/floor-plan.jpg`](assets/floor-plan.jpg) as the source for room arrangement and visible features. Its note says the plan is **not to scale** and that deviations may occur. No verified measurements, wall heights, or construction details are provided yet.

Do not present estimates inferred from the image as measured dimensions. Keep assumptions explicit and easy to revise; use verified measurements when they become available. Until then, any geometry based on proportions is a provisional visualization, not a dimensionally accurate or construction-ready model.

The first Blender blockout uses the supplied **53 m²** area and **2.40 m** height. The 2.40 m value is interpreted as floor-to-ceiling/wall height. The image proportions are scaled to make the modeled clear floor area approximately 53 m²; exterior dimensions, wall thicknesses, room proportions, opening sizes and heights, and fixture sizes remain estimates. Bathroom fixture positions follow the plan symbols, while the supplied bathroom photo informs their forms and orientation; fixtures are aligned flush to modeled interior wall faces. Kitchen photos inform the wall-connected casework, sink, oven/hob, and cabinets; K/F remain separate refrigerator/freezer appliances at the plan's marked location. A movable bed with a 160 × 200 cm mattress and a provisional **60 cm floor-to-sleeping-surface height** is placed in the living room, which the user uses as their bedroom; other freestanding furniture is not included. These assumptions are also stored as scene custom properties.

The living room's four boundary walls have approximate clear-length labels and arrows on the floor. These estimates are derived from the traced plan coordinates after scaling the outline to 53 m²; they are not measured apartment dimensions and should be replaced when verified measurements are available.

The aquarium-and-shelf asset is included as a separate collection in [`apartment.blend`](apartment.blend), built by [`blender/aquarium_shelf.py`](blender/aquarium_shelf.py), and exported as [`blender/aquarium_shelf.glb`](blender/aquarium_shelf.glb). Its overall width (**0.95 m**), depth (**0.45 m**), and height (**0.95 m**) are user-provided. Since only the combined height was specified, the model provisionally allocates **0.40 m** to the open shelf stand and **0.55 m** to the aquarium. Component thicknesses and the water fill level are also provisional; dimensions and assumptions are recorded on the root object and at the top of the source script. The stand and tank are separate collections with individually editable parts. The collection is at the origin until its position in a room is chosen.

![Apartment floor plan](assets/floor-plan.jpg)

## Interior visual references

The supplied interior images are stored under [`assets/references/`](assets/references/), grouped by the room or area they primarily show. Start with the [reference catalog](assets/references/README.md) for inferred viewpoints, visible features, and cross-room clues.

These images are visual guidance, not verified survey photographs or dimensional evidence. Their provenance and consistency with the exact apartment have not been established. Use the floor plan for room adjacency and openings; confirm uncertain details and all dimensions before treating them as model facts.

## Project direction

1. Establish the apartment shell and room layout.
2. Refine openings, built-ins, and visible fixtures using confirmed information.
3. Add furniture as a later, separate layer of work.
4. Refine the Blender shell and replace provisional dimensions with measurements when available.

## Wardrobe component

The L-shaped wardrobe is a separate, movable collection, not part of the apartment shell. Its editable source is [`blender/wardrobe_component.py`](blender/wardrobe_component.py). In `apartment.blend`, select **Wardrobe - Move as one** in the Outliner and move it as a single unit; it starts beside the apartment model. To use it in another project or session, use **File > Append** and select the `Wardrobe Component` collection from `apartment.blend`, or run the component script in the target Blender scene.

The model uses the 1.50 m main run (three nominal 0.50 m bays), 0.35 m shelf depth, 0.60 m return, and 0.50 m mirror width in [`assets/wardrobe-measurements.svg`](assets/wardrobe-measurements.svg). The shelf measurement applies to the actual shelves; the back panels add 0.018 m to the case depth, and drawer fronts project beyond it. The mirror measurement applies to the reflective face; its provisional frame adds 0.05 m to the section width. The 2.10 m height and 0.018 m panel thickness are provisional and editable at the top of the source script. The main run's 1.50 m width includes its dividers, so clear shelf openings are slightly narrower than 0.50 m. The reference photos guide the open-shelf and lower-drawer arrangement; they do not establish construction details. To rebuild or adjust the component, open `apartment.blend` in Blender 5.3+, run `blender/wardrobe_component.py` in the Scripting workspace, then save the project. Running the script replaces only the wardrobe collection and preserves the root object's placement.

## Getting started

Open `apartment.blend` in Blender 5.3 or later to inspect the current model. To move the bed, select **Movable Bed - 160 x 200 cm** in the **Furniture** collection in the Outliner. With the pointer over the 3D View, press **G**, then **Shift+Z**, move the bed, and click or press **Enter** to confirm (**Esc** cancels). Press **R**, then **Z** to rotate it on the floor. The frame, mattress, duvet, headboard, and pillows move together. Their individual objects are selection-locked to prevent accidental movement; unlock them in the Outliner when intentionally editing the bed.

To add the bed to another Blender drawing without replacing that drawing, choose **File → Append**, open `blender/movable_bed_160x200.blend`, open **Collection**, select **Furniture**, and click **Append**. In the Outliner, select **Movable Bed - 160 x 200 cm**. With the pointer over the 3D View, press **G**, then **Shift+Z**, move the mouse to position the bed on the floor, and click or press **Enter** to confirm (**Esc** cancels). For a precise move along an apartment axis, press **G**, then **X** or **Y**, type a distance in meters, and press **Enter**. The reusable asset is centered at the origin; position it where desired after appending.

To regenerate or revise the apartment, open `blender/apartment_model.py` in Blender's Scripting workspace and choose **Run Script**; save the result as `apartment.blend` in the repository root. Then regenerate the appendable bed asset from the repository root with `blender --background --python blender/export_movable_bed.py`. The apartment script replaces only its named provisional model collection, retains the camera and light, and configures them for a plan view. Edit the traced plan coordinates and clearly marked assumptions in the script as better measurements become available. This is a visualization workflow, not construction documentation.

The saved `apartment.blend` already includes the `Aquarium + Shelf - 95x45x95cm` collection at the origin with its base on `z = 0`; move the root parent empty to place it. To rebuild it, run `blender/aquarium_shelf.py` in Blender's Scripting workspace; it replaces only that named collection. To bring the standalone asset into another file, use **File → Import → glTF 2.0**, select `blender/aquarium_shelf.glb`, then move its root empty. To regenerate that standalone file after changing the source, run the script in the apartment file and call `export_aquarium_asset("/path/to/blender/aquarium_shelf.glb")` from Blender's Python Console.

## Contributing

See [`AGENTS.md`](AGENTS.md) for project-specific guidance for AI coding agents and contributors.

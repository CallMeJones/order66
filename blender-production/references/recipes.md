# Blender Production — Domain Recipes

Each recipe follows the SKILL.md loop. Tool names are catalog helpers reached via
`invoke_blender_tool` (look up schema first). The plan call returns the authoritative
`helper_path`; these are sensible defaults, not a substitute for inspecting the live scene.

---

## Full professional animation

Plan: `plan_animation_workflow` (mode `full`) or `plan_advanced_scene_workflow` domain
`advanced_animation`.

1. **Brief & timing** — establish frame range and fps with `set_scene_frame_range`. Match the
   plan's timing chart; storyboard the beats before keying.
2. **Subjects** — create/import the objects to animate; inspect with `list_scene_objects`.
3. **Motion** — helpers: `create_camera_dolly_animation`, `create_camera_orbit`,
   `create_follow_path_animation`, plus transform-keying helpers. Use easing
   (`SINE`/`BEZIER`) for natural in/out; `LINEAR` only for mechanical moves.
4. **Camera & framing** — `set_active_camera`, `set_camera_settings` (lens, DOF). Use a tracked
   empty as a dolly/orbit target for clean recomposition.
5. **Lighting** — `apply_lighting_preset` (product_softbox, dramatic_rim, gallery_even).
6. **Review loop** — `set_viewport_view view=camera` → `capture_animation_playblast` across the
   range. Iterate on spacing, arcs, contacts. Optionally `run_animation_workflow` mode `review`
   for structured evaluator findings, then mode `repair` with `apply_repairs`.
7. **Commit → save → render** (see Rendering recipe).

Scripting fallback only for custom fcurve work — and mind the 5.1 channelbag/slot API.

---

## Procedural 3D object

Plan: `plan_advanced_scene_workflow` domain `procedural_3d`.

1. **Base geometry** — primitive/creation helpers; set transform on creation.
2. **Procedural detail** — modifier/geometry helpers via `search_blender_tools query="modifier"`
   (array, bevel, subdivision, boolean, etc.). Stack non-destructively; inspect after each.
3. **Materials** — `create_material_palette`, `assign_emission_material_to_selected`, or PBR
   material helpers. Assign to selected meshes.
4. **Verify the model** — `capture_object_inspection_renders` for close-ups (undersides, side
   views, occluded parts, defects). This renders diagnostic PNGs from bounded views.
5. **Organize** — `create_collection` to group; name objects meaningfully.
6. **Commit → save.** Export via the appropriate export helper if a deliverable file is needed
   (confirm the path with the user).

---

## Simulation

Plan: `plan_advanced_scene_workflow` domain `simulation_setup`. Inspect with
`get_simulation_details` / `inspect_simulation_bake`.

1. **Domain & objects** — set up the sim domain and emitters/colliders via helpers.
2. **Settings sanity** — keep resolution modest first. **Gas: low res + dissolve ON** (see
   Mantaflow OOM gotcha). Validate before a long bake.
3. **Bake** — `stage_persistent_simulation_bake` for a persistent cache bake. This needs explicit
   one-time user approval (session script-trust does NOT cover it) — stage, then let the user
   approve. Bakes are long-running.
4. **Recover** — if the bridge drops mid-bake (WinError 10061 / timeout), it's recoverable: wait,
   `blender_bridge_status`, restore from the latest checkpoint, lower res, retry.
5. **Look-dev** — drive density/shading from the volume material rather than re-baking at high res.
6. **Review → commit → save → render.**

---

## Rendering

Plan: `plan_advanced_scene_workflow` domain `compositor_render`. Inspect with
`get_render_camera_compositor_details`.

1. **Settings** — `set_render_settings` (engine, resolution, fps, frame range, transparency).
2. **Camera** — confirm active camera and framing; review one frame in camera view first.
3. **Start job** — `start_render_job`:
   - `output_kind`: `frames` (PNG sequence, progress counts) or `video`/`mp4`.
   - `quality`: `auto` low-res for preview/review; `final`/`1080p`/`production` for deliverables.
   - Pass `camera_name`, `frame_start/end`, `samples`, `resolution_*` as needed.
   - Returns a `job_id` immediately — it's a **background** job.
4. **Poll** — `get_render_job_status job_id=...` until terminal. Don't start duplicate jobs.
5. **Assemble / validate** — `assemble_render_job_video` for MP4 from frames;
   `validate_render_job_output` to confirm outputs exist and are sane.
6. **Evidence** — frame/metadata resources are under the project `.claude_blender/captures` /
   render output dirs; read PNGs to confirm the result.

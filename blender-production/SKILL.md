---
name: blender-production
description: Drive the Blender Agent Bridge MCP to build professional 3D/2D work — animation, modeling, simulation, rendering — via the helper-first workflow. Use when the user wants to create, animate, simulate, model, or render anything in Blender, set up a scene, make an animatic/storyboard, build a 3D object, or run a bake/render through the blender MCP tools. Requires the `blender` MCP server (Blender Agent Bridge) running with its localhost bridge active.
---

# Blender Production

Paved-path workflow for the `blender` MCP server (Blender Agent Bridge). The value is the
discipline: **plan first, use helpers, preview, review with your eyes, commit, save.** Never
hand-write Python when a helper exists.

## The loop (every task)

1. **Status** — `blender_bridge_status`. Confirm `ok`, note `blender_version`, `addon_version`,
   `external_script_trust`. If `recoverable`/`bridge_busy`, wait `poll_after_seconds` and recheck;
   don't retry blindly.
2. **Plan** — call `plan_advanced_scene_workflow` (domains: `2d_storyboard`, `procedural_3d`,
   `advanced_animation`, `simulation_setup`, `compositor_render`) or `plan_animation_workflow`
   **before mutating**. Follow its `helper_path` and `inspect_first`.
3. **Inspect** — run the plan's inspect tool (`list_scene_objects`, `get_2d_animation_details`,
   `get_simulation_details`, etc.) to learn real names, positions, orientation, units.
4. **Build with helpers** — `search_blender_tools` → `get_blender_tool_schema` →
   `invoke_blender_tool`. Validate the schema before each call. Most creation helpers are
   `risk: preview` (reversible). See [references/recipes.md](references/recipes.md) for per-domain
   sequences.
5. **Review** — `capture_animation_playblast`. **Set the viewport to camera view first**
   (`set_viewport_view view=camera`) or you'll review the editing view, not the shot. Read the
   PNG frames; check framing, staging, timing.
6. **Commit & save** — inspect result, then `commit_preview`, then `save_blend_file` (omit path
   for the bound file). Render finals with `start_render_job` (background; poll
   `get_render_job_status`).

## Hard rules

- **Helper-first.** Use `draft_script` only for a genuine helper gap (custom GP strokes, SVG
  import, niche vector ops). The static AST denylist before `exec()` is bypassable and restricted —
  treat scripting as last resort, never the default.
- **Confirm paths.** `create_new_blender_project`, `open_blend_file`, save-as/copy need a
  user-given path + `user_confirmed_path` + `confirm_discard_current`. Never invent a filesystem
  path. Destructive/new-project ops checkpoint first by default — keep that.
- **One transaction.** Preview helpers batch into a transaction; `commit_preview` /
  `revert_preview` applies to all pending changes. Review before committing.
- **Recover, don't thrash.** On `bridge_timeout`: wait `poll_after_seconds`, `blender_bridge_status`,
  inspect visual-evidence/audit resources, *then* decide. Long ops (bake/render) are background.

## Gotchas (verified)

- **Camera-view playblast trap.** Playblast captures the active viewport. If it's "User Perspective"
  you're not seeing the camera. Switch to camera view before capturing.
- **Default scene cruft.** A fresh project has Cube + Light + Camera. Hide/remove the Cube
  (`set_object_visibility hide_render hide_viewport`) before it photobombs a render.
- **Blender 5.1 slotted actions.** `Action.fcurves` is gone in 5.1. Reach fcurves via layered
  channelbags matched by slot handle. (Only relevant if you fall back to scripting animation.)
- **Mantaflow bake OOM.** High-res gas bake with dissolve off can crash Blender (bridge →
  WinError 10061). Bake gas at low res, keep dissolve on, get density from the volume material.
  Use `stage_persistent_simulation_bake` for cache bakes (needs one-time user approval).
- **draft_script trust.** Even with session script-trust active, persistent sim/cache bakes and
  free operators require explicit one-time approval — stage them, don't auto-run.

## Domain recipes

See [references/recipes.md](references/recipes.md) — full animation, procedural 3D object,
simulation, rendering.

/*
 * tools_scene.cpp - Scene render-hook dispatcher.
 *
 * Iterates the g_panel_defs registry and calls every registered draw_scene
 * callback. Called by main.cpp each frame inside BeginMode3D / BeginMode2D so
 * tool overlays draw on top of the scene.
 */

#include "tools_scene.h"
#include "tools_registry.h"
#include "imgui.h"

void DrawSceneHooks(SceneContext *sctx, AppConfig *cfg)
{
    /* DrawGUI() creates the ImGui context on its first frame. Some scene hooks
     * inspect ImGui input state, so do not dispatch them before that context
     * exists. The hooks begin normally on the following frame. */
    if (!ImGui::GetCurrentContext()) return;

    for (int i = 0; i < g_panel_count; i++)
    {
        if (g_panel_defs[i].draw_scene)
            g_panel_defs[i].draw_scene(sctx, cfg);
    }
}
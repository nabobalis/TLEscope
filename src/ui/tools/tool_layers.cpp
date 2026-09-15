/* tool_layers.cpp - Layers panel */
#include "tools.h"
#include "tools_common.h"
#include "core/theme.h"
#include "core/config.h"
#include "ui/labels.h"
#include "ui/tools/tools_settings.h"
#include "map_detail_data.h"
#include <cmath>
#include <raylib.h>
#include "imgui.h"
#include "IconsFontAwesome6.h"

static const char *COASTLINES_KEY = "map2d.coastlines";

void DrawPanelLayers(UIContext *ctx, AppConfig *cfg)
{
    (void)ctx;
    ImGui::PushTextWrapPos(0.0f);
    const float icon_w = 24.0f;
    auto row = [&](const char *label, bool *value, const char *icon, const char *tip) {
        ImGui::PushStyleColor(ImGuiCol_Text, ThemeColor(*value ? g_theme.ui.ui_accent : g_theme.ui.text_secondary));
        ImU32 col = ImGui::GetColorU32(ImGuiCol_Text); ImVec2 sz = ImGui::CalcTextSize(icon); ImVec2 p = ImGui::GetCursorScreenPos();
        ImGui::GetWindowDrawList()->AddText(ImVec2(p.x + (icon_w - sz.x) * 0.5f, p.y), col, icon); ImGui::PopStyleColor();
        ImGui::Dummy(ImVec2(icon_w, ImGui::GetFrameHeight())); ImGui::SameLine(); ImGui::Checkbox(label, value);
        if (tip && ImGui::IsItemHovered()) ImGui::SetTooltip("%s", tip);
    };
    row("Clouds", &cfg->show_clouds, ICON_FA_CLOUD, "Show cloud layer (C)");
    row("Night Lights", &cfg->show_night_lights, ICON_FA_MOON, "Show night-side city lights (N)");
    row("Markers", &cfg->show_markers, ICON_FA_MAP_PIN, "Show ground markers (L)");
    row("Scattering", &cfg->show_scattering, ICON_FA_SUN, "Atmospheric scattering effect");
    row("Skybox", &cfg->show_skybox, ICON_FA_STAR, "Show starfield skybox");
    row("Highlight Sunlit", &cfg->highlight_sunlit, ICON_FA_BOLT, "Highlight sunlit portions of orbits");
    row("Slant Range", &cfg->show_slant_range, ICON_FA_RULER, "Show slant range line to home");
    row("Ground Coverage", &cfg->show_ground_coverage, ICON_FA_ROUTE, "Show the line-of-sight ground coverage footprint");
    row("Apsides", &cfg->show_apsides, ICON_FA_CIRCLE_DOT, "Show perigee/apogee markers and altitude labels");
    bool enabled = ToolSettingGetBool(cfg, COASTLINES_KEY, true); if (ImGui::Checkbox("2D Coastlines", &enabled)) ToolSettingSetBool(cfg, COASTLINES_KEY, enabled);
    ImGui::Separator();
    bool labels = ToolSettingGetBool(cfg, LABELS_KEY_ENABLED, true); if (ImGui::Checkbox("Labels", &labels)) ToolSettingSetBool(cfg, LABELS_KEY_ENABLED, labels);
    int mode = ToolSettingGetInt(cfg, LABELS_KEY_MODE, LABELS_MODE_ACTIVE_ONLY); const char *modes[] = {"Active only","All","None"}; ImGui::SetNextItemWidth(-1); if (ImGui::Combo("##label_mode", &mode, modes, 3)) ToolSettingSetInt(cfg, LABELS_KEY_MODE, mode);
    bool alt = ToolSettingGetBool(cfg, LABELS_KEY_ALTITUDE, false); if (ImGui::Checkbox("Label Altitude", &alt)) ToolSettingSetBool(cfg, LABELS_KEY_ALTITUDE, alt);
    float size = ToolSettingGetFloat(cfg, LABELS_KEY_SIZE, 1.0f); if (ImGui::SliderFloat("Label Size", &size, 0.5f, 1.5f, "%.2fx")) ToolSettingSetFloat(cfg, LABELS_KEY_SIZE, size);
    bool bg = ToolSettingGetBool(cfg, LABELS_KEY_BG, true); if (ImGui::Checkbox("Label Background", &bg)) ToolSettingSetBool(cfg, LABELS_KEY_BG, bg);
    int max_count = ToolSettingGetInt(cfg, LABELS_KEY_MAX_COUNT, 200); if (ImGui::SliderInt("Max Labels", &max_count, 10, 1000)) ToolSettingSetInt(cfg, LABELS_KEY_MAX_COUNT, max_count);
    ImGui::PopTextWrapPos();
}

static Vector2 to_world(MapDetailPoint p, float w, float h) { return {((float)p.lon100 / 100.0f / 360.0f) * w, -((float)p.lat100 / 100.0f / 180.0f) * h}; }

void DrawSceneLayers(SceneContext *sctx, AppConfig *cfg)
{
    if (!sctx->is_2d_view || !sctx->camera2d || !ToolSettingGetBool(cfg, COASTLINES_KEY, true)) return;
    Color c = g_theme.ui.text_main; c.a = (unsigned char)(c.a * 0.58f); float width = 1.15f / fmaxf(sctx->camera2d->zoom, 0.10f);
    for (int i = 0; i < MAP_COAST_LINE_COUNT; ++i) { int start = MAP_COAST_LINES[i].start, count = MAP_COAST_LINES[i].count; for (int j = 1; j < count; ++j) { Vector2 a = to_world(MAP_COAST_POINTS[start+j-1], sctx->map_w, sctx->map_h); Vector2 b = to_world(MAP_COAST_POINTS[start+j], sctx->map_w, sctx->map_h); if (fabsf(a.x-b.x) <= sctx->map_w*0.45f) DrawLineEx(a,b,width,c); } }
}

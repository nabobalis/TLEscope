/*
 * tool_layers.cpp - Layers panel
 */

#include "tools.h"
#include "tools_common.h"
#include "core/astro.h"
#include "core/theme.h"
#include "core/config.h"
#include "ui/labels.h"
#include "ui/tools/tools_settings.h"

#include <cmath>
#include <cstdint>
#include <cstdio>
#include <raylib.h>
#include <raymath.h>

#include "imgui.h"
#include "IconsFontAwesome6.h"

static Color DefaultGroundTrackColor(const char *norad_id)
{
    static const Color palette[] = {
        {  31, 119, 180, 255 }, { 255, 127,  14, 255 }, {  44, 160,  44, 255 },
        { 214,  39,  40, 255 }, { 148, 103, 189, 255 }, { 140,  86,  75, 255 },
        { 227, 119, 194, 255 }, { 127, 127, 127, 255 }, { 188, 189,  34, 255 },
        {  23, 190, 207, 255 }, {  57, 106, 177, 255 }, { 218, 124,  48, 255 },
        {  62, 150,  81, 255 }, { 204,  37,  41, 255 }, { 107,  76, 154, 255 },
        { 146,  36,  40, 255 }, { 148, 139,  61, 255 }, { 132,  65,  98, 255 },
        {  64, 170,  98, 255 }, { 145,  39, 143, 255 }, {  36, 121, 108, 255 },
        { 220,  95,  20, 255 }, {  82,  84, 163, 255 }, { 153, 153, 153, 255 }
    };
    uint32_t hash = 2166136261u;
    for (const unsigned char *p = (const unsigned char *)norad_id; p && *p; ++p)
    {
        hash ^= *p;
        hash *= 16777619u;
    }
    return palette[hash % (sizeof(palette) / sizeof(palette[0]))];
}

static void GroundTrackColorKey(const char *norad_id, char *key, size_t key_size)
{
    snprintf(key, key_size, "groundtracks.color.%s", norad_id ? norad_id : "");
}

static Color GroundTrackColor(AppConfig *cfg, const char *norad_id)
{
    Color color = DefaultGroundTrackColor(norad_id);
    char key[64];
    GroundTrackColorKey(norad_id, key, sizeof(key));
    const char *value = ToolSettingGetString(cfg, key, "");
    unsigned int r, g, b;
    if (value && sscanf(value, "#%02x%02x%02x", &r, &g, &b) == 3)
        color = (Color){ (unsigned char)r, (unsigned char)g, (unsigned char)b, 255 };
    return color;
}

void DrawPanelLayers(UIContext *ctx, AppConfig *cfg)
{
    ImGui::PushTextWrapPos(0.0f);
    const float icon_w = 24.0f;

    auto DrawLayerCheckbox = [&](const char *label, bool *value, const char *icon, const char *tooltip) {
        ImGui::PushStyleColor(ImGuiCol_Text, ThemeColor(*value ? g_theme.ui.ui_accent : g_theme.ui.text_secondary));
        ImU32 col = ImGui::GetColorU32(ImGuiCol_Text);
        ImVec2 icon_sz = ImGui::CalcTextSize(icon);
        ImVec2 pos = ImGui::GetCursorScreenPos();
        ImGui::GetWindowDrawList()->AddText(ImVec2(pos.x + (icon_w - icon_sz.x) * 0.5f, pos.y), col, icon);
        ImGui::PopStyleColor();
        ImGui::Dummy(ImVec2(icon_w, ImGui::GetFrameHeight()));
        ImGui::SameLine();
        ImGui::Checkbox(label, value);
        if (tooltip && ImGui::IsItemHovered()) ImGui::SetTooltip("%s", tooltip);
    };

    DrawLayerCheckbox("Clouds", &cfg->show_clouds, ICON_FA_CLOUD, "Show cloud layer (C)");
    DrawLayerCheckbox("Night Lights", &cfg->show_night_lights, ICON_FA_MOON, "Show night-side city lights (N)");
    DrawLayerCheckbox("Markers", &cfg->show_markers, ICON_FA_MAP_PIN, "Show ground markers (L)");
    DrawLayerCheckbox("Scattering", &cfg->show_scattering, ICON_FA_SUN, "Atmospheric scattering effect");
    DrawLayerCheckbox("Skybox", &cfg->show_skybox, ICON_FA_STAR, "Show starfield skybox");
    DrawLayerCheckbox("Highlight Sunlit", &cfg->highlight_sunlit, ICON_FA_BOLT, "Highlight sunlit portions of orbits");
    DrawLayerCheckbox("Slant Range", &cfg->show_slant_range, ICON_FA_RULER, "Show slant range line to home");
    DrawLayerCheckbox("Ground Coverage", &cfg->show_ground_coverage, ICON_FA_ROUTE, "Show the line-of-sight ground coverage footprint");
    DrawLayerCheckbox("Apsides", &cfg->show_apsides, ICON_FA_CIRCLE_DOT, "Show perigee/apogee markers and altitude labels");

    Satellite *selected = ctx && ctx->selected_sat ? *ctx->selected_sat : NULL;
    if (selected && selected->norad_id[0] != '\0')
    {
        ImGui::SeparatorText("Selected Track");
        Color color = GroundTrackColor(cfg, selected->norad_id);
        float rgb[3] = { color.r / 255.0f, color.g / 255.0f, color.b / 255.0f };
        ImGui::TextUnformatted(selected->name);
        if (ImGui::ColorEdit3("Track Color", rgb, ImGuiColorEditFlags_NoAlpha))
        {
            char key[64], value[16];
            GroundTrackColorKey(selected->norad_id, key, sizeof(key));
            snprintf(value, sizeof(value), "#%02X%02X%02X",
                     (int)(rgb[0] * 255.0f + 0.5f),
                     (int)(rgb[1] * 255.0f + 0.5f),
                     (int)(rgb[2] * 255.0f + 0.5f));
            ToolSettingSetString(cfg, key, value);
        }
        if (ImGui::SmallButton("Reset Track Color"))
        {
            char key[64];
            GroundTrackColorKey(selected->norad_id, key, sizeof(key));
            ToolSettingSetString(cfg, key, "");
        }
        if (ImGui::IsItemHovered()) ImGui::SetTooltip("Return this NORAD ID to its deterministic palette color");
    }

    ImGui::Separator();
    bool labels_enabled = ToolSettingGetBool(cfg, LABELS_KEY_ENABLED, true);
    if (ImGui::Checkbox("Labels", &labels_enabled)) ToolSettingSetBool(cfg, LABELS_KEY_ENABLED, labels_enabled);
    if (ImGui::IsItemHovered()) ImGui::SetTooltip("Show name labels for satellites and markers");

    int label_mode = ToolSettingGetInt(cfg, LABELS_KEY_MODE, LABELS_MODE_ACTIVE_ONLY);
    const char *modes[] = { "Active only", "All", "None" };
    ImGui::SetNextItemWidth(-1.0f);
    if (ImGui::Combo("##label_mode", &label_mode, modes, 3)) ToolSettingSetInt(cfg, LABELS_KEY_MODE, label_mode);
    if (ImGui::IsItemHovered()) ImGui::SetTooltip("Which satellites get name labels");

    bool show_alt = ToolSettingGetBool(cfg, LABELS_KEY_ALTITUDE, false);
    if (ImGui::Checkbox("Label Altitude", &show_alt)) ToolSettingSetBool(cfg, LABELS_KEY_ALTITUDE, show_alt);
    if (ImGui::IsItemHovered()) ImGui::SetTooltip("Append current altitude (km) to satellite labels");

    float label_size = ToolSettingGetFloat(cfg, LABELS_KEY_SIZE, 1.0f);
    if (ImGui::SliderFloat("Label Size", &label_size, 0.5f, 1.5f, "%.2fx")) ToolSettingSetFloat(cfg, LABELS_KEY_SIZE, label_size);
    if (ImGui::IsItemHovered()) ImGui::SetTooltip("Scale multiplier on the UI font (1.0x = crisp native size)");

    bool use_bg = ToolSettingGetBool(cfg, LABELS_KEY_BG, true);
    if (ImGui::Checkbox("Label Background", &use_bg)) ToolSettingSetBool(cfg, LABELS_KEY_BG, use_bg);
    if (ImGui::IsItemHovered()) ImGui::SetTooltip("Draw a dark rounded box behind label text for contrast");

    int max_count = ToolSettingGetInt(cfg, LABELS_KEY_MAX_COUNT, 200);
    if (ImGui::SliderInt("Max Labels", &max_count, 10, 1000)) ToolSettingSetInt(cfg, LABELS_KEY_MAX_COUNT, max_count);
    if (ImGui::IsItemHovered()) ImGui::SetTooltip("Declutter cap: how many labels are drawn before overlap rejection kicks in");
    ImGui::PopTextWrapPos();
}

static void DrawFutureTrack2D(const SceneContext *sctx, AppConfig *cfg, Satellite *sat)
{
    if (sat->mean_motion <= 0.0 || cfg->orbits_to_draw <= 0.0f) return;
    int segments = (int)(400.0f * cfg->orbits_to_draw);
    if (segments < 50) segments = 50;
    if (segments > 4000) segments = 4000;

    Vector2 points[4001];
    bool sunlit[4001] = { false };
    const double period_days = (2.0 * PI / sat->mean_motion) / 86400.0;
    const double time_step = (period_days * cfg->orbits_to_draw) / segments;
    const Vector3 sun_dir = cfg->highlight_sunlit
        ? Vector3Normalize(calculate_sun_position(sctx->current_epoch)) : Vector3Zero();

    for (int j = 0; j <= segments; ++j)
    {
        const double t = (j == 0) ? sctx->current_epoch
            : (sctx->current_epoch - fmod(sctx->current_epoch, time_step) + j * time_step);
        const Vector3 raw_pos = calculate_position(sat, get_unix_from_epoch(t));
        get_map_coordinates(raw_pos, epoch_to_gmst(t), sctx->earth_rotation_offset,
                            sctx->map_w, sctx->map_h, &points[j].x, &points[j].y);
        if (cfg->highlight_sunlit) sunlit[j] = !is_sat_eclipsed(raw_pos, sun_dir);
    }

    const Color base_color = GroundTrackColor(cfg, sat->norad_id);
    for (int offset = -1; offset <= 1; ++offset)
    {
        const float x_off = offset * sctx->map_w;
        for (int j = 1; j <= segments; ++j)
        {
            if (fabsf(points[j].x - points[j - 1].x) >= sctx->map_w * 0.6f) continue;
            Color color = (cfg->highlight_sunlit && sunlit[j]) ? g_theme.world.sat_highlighted : base_color;
            DrawLineEx((Vector2){ points[j - 1].x + x_off, points[j - 1].y },
                       (Vector2){ points[j].x + x_off, points[j].y },
                       2.0f / sctx->camera2d->zoom, color);
        }
    }
}

void DrawSceneLayers(SceneContext *sctx, AppConfig *cfg)
{
    if (!sctx->is_2d_view || !sctx->camera2d || sctx->is_pov_mode) return;
    Vector2 map_min = GetWorldToScreen2D((Vector2){ -sctx->map_w / 2.0f, -sctx->map_h / 2.0f }, *sctx->camera2d);
    Vector2 map_max = GetWorldToScreen2D((Vector2){ sctx->map_w / 2.0f, sctx->map_h / 2.0f }, *sctx->camera2d);
    int sc_x = (int)map_min.x, sc_y = (int)map_min.y;
    int sc_w = (int)(map_max.x - map_min.x), sc_h = (int)(map_max.y - map_min.y);
    if (sc_x < 0) { sc_w += sc_x; sc_x = 0; }
    if (sc_y < 0) { sc_h += sc_y; sc_y = 0; }
    if (sc_x + sc_w > GetScreenWidth()) sc_w = GetScreenWidth() - sc_x;
    if (sc_y + sc_h > GetScreenHeight()) sc_h = GetScreenHeight() - sc_y;
    if (sc_w <= 0 || sc_h <= 0) return;

    BeginScissorMode(sc_x, sc_y, sc_w, sc_h);
    for (int i = 0; i < sat_count; ++i)
        if (satellites[i].is_active) DrawFutureTrack2D(sctx, cfg, &satellites[i]);
    EndScissorMode();
}

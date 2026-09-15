/*
 * tool_layers.cpp - Layers panel and 2D map overlays
 */
#include "tools.h"
#include "tools_common.h"
#include "core/astro.h"
#include "core/theme.h"
#include "core/config.h"
#include "ui/labels.h"
#include "ui/ui_layout.h"
#include "ui/tools/tools_settings.h"
#include "map_detail_data.h"

#include <cmath>
#include <cstdint>
#include <cstdio>
#include <cstring>
#include <raylib.h>
#include <raymath.h>

#include "imgui.h"
#include "IconsFontAwesome6.h"

static const char *PAST_ORBITS_KEY = "groundtracks.past_orbits";
static const char *TRACK_LEGEND_KEY = "groundtracks.legend";
static const char *COASTLINES_KEY = "map2d.coastlines";
static const char *BORDERS_KEY = "map2d.country_borders";
static const char *GRID_KEY = "map2d.latlon_grid";

#define TRACK_CACHE_SLOTS 64
#define TRACK_CACHE_MAX_POINTS 4001
#define TRACK_CACHE_SIM_SECONDS 3.0
#define TRACK_CACHE_MIN_REAL_SECONDS 0.5

typedef struct {
    bool valid;
    int sat_index;
    int past_orbits;
    float future_orbits;
    int samples_per_orbit;
    int past_segments;
    int future_segments;
    int segments;
    bool highlight_sunlit;
    float earth_rotation_offset;
    float map_w;
    float map_h;
    double sat_epoch_unix;
    double mean_motion;
    double center_epoch;
    double last_build_wall;
    unsigned long last_used;
    Vector2 points[TRACK_CACHE_MAX_POINTS];
    unsigned char sunlit[TRACK_CACHE_MAX_POINTS];
} GroundTrackCache;

static GroundTrackCache s_track_cache[TRACK_CACHE_SLOTS] = {};
static unsigned long s_track_cache_clock = 0;

static Color DefaultGroundTrackColor(const char *norad_id)
{
    static const Color palette[] = {
        {31,119,180,255}, {255,127,14,255}, {44,160,44,255}, {214,39,40,255},
        {148,103,189,255}, {140,86,75,255}, {227,119,194,255}, {127,127,127,255},
        {188,189,34,255}, {23,190,207,255}, {57,106,177,255}, {218,124,48,255},
        {62,150,81,255}, {204,37,41,255}, {107,76,154,255}, {146,36,40,255},
        {148,139,61,255}, {132,65,98,255}, {64,170,98,255}, {145,39,143,255},
        {36,121,108,255}, {220,95,20,255}, {82,84,163,255}, {153,153,153,255}
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
        color = (Color){(unsigned char)r, (unsigned char)g, (unsigned char)b, 255};
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
    DrawLayerCheckbox("Highlight Sunlit", &cfg->highlight_sunlit, ICON_FA_BOLT, "Highlight sunlit portions of ground tracks");
    DrawLayerCheckbox("Slant Range", &cfg->show_slant_range, ICON_FA_RULER, "Show slant range line to home");
    DrawLayerCheckbox("Ground Coverage", &cfg->show_ground_coverage, ICON_FA_ROUTE, "Show the line-of-sight ground coverage footprint");
    DrawLayerCheckbox("Apsides", &cfg->show_apsides, ICON_FA_CIRCLE_DOT, "Show perigee/apogee markers and altitude labels");

    ImGui::SeparatorText("2D Map");
    float future_orbits = cfg->orbits_to_draw;
    if (ImGui::SliderFloat("Future Orbits", &future_orbits, 0.25f, 10.0f, "%.2f"))
        cfg->orbits_to_draw = future_orbits;
    int past_orbits = ToolSettingGetInt(cfg, PAST_ORBITS_KEY, 1);
    if (ImGui::SliderInt("Past Orbits", &past_orbits, 0, 10))
        ToolSettingSetInt(cfg, PAST_ORBITS_KEY, past_orbits);

    bool legend_enabled = ToolSettingGetBool(cfg, TRACK_LEGEND_KEY, true);
    if (ImGui::Checkbox("Track Legend", &legend_enabled)) ToolSettingSetBool(cfg, TRACK_LEGEND_KEY, legend_enabled);
    bool coastlines = ToolSettingGetBool(cfg, COASTLINES_KEY, true);
    if (ImGui::Checkbox("Coastlines", &coastlines)) ToolSettingSetBool(cfg, COASTLINES_KEY, coastlines);
    bool borders = ToolSettingGetBool(cfg, BORDERS_KEY, false);
    if (ImGui::Checkbox("Country Borders", &borders)) ToolSettingSetBool(cfg, BORDERS_KEY, borders);
    bool grid = ToolSettingGetBool(cfg, GRID_KEY, false);
    if (ImGui::Checkbox("Lat/Lon Grid", &grid)) ToolSettingSetBool(cfg, GRID_KEY, grid);

    Satellite *selected = ctx && ctx->selected_sat ? *ctx->selected_sat : NULL;
    if (selected && selected->norad_id[0])
    {
        ImGui::SeparatorText("Selected Track");
        Color color = GroundTrackColor(cfg, selected->norad_id);
        float rgb[3] = {color.r / 255.0f, color.g / 255.0f, color.b / 255.0f};
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
    }

    ImGui::TextColored(ThemeColor(g_theme.ui.text_secondary), "Press H for clean view");
    ImGui::Separator();

    bool labels_enabled = ToolSettingGetBool(cfg, LABELS_KEY_ENABLED, true);
    if (ImGui::Checkbox("Labels", &labels_enabled)) ToolSettingSetBool(cfg, LABELS_KEY_ENABLED, labels_enabled);
    int label_mode = ToolSettingGetInt(cfg, LABELS_KEY_MODE, LABELS_MODE_ACTIVE_ONLY);
    const char *modes[] = {"Active only", "All", "None"};
    ImGui::SetNextItemWidth(-1.0f);
    if (ImGui::Combo("##label_mode", &label_mode, modes, 3)) ToolSettingSetInt(cfg, LABELS_KEY_MODE, label_mode);
    bool show_alt = ToolSettingGetBool(cfg, LABELS_KEY_ALTITUDE, false);
    if (ImGui::Checkbox("Label Altitude", &show_alt)) ToolSettingSetBool(cfg, LABELS_KEY_ALTITUDE, show_alt);
    float label_size = ToolSettingGetFloat(cfg, LABELS_KEY_SIZE, 1.0f);
    if (ImGui::SliderFloat("Label Size", &label_size, 0.5f, 1.5f, "%.2fx")) ToolSettingSetFloat(cfg, LABELS_KEY_SIZE, label_size);
    bool use_bg = ToolSettingGetBool(cfg, LABELS_KEY_BG, true);
    if (ImGui::Checkbox("Label Background", &use_bg)) ToolSettingSetBool(cfg, LABELS_KEY_BG, use_bg);
    int max_count = ToolSettingGetInt(cfg, LABELS_KEY_MAX_COUNT, 200);
    if (ImGui::SliderInt("Max Labels", &max_count, 10, 1000)) ToolSettingSetInt(cfg, LABELS_KEY_MAX_COUNT, max_count);
    ImGui::PopTextWrapPos();
}

static int SamplesPerOrbit(float zoom)
{
    if (zoom < 0.80f) return 60;
    if (zoom > 1.80f) return 180;
    return 120;
}

static GroundTrackCache *AcquireTrackCache(Satellite *sat)
{
    int sat_index = (int)(sat - satellites);
    GroundTrackCache *slot = NULL;
    for (int i = 0; i < TRACK_CACHE_SLOTS; ++i)
        if (s_track_cache[i].valid && s_track_cache[i].sat_index == sat_index) { slot = &s_track_cache[i]; break; }
    if (!slot)
        for (int i = 0; i < TRACK_CACHE_SLOTS; ++i)
            if (!s_track_cache[i].valid) { slot = &s_track_cache[i]; break; }
    if (!slot)
    {
        int oldest = 0;
        for (int i = 1; i < TRACK_CACHE_SLOTS; ++i)
            if (s_track_cache[i].last_used < s_track_cache[oldest].last_used) oldest = i;
        slot = &s_track_cache[oldest];
    }
    if (!slot->valid || slot->sat_index != sat_index)
    {
        memset(slot, 0, sizeof(*slot));
        slot->sat_index = sat_index;
    }
    slot->last_used = ++s_track_cache_clock;
    return slot;
}

static GroundTrackCache *GetTrackCache(const SceneContext *sctx, AppConfig *cfg,
                                       Satellite *sat, int past_orbits)
{
    GroundTrackCache *cache = AcquireTrackCache(sat);
    int samples = SamplesPerOrbit(sctx->camera2d->zoom);
    int past_segments = past_orbits * samples;
    int future_segments = (int)ceilf(cfg->orbits_to_draw * samples);
    int segments = past_segments + future_segments;
    if (segments > TRACK_CACHE_MAX_POINTS - 1) segments = TRACK_CACHE_MAX_POINTS - 1;
    if (past_segments > segments) past_segments = segments;
    future_segments = segments - past_segments;

    double sim_delta = cache->valid ? fabs(sctx->current_epoch - cache->center_epoch) * 86400.0 : 1e30;
    double real_delta = cache->valid ? GetTime() - cache->last_build_wall : 1e30;
    bool structure_changed = !cache->valid || cache->past_orbits != past_orbits ||
        cache->future_orbits != cfg->orbits_to_draw || cache->samples_per_orbit != samples ||
        cache->highlight_sunlit != cfg->highlight_sunlit || cache->map_w != sctx->map_w ||
        cache->map_h != sctx->map_h || cache->earth_rotation_offset != sctx->earth_rotation_offset ||
        cache->sat_epoch_unix != sat->epoch_unix || cache->mean_motion != sat->mean_motion;

    if (structure_changed || (sim_delta >= TRACK_CACHE_SIM_SECONDS && real_delta >= TRACK_CACHE_MIN_REAL_SECONDS))
    {
        cache->past_orbits = past_orbits;
        cache->future_orbits = cfg->orbits_to_draw;
        cache->samples_per_orbit = samples;
        cache->past_segments = past_segments;
        cache->future_segments = future_segments;
        cache->segments = segments;
        cache->highlight_sunlit = cfg->highlight_sunlit;
        cache->earth_rotation_offset = sctx->earth_rotation_offset;
        cache->map_w = sctx->map_w;
        cache->map_h = sctx->map_h;
        cache->sat_epoch_unix = sat->epoch_unix;
        cache->mean_motion = sat->mean_motion;
        cache->center_epoch = sctx->current_epoch;
        cache->last_build_wall = GetTime();

        const double period_days = (2.0 * PI / sat->mean_motion) / 86400.0;
        const double step = period_days / samples;
        Vector3 sun_dir = cfg->highlight_sunlit
            ? Vector3Normalize(calculate_sun_position(sctx->current_epoch)) : Vector3Zero();
        for (int j = 0; j <= segments; ++j)
        {
            int offset_segments = j - past_segments;
            double t = sctx->current_epoch + offset_segments * step;
            Vector3 raw = calculate_position(sat, get_unix_from_epoch(t));
            get_map_coordinates(raw, epoch_to_gmst(t), sctx->earth_rotation_offset,
                                sctx->map_w, sctx->map_h,
                                &cache->points[j].x, &cache->points[j].y);
            cache->sunlit[j] = cfg->highlight_sunlit ? !is_sat_eclipsed(raw, sun_dir) : 1;
        }
        cache->valid = true;
    }
    return cache;
}

static Color WithAlpha(Color c, float alpha)
{
    c.a = (unsigned char)fmaxf(0.0f, fminf(255.0f, c.a * alpha));
    return c;
}

static void DrawSatelliteTracks(const SceneContext *sctx, AppConfig *cfg,
                                Satellite *sat, int past_orbits)
{
    if (sat->mean_motion <= 0.0) return;
    GroundTrackCache *cache = GetTrackCache(sctx, cfg, sat, past_orbits);
    Color base = GroundTrackColor(cfg, sat->norad_id);
    const float width = (sat == sctx->active_sat ? 2.6f : 1.7f) /
                        fmaxf(sctx->camera2d->zoom, 0.10f);

    for (int offset = -1; offset <= 1; ++offset)
    {
        float x_off = offset * sctx->map_w;
        for (int j = 1; j <= cache->segments; ++j)
        {
            bool is_past = j <= cache->past_segments;
            if (is_past && j != cache->past_segments && ((j / 3) % 2) != 0) continue;
            if (fabsf(cache->points[j].x - cache->points[j - 1].x) >= sctx->map_w * 0.6f) continue;
            float alpha = is_past ? 0.45f : 0.95f;
            if (cfg->highlight_sunlit && !cache->sunlit[j]) alpha *= 0.45f;
            DrawLineEx((Vector2){cache->points[j - 1].x + x_off, cache->points[j - 1].y},
                       (Vector2){cache->points[j].x + x_off, cache->points[j].y},
                       width, WithAlpha(base, alpha));
        }
    }
}

static Vector2 MapDetailToWorld(MapDetailPoint p, float map_w, float map_h)
{
    return (Vector2){((float)p.lon100 / 100.0f / 360.0f) * map_w,
                     -((float)p.lat100 / 100.0f / 180.0f) * map_h};
}

static void DrawMapLines(const MapDetailPoint *points, const MapDetailLine *lines,
                         int line_count, const SceneContext *sctx,
                         float width_px, Color color)
{
    float width = width_px / fmaxf(sctx->camera2d->zoom, 0.10f);
    for (int i = 0; i < line_count; ++i)
    {
        int start = lines[i].start;
        int count = lines[i].count;
        for (int j = 1; j < count; ++j)
        {
            Vector2 a = MapDetailToWorld(points[start + j - 1], sctx->map_w, sctx->map_h);
            Vector2 b = MapDetailToWorld(points[start + j], sctx->map_w, sctx->map_h);
            if (fabsf(a.x - b.x) > sctx->map_w * 0.45f) continue;
            DrawLineEx(a, b, width, color);
        }
    }
}

static void DrawMapDetails(const SceneContext *sctx, AppConfig *cfg)
{
    if (ToolSettingGetBool(cfg, GRID_KEY, false))
    {
        float zoom = fmaxf(sctx->camera2d->zoom, 0.10f);
        Color thin_c = WithAlpha(g_theme.ui.text_main, 0.15f);
        Color strong_c = WithAlpha(g_theme.ui.text_main, 0.28f);
        for (int lon = -150; lon <= 150; lon += 30)
        {
            float x = ((float)lon / 360.0f) * sctx->map_w;
            DrawLineEx((Vector2){x, -sctx->map_h * 0.5f}, (Vector2){x, sctx->map_h * 0.5f},
                       (lon == 0 ? 1.1f : 0.8f) / zoom, lon == 0 ? strong_c : thin_c);
        }
        for (int lat = -60; lat <= 60; lat += 30)
        {
            float y = -((float)lat / 180.0f) * sctx->map_h;
            DrawLineEx((Vector2){-sctx->map_w * 0.5f, y}, (Vector2){sctx->map_w * 0.5f, y},
                       (lat == 0 ? 1.1f : 0.8f) / zoom, lat == 0 ? strong_c : thin_c);
        }
    }
    if (ToolSettingGetBool(cfg, BORDERS_KEY, false))
        DrawMapLines(MAP_BORDER_POINTS, MAP_BORDER_LINES, MAP_BORDER_LINE_COUNT,
                     sctx, 0.8f, WithAlpha(g_theme.ui.text_main, 0.20f));
    if (ToolSettingGetBool(cfg, COASTLINES_KEY, true))
        DrawMapLines(MAP_COAST_POINTS, MAP_COAST_LINES, MAP_COAST_LINE_COUNT,
                     sctx, 1.15f, WithAlpha(g_theme.ui.text_main, 0.58f));
}

static void DrawTrackLegend(const SceneContext *sctx, int sc_x, int sc_y)
{
    float iz = 1.0f / sctx->camera2d->zoom;
    Vector2 tl = GetScreenToWorld2D((Vector2){(float)sc_x + 12.0f, (float)sc_y + 12.0f}, *sctx->camera2d);
    Rectangle box = {tl.x, tl.y, 154.0f * iz, 68.0f * iz};
    Color bg = g_theme.world.bg; bg.a = 205;
    DrawRectangleRec(box, bg);
    DrawRectangleLinesEx(box, iz, g_theme.ui.window_border);
    float x1 = tl.x + 9.0f * iz, x2 = x1 + 30.0f * iz, tx = x2 + 8.0f * iz;
    float y = tl.y + 14.0f * iz, fs = 12.0f * iz;
    Color future = g_theme.world.orbit_normal;
    Color past = WithAlpha(future, 0.45f);
    for (int d = 0; d < 4; ++d)
        DrawLineEx((Vector2){x1 + d * 8.0f * iz, y}, (Vector2){x1 + d * 8.0f * iz + 4.0f * iz, y}, 2.0f * iz, past);
    DrawTextEx(GetFontDefault(), "Past", (Vector2){tx, y - 6.0f * iz}, fs, iz, g_theme.ui.text_main);
    y += 18.0f * iz;
    DrawCircleV((Vector2){(x1 + x2) * 0.5f, y}, 3.5f * iz, g_theme.world.sat_highlighted);
    DrawTextEx(GetFontDefault(), "Current", (Vector2){tx, y - 6.0f * iz}, fs, iz, g_theme.ui.text_main);
    y += 18.0f * iz;
    DrawLineEx((Vector2){x1, y}, (Vector2){x2, y}, 2.0f * iz, future);
    DrawTextEx(GetFontDefault(), "Future", (Vector2){tx, y - 6.0f * iz}, fs, iz, g_theme.ui.text_main);
}

static void HandleCleanView(void)
{
    static bool clean = false;
    static bool saved_left = true, saved_right = true, saved_bottom = true;
    if (ImGui::GetIO().WantTextInput || !IsKeyPressed(KEY_H)) return;
    clean = !clean;
    if (clean)
    {
        saved_left = LayoutSidebarVisible(SIDEBAR_LEFT);
        saved_right = LayoutSidebarVisible(SIDEBAR_RIGHT);
        saved_bottom = LayoutBottomBarVisible();
        LayoutSetSidebarVisible(SIDEBAR_LEFT, false);
        LayoutSetSidebarVisible(SIDEBAR_RIGHT, false);
        LayoutSetBottomBarVisible(false);
    }
    else
    {
        LayoutSetSidebarVisible(SIDEBAR_LEFT, saved_left);
        LayoutSetSidebarVisible(SIDEBAR_RIGHT, saved_right);
        LayoutSetBottomBarVisible(saved_bottom);
    }
}

void DrawSceneLayers(SceneContext *sctx, AppConfig *cfg)
{
    HandleCleanView();
    if (!sctx->is_2d_view || !sctx->camera2d || sctx->is_pov_mode) return;

    Vector2 mn = GetWorldToScreen2D((Vector2){-sctx->map_w / 2.0f, -sctx->map_h / 2.0f}, *sctx->camera2d);
    Vector2 mx = GetWorldToScreen2D((Vector2){ sctx->map_w / 2.0f,  sctx->map_h / 2.0f}, *sctx->camera2d);
    int x = (int)mn.x, y = (int)mn.y, w = (int)(mx.x - mn.x), h = (int)(mx.y - mn.y);
    if (x < 0) { w += x; x = 0; }
    if (y < 0) { h += y; y = 0; }
    if (x + w > GetScreenWidth()) w = GetScreenWidth() - x;
    if (y + h > GetScreenHeight()) h = GetScreenHeight() - y;
    if (w <= 0 || h <= 0) return;

    BeginScissorMode(x, y, w, h);
    DrawMapDetails(sctx, cfg);
    int past_orbits = ToolSettingGetInt(cfg, PAST_ORBITS_KEY, 1);
    if (past_orbits < 0) past_orbits = 0;
    if (past_orbits > 10) past_orbits = 10;
    for (int i = 0; i < sat_count; ++i)
        if (satellites[i].is_active)
            DrawSatelliteTracks(sctx, cfg, &satellites[i], past_orbits);
    if (ToolSettingGetBool(cfg, TRACK_LEGEND_KEY, true))
        DrawTrackLegend(sctx, x, y);
    EndScissorMode();
}

/* tool_layers.cpp - Layers panel */
#include "tools.h"
#include "tools_common.h"
#include "core/astro.h"
#include "core/theme.h"
#include "core/config.h"
#include "ui/labels.h"
#include "ui/tools/tools_settings.h"
#include <cmath>
#include <cstring>
#include <raylib.h>
#include <raymath.h>
#include "imgui.h"
#include "IconsFontAwesome6.h"

#define TRACK_CACHE_SLOTS 64
#define TRACK_CACHE_MAX_POINTS 4001
#define TRACK_CACHE_SIM_SECONDS 3.0
#define TRACK_CACHE_MIN_REAL_SECONDS 0.5

typedef struct {
    bool valid;
    int sat_index;
    int segments;
    float orbits;
    float map_w, map_h;
    float earth_rotation_offset;
    bool highlight_sunlit;
    double center_epoch;
    double last_build_wall;
    double sat_epoch_unix;
    double mean_motion;
    unsigned long last_used;
    Vector2 points[TRACK_CACHE_MAX_POINTS];
    unsigned char sunlit[TRACK_CACHE_MAX_POINTS];
} TrackCache;

static TrackCache s_track_cache[TRACK_CACHE_SLOTS] = {};
static unsigned long s_cache_clock = 0;

void DrawPanelLayers(UIContext *ctx, AppConfig *cfg)
{
    (void)ctx;
    ImGui::PushTextWrapPos(0.0f);
    const float icon_w = 24.0f;
    auto DrawLayerCheckbox = [&](const char *label, bool *value, const char *icon, const char *tooltip) {
        ImGui::PushStyleColor(ImGuiCol_Text, ThemeColor(*value ? g_theme.ui.ui_accent : g_theme.ui.text_secondary));
        ImU32 col = ImGui::GetColorU32(ImGuiCol_Text); ImVec2 icon_sz = ImGui::CalcTextSize(icon); ImVec2 pos = ImGui::GetCursorScreenPos();
        ImGui::GetWindowDrawList()->AddText(ImVec2(pos.x + (icon_w - icon_sz.x) * 0.5f, pos.y), col, icon); ImGui::PopStyleColor();
        ImGui::Dummy(ImVec2(icon_w, ImGui::GetFrameHeight())); ImGui::SameLine(); ImGui::Checkbox(label, value);
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
    ImGui::Separator();
    bool labels_enabled = ToolSettingGetBool(cfg, LABELS_KEY_ENABLED, true); if (ImGui::Checkbox("Labels", &labels_enabled)) ToolSettingSetBool(cfg, LABELS_KEY_ENABLED, labels_enabled);
    int label_mode = ToolSettingGetInt(cfg, LABELS_KEY_MODE, LABELS_MODE_ACTIVE_ONLY); const char *modes[] = {"Active only", "All", "None"}; ImGui::SetNextItemWidth(-1.0f); if (ImGui::Combo("##label_mode", &label_mode, modes, 3)) ToolSettingSetInt(cfg, LABELS_KEY_MODE, label_mode);
    bool show_alt = ToolSettingGetBool(cfg, LABELS_KEY_ALTITUDE, false); if (ImGui::Checkbox("Label Altitude", &show_alt)) ToolSettingSetBool(cfg, LABELS_KEY_ALTITUDE, show_alt);
    float label_size = ToolSettingGetFloat(cfg, LABELS_KEY_SIZE, 1.0f); if (ImGui::SliderFloat("Label Size", &label_size, 0.5f, 1.5f, "%.2fx")) ToolSettingSetFloat(cfg, LABELS_KEY_SIZE, label_size);
    bool use_bg = ToolSettingGetBool(cfg, LABELS_KEY_BG, true); if (ImGui::Checkbox("Label Background", &use_bg)) ToolSettingSetBool(cfg, LABELS_KEY_BG, use_bg);
    int max_count = ToolSettingGetInt(cfg, LABELS_KEY_MAX_COUNT, 200); if (ImGui::SliderInt("Max Labels", &max_count, 10, 1000)) ToolSettingSetInt(cfg, LABELS_KEY_MAX_COUNT, max_count);
    ImGui::PopTextWrapPos();
}

static int SamplesPerOrbit(float zoom)
{
    if (zoom < 0.8f) return 60;
    if (zoom > 1.8f) return 180;
    return 120;
}

static TrackCache *AcquireCache(Satellite *sat)
{
    int sat_index = (int)(sat - satellites);
    TrackCache *slot = NULL;
    for (int i = 0; i < TRACK_CACHE_SLOTS; ++i) if (s_track_cache[i].valid && s_track_cache[i].sat_index == sat_index) { slot = &s_track_cache[i]; break; }
    if (!slot) for (int i = 0; i < TRACK_CACHE_SLOTS; ++i) if (!s_track_cache[i].valid) { slot = &s_track_cache[i]; break; }
    if (!slot) { int oldest = 0; for (int i = 1; i < TRACK_CACHE_SLOTS; ++i) if (s_track_cache[i].last_used < s_track_cache[oldest].last_used) oldest = i; slot = &s_track_cache[oldest]; }
    if (!slot->valid || slot->sat_index != sat_index) { memset(slot, 0, sizeof(*slot)); slot->sat_index = sat_index; }
    slot->last_used = ++s_cache_clock;
    return slot;
}

static TrackCache *GetTrackCache(const SceneContext *sctx, const AppConfig *cfg, Satellite *sat)
{
    TrackCache *cache = AcquireCache(sat);
    int segments = (int)ceilf(cfg->orbits_to_draw * SamplesPerOrbit(sctx->camera2d->zoom));
    if (segments < 50) segments = 50;
    if (segments > 4000) segments = 4000;
    double sim_delta = cache->valid ? fabs(sctx->current_epoch - cache->center_epoch) * 86400.0 : 1e30;
    double real_delta = cache->valid ? GetTime() - cache->last_build_wall : 1e30;
    bool structure_changed = !cache->valid || cache->segments != segments || cache->orbits != cfg->orbits_to_draw || cache->map_w != sctx->map_w || cache->map_h != sctx->map_h || cache->earth_rotation_offset != sctx->earth_rotation_offset || cache->highlight_sunlit != cfg->highlight_sunlit || cache->sat_epoch_unix != sat->epoch_unix || cache->mean_motion != sat->mean_motion;
    if (structure_changed || (sim_delta >= TRACK_CACHE_SIM_SECONDS && real_delta >= TRACK_CACHE_MIN_REAL_SECONDS))
    {
        cache->segments = segments; cache->orbits = cfg->orbits_to_draw; cache->map_w = sctx->map_w; cache->map_h = sctx->map_h; cache->earth_rotation_offset = sctx->earth_rotation_offset; cache->highlight_sunlit = cfg->highlight_sunlit; cache->sat_epoch_unix = sat->epoch_unix; cache->mean_motion = sat->mean_motion; cache->center_epoch = sctx->current_epoch; cache->last_build_wall = GetTime();
        double period_days = (2.0 * PI / sat->mean_motion) / 86400.0; double step = (period_days * cfg->orbits_to_draw) / segments;
        Vector3 sun_dir = cfg->highlight_sunlit ? Vector3Normalize(calculate_sun_position(sctx->current_epoch)) : Vector3Zero();
        for (int j = 0; j <= segments; ++j) { double t = sctx->current_epoch + j * step; Vector3 raw = calculate_position(sat, get_unix_from_epoch(t)); get_map_coordinates(raw, epoch_to_gmst(t), sctx->earth_rotation_offset, sctx->map_w, sctx->map_h, &cache->points[j].x, &cache->points[j].y); cache->sunlit[j] = cfg->highlight_sunlit ? !is_sat_eclipsed(raw, sun_dir) : 1; }
        cache->valid = true;
    }
    return cache;
}

static void DrawFutureTrack2D(const SceneContext *sctx, const AppConfig *cfg, Satellite *sat)
{
    if (sat->mean_motion <= 0.0 || cfg->orbits_to_draw <= 0.0f) return;
    TrackCache *cache = GetTrackCache(sctx, cfg, sat);
    for (int offset = -1; offset <= 1; ++offset) { float x_off = offset * sctx->map_w; for (int j = 1; j <= cache->segments; ++j) { if (fabsf(cache->points[j].x - cache->points[j-1].x) >= sctx->map_w * 0.6f) continue; Color color = (cfg->highlight_sunlit && cache->sunlit[j]) ? g_theme.world.sat_highlighted : g_theme.world.orbit_normal; DrawLineEx((Vector2){cache->points[j-1].x+x_off, cache->points[j-1].y}, (Vector2){cache->points[j].x+x_off, cache->points[j].y}, 2.0f / sctx->camera2d->zoom, color); } }
}

void DrawSceneLayers(SceneContext *sctx, AppConfig *cfg)
{
    if (!sctx->is_2d_view || !sctx->camera2d || sctx->is_pov_mode) return;
    Vector2 mn = GetWorldToScreen2D((Vector2){-sctx->map_w/2.0f,-sctx->map_h/2.0f}, *sctx->camera2d); Vector2 mx = GetWorldToScreen2D((Vector2){sctx->map_w/2.0f,sctx->map_h/2.0f}, *sctx->camera2d);
    int x=(int)mn.x,y=(int)mn.y,w=(int)(mx.x-mn.x),h=(int)(mx.y-mn.y); if(x<0){w+=x;x=0;} if(y<0){h+=y;y=0;} if(x+w>GetScreenWidth())w=GetScreenWidth()-x; if(y+h>GetScreenHeight())h=GetScreenHeight()-y; if(w<=0||h<=0)return;
    BeginScissorMode(x,y,w,h); for(int i=0;i<sat_count;++i){Satellite *sat=&satellites[i]; if(!sat->is_active || sat==sctx->active_sat) continue; DrawFutureTrack2D(sctx,cfg,sat);} EndScissorMode();
}

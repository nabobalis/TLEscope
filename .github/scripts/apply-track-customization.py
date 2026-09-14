from pathlib import Path
import re


def replace_once(path, old, new):
    p = Path(path)
    text = p.read_text()
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{path}: expected one match, found {count}: {old[:100]!r}")
    p.write_text(text.replace(old, new, 1))


def regex_once(path, pattern, replacement):
    p = Path(path)
    text = p.read_text()
    new_text, count = re.subn(pattern, replacement, text, count=1, flags=re.S)
    if count != 1:
        raise RuntimeError(f"{path}: expected one regex match, found {count}")
    p.write_text(new_text)


# types.h --------------------------------------------------------------------
replace_once("src/types.h", "#define MAX_CUSTOM_TLE_SOURCES 20\n", "#define MAX_CUSTOM_TLE_SOURCES 20\n#define MAX_MISSION_TRACK_COLORS 64\n")
replace_once(
    "src/types.h",
    "typedef struct\n{\n    char name[64];\n    char url[256];\n    bool selected;\n} CustomTLESource;\n",
    "typedef struct\n{\n    char name[64];\n    char url[256];\n    bool selected;\n} CustomTLESource;\n\ntypedef struct\n{\n    char norad_id[8];\n    Color color;\n} MissionTrackColor;\n",
)
replace_once(
    "src/types.h",
    "    float earth_rotation_offset;\n    float orbits_to_draw;\n",
    "    float earth_rotation_offset;\n    float orbits_to_draw;\n    int groundtrack_past_orbits;\n    int groundtrack_future_orbits;\n    bool show_2d_mission_labels;\n    bool show_2d_footprints;\n",
)
replace_once(
    "src/types.h",
    "    char manual_tles[MAX_MANUAL_TLES][512];\n    int manual_tle_count;\n",
    "    char manual_tles[MAX_MANUAL_TLES][512];\n    int manual_tle_count;\n\n    MissionTrackColor mission_track_colors[MAX_MISSION_TRACK_COLORS];\n    int mission_track_color_count;\n",
)

# config.h -------------------------------------------------------------------
replace_once(
    "src/config.h",
    "void SaveAppConfig(const char *filename, AppConfig *config);\n",
    "void SaveAppConfig(const char *filename, AppConfig *config);\n\nint GetMissionTrackPaletteSize(void);\nColor GetMissionTrackPaletteColor(int index);\nColor GetMissionTrackColor(const AppConfig *config, const char *norad_id);\nvoid SetMissionTrackColor(AppConfig *config, const char *norad_id, Color color);\nvoid ResetMissionTrackColor(AppConfig *config, const char *norad_id);\n",
)

# config.c -------------------------------------------------------------------
replace_once(
    "src/config.c",
    "    return (Color){(unsigned char)r, (unsigned char)g, (unsigned char)b, (unsigned char)a};\n}\n\nstatic bool ParseJsonBool",
    r'''    return (Color){(unsigned char)r, (unsigned char)g, (unsigned char)b, (unsigned char)a};
}

static const Color MISSION_TRACK_PALETTE[] = {
    {  0, 174, 239, 255}, {255, 153,   0, 255}, {  0, 204, 136, 255},
    {238, 102, 119, 255}, {187, 119, 255, 255}, {255, 221,  87, 255},
    { 86, 180, 233, 255}, {230, 159,   0, 255}, {  0, 158, 115, 255},
    {213,  94,   0, 255}, {204, 121, 167, 255}, {120, 220, 120, 255}
};

static void NormalizeNoradId(const char *src, char out[8])
{
    int j = 0;
    if (src)
    {
        for (int i = 0; i < 7 && src[i] && j < 7; i++)
        {
            if (isdigit((unsigned char)src[i])) out[j++] = src[i];
            else if (j > 0) break;
        }
    }
    out[j] = '\0';
}

int GetMissionTrackPaletteSize(void)
{
    return (int)(sizeof(MISSION_TRACK_PALETTE) / sizeof(MISSION_TRACK_PALETTE[0]));
}

Color GetMissionTrackPaletteColor(int index)
{
    int count = GetMissionTrackPaletteSize();
    if (count <= 0) return WHITE;
    index %= count;
    if (index < 0) index += count;
    return MISSION_TRACK_PALETTE[index];
}

Color GetMissionTrackColor(const AppConfig *config, const char *norad_id)
{
    char normalized[8] = {0};
    NormalizeNoradId(norad_id, normalized);
    if (config)
    {
        for (int i = 0; i < config->mission_track_color_count; i++)
            if (strcmp(config->mission_track_colors[i].norad_id, normalized) == 0)
                return config->mission_track_colors[i].color;
    }
    unsigned long id = strtoul(normalized, NULL, 10);
    return GetMissionTrackPaletteColor((int)(id % (unsigned long)GetMissionTrackPaletteSize()));
}

void SetMissionTrackColor(AppConfig *config, const char *norad_id, Color color)
{
    if (!config) return;
    char normalized[8] = {0};
    NormalizeNoradId(norad_id, normalized);
    if (!normalized[0]) return;
    for (int i = 0; i < config->mission_track_color_count; i++)
    {
        if (strcmp(config->mission_track_colors[i].norad_id, normalized) == 0)
        {
            config->mission_track_colors[i].color = color;
            return;
        }
    }
    if (config->mission_track_color_count >= MAX_MISSION_TRACK_COLORS) return;
    MissionTrackColor *entry = &config->mission_track_colors[config->mission_track_color_count++];
    strncpy(entry->norad_id, normalized, sizeof(entry->norad_id) - 1);
    entry->norad_id[sizeof(entry->norad_id) - 1] = '\0';
    entry->color = color;
}

void ResetMissionTrackColor(AppConfig *config, const char *norad_id)
{
    if (!config) return;
    char normalized[8] = {0};
    NormalizeNoradId(norad_id, normalized);
    for (int i = 0; i < config->mission_track_color_count; i++)
    {
        if (strcmp(config->mission_track_colors[i].norad_id, normalized) == 0)
        {
            for (int j = i; j < config->mission_track_color_count - 1; j++)
                config->mission_track_colors[j] = config->mission_track_colors[j + 1];
            config->mission_track_color_count--;
            return;
        }
    }
}

static bool ParseJsonBool''',
)
replace_once(
    "src/config.c",
    "    config->custom_tle_source_count = 0;\n",
    "    config->custom_tle_source_count = 0;\n    config->mission_track_color_count = 0;\n    config->groundtrack_past_orbits = 1;\n    config->groundtrack_future_orbits = 2;\n    config->show_2d_mission_labels = true;\n    config->show_2d_footprints = false;\n",
)
replace_once(
    "src/config.c",
    "            PARSE_FLOAT(\"earth_rotation_offset\", earth_rotation_offset);\n            PARSE_FLOAT(\"orbits_to_draw\", orbits_to_draw);\n",
    "            PARSE_FLOAT(\"earth_rotation_offset\", earth_rotation_offset);\n            PARSE_FLOAT(\"orbits_to_draw\", orbits_to_draw);\n            PARSE_INT(\"groundtrack_past_orbits\", groundtrack_past_orbits);\n            PARSE_INT(\"groundtrack_future_orbits\", groundtrack_future_orbits);\n            if (config->groundtrack_past_orbits < 0) config->groundtrack_past_orbits = 0;\n            if (config->groundtrack_past_orbits > 10) config->groundtrack_past_orbits = 10;\n            if (config->groundtrack_future_orbits < 0) config->groundtrack_future_orbits = 0;\n            if (config->groundtrack_future_orbits > 10) config->groundtrack_future_orbits = 10;\n",
)
replace_once(
    "src/config.c",
    "            config->show_first_run_dialog = ParseJsonBool(text, \"show_first_run_dialog\", config->show_first_run_dialog);\n",
    "            config->show_first_run_dialog = ParseJsonBool(text, \"show_first_run_dialog\", config->show_first_run_dialog);\n            config->show_2d_mission_labels = ParseJsonBool(text, \"show_2d_mission_labels\", config->show_2d_mission_labels);\n            config->show_2d_footprints = ParseJsonBool(text, \"show_2d_footprints\", config->show_2d_footprints);\n",
)
replace_once(
    "src/config.c",
    "            // load home location\n",
    r'''            // load per-mission 2D ground-track color overrides
            char *mc_ptr = strstr(text, "\"mission_track_colors\"");
            if (mc_ptr)
            {
                char *array_start = strchr(mc_ptr, '[');
                char *array_end = array_start ? strchr(array_start, ']') : NULL;
                if (array_start && array_end)
                {
                    char *curr = array_start + 1;
                    while (curr < array_end && config->mission_track_color_count < MAX_MISSION_TRACK_COLORS)
                    {
                        char *obj_start = strchr(curr, '{');
                        if (!obj_start || obj_start >= array_end) break;
                        char *obj_end = strchr(obj_start, '}');
                        if (!obj_end || obj_end > array_end) break;
                        char *norad_ptr = strstr(obj_start, "\"norad\"");
                        char *color_ptr = strstr(obj_start, "\"color\"");
                        if (norad_ptr && norad_ptr < obj_end && color_ptr && color_ptr < obj_end)
                        {
                            char norad_raw[16] = {0};
                            char color_raw[16] = {0};
                            char *nq = strchr(strchr(norad_ptr, ':'), '"');
                            char *cq = strchr(strchr(color_ptr, ':'), '"');
                            if (nq && cq)
                            {
                                sscanf(nq + 1, "%15[^\"]", norad_raw);
                                sscanf(cq + 1, "%15[^\"]", color_raw);
                                SetMissionTrackColor(config, norad_raw, ParseHexColor(color_raw, WHITE));
                            }
                        }
                        curr = obj_end + 1;
                    }
                }
            }

            // load home location
''',
)
replace_once(
    "src/config.c",
    "        config->orbits_to_draw = 3.00;\n",
    "        config->orbits_to_draw = 3.00;\n        config->groundtrack_past_orbits = 1;\n        config->groundtrack_future_orbits = 2;\n        config->show_2d_mission_labels = true;\n        config->show_2d_footprints = false;\n",
)
replace_once(
    "src/config.c",
    "    fprintf(file, \"    \\\"orbits_to_draw\\\": %.2f,\\n\", config->orbits_to_draw);\n",
    "    fprintf(file, \"    \\\"orbits_to_draw\\\": %.2f,\\n\", config->orbits_to_draw);\n    fprintf(file, \"    \\\"groundtrack_past_orbits\\\": %d,\\n\", config->groundtrack_past_orbits);\n    fprintf(file, \"    \\\"groundtrack_future_orbits\\\": %d,\\n\", config->groundtrack_future_orbits);\n    fprintf(file, \"    \\\"show_2d_mission_labels\\\": %s,\\n\", config->show_2d_mission_labels ? \"true\" : \"false\");\n    fprintf(file, \"    \\\"show_2d_footprints\\\": %s,\\n\", config->show_2d_footprints ? \"true\" : \"false\");\n",
)
replace_once(
    "src/config.c",
    "    if (config->custom_tle_source_count > 0)\n",
    r'''    if (config->mission_track_color_count > 0)
    {
        fprintf(file, "    \"mission_track_colors\": [\n");
        for (int i = 0; i < config->mission_track_color_count; i++)
        {
            MissionTrackColor *entry = &config->mission_track_colors[i];
            fprintf(file, "        {\"norad\": \"%s\", \"color\": \"#%02X%02X%02X\"}%s\n",
                    entry->norad_id, entry->color.r, entry->color.g, entry->color.b,
                    (i == config->mission_track_color_count - 1) ? "" : ",");
        }
        fprintf(file, "    ],\n");
    }

    if (config->custom_tle_source_count > 0)
''',
)

# main.c ---------------------------------------------------------------------
replace_once(
    "src/main.c",
    "#include \"rotator.h\"\n\n/* * shaders for day/night transition",
    r'''#include "rotator.h"

#define MAX_2D_TRACK_ORBITS 10
#define TRACK_SEGMENTS_PER_ORBIT 120
#define MAX_2D_TRACK_SEGMENTS (MAX_2D_TRACK_ORBITS * 2 * TRACK_SEGMENTS_PER_ORBIT)

static int Clamp2DTrackOrbits(int count)
{
    if (count < 0) return 0;
    if (count > MAX_2D_TRACK_ORBITS) return MAX_2D_TRACK_ORBITS;
    return count;
}

static void DrawGroundTrack2D(Satellite *sat, const AppConfig *cfg, double current_epoch,
                              float map_w, float map_h, float zoom, float alpha,
                              bool highlighted, Color track_color, int past_orbits,
                              int future_orbits)
{
    past_orbits = Clamp2DTrackOrbits(past_orbits);
    future_orbits = Clamp2DTrackOrbits(future_orbits);
    int past_segments = past_orbits * TRACK_SEGMENTS_PER_ORBIT;
    int future_segments = future_orbits * TRACK_SEGMENTS_PER_ORBIT;
    int segments = past_segments + future_segments;
    if (segments <= 0) return;

    Vector2 track_pts[MAX_2D_TRACK_SEGMENTS + 1];
    bool is_sunlit_arr[MAX_2D_TRACK_SEGMENTS + 1];
    double period_days = (2.0 * PI / sat->mean_motion) / 86400.0;
    double time_step = period_days / TRACK_SEGMENTS_PER_ORBIT;
    Vector3 sun_dir = {0};
    if (cfg->highlight_sunlit)
        sun_dir = Vector3Normalize(calculate_sun_position(current_epoch));

    for (int j = 0; j <= segments; j++)
    {
        int offset_segments = j - past_segments;
        double t = current_epoch + offset_segments * time_step;
        Vector3 raw_pos = calculate_position(sat, get_unix_from_epoch(t));
        get_map_coordinates(raw_pos, epoch_to_gmst(t), cfg->earth_rotation_offset,
                            map_w, map_h, &track_pts[j].x, &track_pts[j].y);
        if (cfg->highlight_sunlit)
            is_sunlit_arr[j] = !is_sat_eclipsed(raw_pos, sun_dir);
    }

    for (int offset_i = -1; offset_i <= 1; offset_i++)
    {
        float x_off = offset_i * map_w;
        for (int j = 1; j <= segments; j++)
        {
            bool is_past = (j <= past_segments);
            if (is_past && j != past_segments && ((j / 3) % 2) != 0)
                continue;
            if (fabs(track_pts[j].x - track_pts[j - 1].x) >= map_w * 0.6f)
                continue;

            float time_alpha = is_past ? 0.45f : 0.95f;
            if (cfg->highlight_sunlit && !is_sunlit_arr[j])
                time_alpha *= 0.45f;
            Color draw_col = ApplyAlpha(track_color, alpha * time_alpha);
            DrawLineEx((Vector2){track_pts[j - 1].x + x_off, track_pts[j - 1].y},
                       (Vector2){track_pts[j].x + x_off, track_pts[j].y},
                       (highlighted ? 2.6f : 1.7f) / zoom, draw_col);
        }
    }
}

/* * shaders for day/night transition''',
)
replace_once(
    "src/main.c",
    "                if (active_sat && has_footprint && active_sat->is_active && !(is_pov_mode && selected_sat != NULL))\n",
    "                if (cfg.show_2d_footprints && active_sat && has_footprint && active_sat->is_active && !(is_pov_mode && selected_sat != NULL))\n",
)

regex_once(
    "src/main.c",
    r'''\s*bool is_hl = \(active_sat == &satellites\[i\]\);\n\s*Color sCol = .*?\n\s*sCol = ApplyAlpha\(sCol, sat_alpha\);\n\n\s*/\* Draw ground tracks for all active satellites on the 2D map\..*?\n\s*}\n\n\s*float sat_mx, sat_my;''',
    r'''
                    bool is_hl = (active_sat == &satellites[i]);
                    Color mission_color = GetMissionTrackColor(&cfg, satellites[i].norad_id);
                    Color sCol = ApplyAlpha(mission_color, sat_alpha);

                    bool draw_multi_tracks = (active_render_count <= 64);
                    bool draw_this_track = draw_multi_tracks || is_hl;
                    if (draw_this_track && !(is_pov_mode && &satellites[i] == selected_sat))
                    {
                        DrawGroundTrack2D(&satellites[i], &cfg, current_epoch, map_w, map_h,
                                          Camera2DParams.zoom, sat_alpha, is_hl, mission_color,
                                          cfg.groundtrack_past_orbits, cfg.groundtrack_future_orbits);

                        if (is_hl)
                        {
                            Vector2 peri2d, apo2d;
                            get_apsis_2d(&satellites[i], current_epoch, false, gmst_deg, cfg.earth_rotation_offset, map_w, map_h, &peri2d);
                            get_apsis_2d(&satellites[i], current_epoch, true, gmst_deg, cfg.earth_rotation_offset, map_w, map_h, &apo2d);
                            for (int offset_i = -1; offset_i <= 1; offset_i++)
                            {
                                float x_off = offset_i * map_w;
                                DrawTexturePro(periMark, (Rectangle){0, 0, periMark.width, periMark.height},
                                    (Rectangle){peri2d.x + x_off, peri2d.y, mark_size_2d, mark_size_2d},
                                    (Vector2){mark_size_2d / 2.f, mark_size_2d / 2.f}, 0.0f, ApplyAlpha(cfg.periapsis, sat_alpha));
                                DrawTexturePro(apoMark, (Rectangle){0, 0, apoMark.width, apoMark.height},
                                    (Rectangle){apo2d.x + x_off, apo2d.y, mark_size_2d, mark_size_2d},
                                    (Vector2){mark_size_2d / 2.f, mark_size_2d / 2.f}, 0.0f, ApplyAlpha(cfg.apoapsis, sat_alpha));
                            }
                        }
                    }

                    float sat_mx, sat_my;''',
)
replace_once(
    "src/main.c",
    """                            if (is_hl && Camera2DParams.zoom > 0.1f)
                            {
                                DrawUIText(customFont, satellites[i].name, sat_mx + (offset_i * map_w) + (m_size_2d / 2.f) + 4.f, sat_my - (m_size_2d / 2.f), m_text_2d, sCol);
                            }
""",
    """                            if (cfg.show_2d_mission_labels && (draw_multi_tracks || is_hl) && Camera2DParams.zoom > 0.1f)
                            {
                                float label_x = sat_mx + (offset_i * map_w) + (m_size_2d / 2.f) + 4.f / Camera2DParams.zoom;
                                float label_y = sat_my - (m_size_2d / 2.f);
                                DrawUIText(customFont, satellites[i].name, label_x, label_y, m_text_2d, sCol);
                            }
""",
)
replace_once(
    "src/main.c",
    "            EndMode2D();\n",
    r'''            EndMode2D();

            /* Screen-space legend: make past/NOW/future semantics explicit. */
            {
                float lx = 18.0f * cfg.ui_scale;
                float ly = 55.0f * cfg.ui_scale;
                float lw = 320.0f * cfg.ui_scale;
                float lh = 72.0f * cfg.ui_scale;
                DrawRectangleRounded((Rectangle){lx, ly, lw, lh}, 0.08f, 6, ApplyAlpha(cfg.ui_bg, 0.85f));
                DrawRectangleRoundedLinesEx((Rectangle){lx, ly, lw, lh}, 0.08f, 6, 1.0f, ApplyAlpha(cfg.ui_secondary, 0.7f));
                DrawUIText(customFont, TextFormat("2D ground tracks: %d past / %d future orbits",
                           cfg.groundtrack_past_orbits, cfg.groundtrack_future_orbits),
                           lx + 10.0f * cfg.ui_scale, ly + 8.0f * cfg.ui_scale,
                           14.0f * cfg.ui_scale, cfg.text_main);

                float line_y = ly + 45.0f * cfg.ui_scale;
                Color key = cfg.text_main;
                for (int d = 0; d < 4; d++)
                    DrawLineEx((Vector2){lx + (10 + d * 8) * cfg.ui_scale, line_y},
                               (Vector2){lx + (14 + d * 8) * cfg.ui_scale, line_y},
                               2.0f * cfg.ui_scale, ApplyAlpha(key, 0.5f));
                DrawUIText(customFont, "PAST", lx + 47.0f * cfg.ui_scale, line_y - 7.0f * cfg.ui_scale,
                           12.0f * cfg.ui_scale, cfg.text_secondary);
                DrawCircleV((Vector2){lx + 115.0f * cfg.ui_scale, line_y}, 4.0f * cfg.ui_scale, key);
                DrawUIText(customFont, "NOW", lx + 125.0f * cfg.ui_scale, line_y - 7.0f * cfg.ui_scale,
                           12.0f * cfg.ui_scale, cfg.text_main);
                DrawLineEx((Vector2){lx + 178.0f * cfg.ui_scale, line_y},
                           (Vector2){lx + 218.0f * cfg.ui_scale, line_y},
                           2.0f * cfg.ui_scale, key);
                DrawUIText(customFont, "FUTURE", lx + 226.0f * cfg.ui_scale, line_y - 7.0f * cfg.ui_scale,
                           12.0f * cfg.ui_scale, cfg.text_main);
            }
''',
)

# ui.c -----------------------------------------------------------------------
# Settings window is taller to hold the dedicated 2D map section.
Path("src/ui.c").write_text(Path("src/ui.c").read_text().replace("250 * cfg->ui_scale, 520 * cfg->ui_scale", "250 * cfg->ui_scale, 650 * cfg->ui_scale"))
replace_once(
    "src/ui.c",
    "            GuiCheckBox((Rectangle){sw_x + 10 * cfg->ui_scale, sy, 20 * cfg->ui_scale, 20 * cfg->ui_scale}, \"VSync\", &cfg->hint_vsync);            \n            sy += 30 * cfg->ui_scale;\n\n            DrawLine(sw_x + 10 * cfg->ui_scale, sy, sw_x + settingsWindow.width - 10 * cfg->ui_scale, sy, cfg->ui_secondary);\n",
    r'''            GuiCheckBox((Rectangle){sw_x + 10 * cfg->ui_scale, sy, 20 * cfg->ui_scale, 20 * cfg->ui_scale}, "VSync", &cfg->hint_vsync);
            sy += 30 * cfg->ui_scale;

            DrawLine(sw_x + 10 * cfg->ui_scale, sy, sw_x + settingsWindow.width - 10 * cfg->ui_scale, sy, cfg->ui_secondary);
            sy += 12 * cfg->ui_scale;
            DrawUIText(customFont, "2D Map", sw_x + 10 * cfg->ui_scale, sy, 16 * cfg->ui_scale, cfg->ui_accent);
            sy += 24 * cfg->ui_scale;
            GuiCheckBox((Rectangle){sw_x + 10 * cfg->ui_scale, sy, 20 * cfg->ui_scale, 20 * cfg->ui_scale}, "Mission Labels", &cfg->show_2d_mission_labels);
            sy += 25 * cfg->ui_scale;
            GuiCheckBox((Rectangle){sw_x + 10 * cfg->ui_scale, sy, 20 * cfg->ui_scale, 20 * cfg->ui_scale}, "Coverage Footprints", &cfg->show_2d_footprints);
            sy += 30 * cfg->ui_scale;

            GuiLabel((Rectangle){sw_x + 10 * cfg->ui_scale, sy, 90 * cfg->ui_scale, 24 * cfg->ui_scale}, "Past orbits:");
            if (GuiButton((Rectangle){sw_x + 108 * cfg->ui_scale, sy, 24 * cfg->ui_scale, 24 * cfg->ui_scale}, "-"))
                if (cfg->groundtrack_past_orbits > 0) cfg->groundtrack_past_orbits--;
            DrawUIText(customFont, TextFormat("%d", cfg->groundtrack_past_orbits), sw_x + 146 * cfg->ui_scale, sy + 3 * cfg->ui_scale, 15 * cfg->ui_scale, cfg->text_main);
            if (GuiButton((Rectangle){sw_x + 196 * cfg->ui_scale, sy, 24 * cfg->ui_scale, 24 * cfg->ui_scale}, "+"))
                if (cfg->groundtrack_past_orbits < 10) cfg->groundtrack_past_orbits++;
            sy += 30 * cfg->ui_scale;

            GuiLabel((Rectangle){sw_x + 10 * cfg->ui_scale, sy, 90 * cfg->ui_scale, 24 * cfg->ui_scale}, "Future orbits:");
            if (GuiButton((Rectangle){sw_x + 108 * cfg->ui_scale, sy, 24 * cfg->ui_scale, 24 * cfg->ui_scale}, "-"))
                if (cfg->groundtrack_future_orbits > 0) cfg->groundtrack_future_orbits--;
            DrawUIText(customFont, TextFormat("%d", cfg->groundtrack_future_orbits), sw_x + 146 * cfg->ui_scale, sy + 3 * cfg->ui_scale, 15 * cfg->ui_scale, cfg->text_main);
            if (GuiButton((Rectangle){sw_x + 196 * cfg->ui_scale, sy, 24 * cfg->ui_scale, 24 * cfg->ui_scale}, "+"))
                if (cfg->groundtrack_future_orbits < 10) cfg->groundtrack_future_orbits++;
            sy += 35 * cfg->ui_scale;

            DrawLine(sw_x + 10 * cfg->ui_scale, sy, sw_x + settingsWindow.width - 10 * cfg->ui_scale, sy, cfg->ui_secondary);
''',
)
replace_once(
    "src/ui.c",
    "                Rectangle contentRec = {0, 0, satInfoWindow.width - 32 * cfg->ui_scale, 580 * cfg->ui_scale};\n",
    "                Rectangle contentRec = {0, 0, satInfoWindow.width - 32 * cfg->ui_scale, 700 * cfg->ui_scale};\n",
)
replace_once(
    "src/ui.c",
    """                DRAW_HEADER("Identification");
                DRAW_ROW("NORAD ID:", TextFormat("%.6s", sat->norad_id));
                DRAW_ROW("Intl Desig:", TextFormat("%.8s", sat->intl_designator));

                cur_y += 10 * cfg->ui_scale;
                DRAW_HEADER("Orbital Information");
""",
    r'''                DRAW_HEADER("Identification");
                DRAW_ROW("NORAD ID:", TextFormat("%.6s", sat->norad_id));
                DRAW_ROW("Intl Desig:", TextFormat("%.8s", sat->intl_designator));

                cur_y += 10 * cfg->ui_scale;
                DRAW_HEADER("2D Track Color");
                Color mission_color = GetMissionTrackColor(cfg, sat->norad_id);
                int palette_count = GetMissionTrackPaletteSize();
                for (int p = 0; p < palette_count; p++)
                {
                    int col = p % 6;
                    int row = p / 6;
                    Rectangle swatch = {cur_x + 5 * cfg->ui_scale + col * 38 * cfg->ui_scale,
                                        cur_y + row * 32 * cfg->ui_scale,
                                        28 * cfg->ui_scale, 24 * cfg->ui_scale};
                    Color palette_color = GetMissionTrackPaletteColor(p);
                    DrawRectangleRec(swatch, palette_color);
                    bool chosen = (palette_color.r == mission_color.r && palette_color.g == mission_color.g && palette_color.b == mission_color.b);
                    DrawRectangleLinesEx(swatch, chosen ? 3.0f * cfg->ui_scale : 1.0f * cfg->ui_scale,
                                         chosen ? WHITE : ApplyAlpha(cfg->text_secondary, 0.8f));
                    if (is_topmost && CheckCollisionPointRec(GetMousePosition(), swatch) && CheckCollisionPointRec(GetMousePosition(), viewRec) && IsMouseButtonPressed(MOUSE_LEFT_BUTTON))
                    {
                        SetMissionTrackColor(cfg, sat->norad_id, palette_color);
                        SaveAppConfig("settings.json", cfg);
                        mission_color = palette_color;
                    }
                }
                cur_y += 68 * cfg->ui_scale;
                Rectangle auto_color = {cur_x + 5 * cfg->ui_scale, cur_y, 120 * cfg->ui_scale, 24 * cfg->ui_scale};
                if (is_topmost && CheckCollisionPointRec(GetMousePosition(), viewRec) && GuiButton(auto_color, "Auto color"))
                {
                    ResetMissionTrackColor(cfg, sat->norad_id);
                    SaveAppConfig("settings.json", cfg);
                }
                cur_y += 36 * cfg->ui_scale;

                DRAW_HEADER("Orbital Information");
''',
)

# README ---------------------------------------------------------------------
replace_once(
    "README.md",
    "- **​Dual-View Visualization**: Seamlessly toggle between an interactive 3D orbital space and a 2D projection featuring accurate satellite ground tracks.\n",
    "- **​Dual-View Visualization**: Seamlessly toggle between an interactive 3D orbital space and a 2D projection featuring accurate satellite ground tracks. The 2D mission view can show all active mission names at once, uses individually configurable track colors, distinguishes dashed past tracks from solid predicted tracks, and lets you choose separate past/future orbit counts. Coverage footprints are optional.\n",
)

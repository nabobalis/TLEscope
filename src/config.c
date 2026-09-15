#include "config.h"
#include "types.h"
#include <ctype.h>
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>

Marker home_location;

// turn hex strings into real colors
Color ParseHexColor(const char *hexStr, Color fallback)
{
    if (!hexStr || hexStr[0] != '#')
        return fallback;
    unsigned int r = 0, g = 0, b = 0, a = 255;
    int len = strlen(hexStr);
    if (len == 7)
    {
        sscanf(hexStr, "#%02x%02x%02x", &r, &g, &b);
    }
    else if (len >= 9)
    {
        sscanf(hexStr, "#%02x%02x%02x%02x", &r, &g, &b, &a);
    }
    else
    {
        return fallback;
    }
    return (Color){(unsigned char)r, (unsigned char)g, (unsigned char)b, (unsigned char)a};
}

// High-contrast categorical colors for automatic 2D mission tracks.  The
// ordering deliberately jumps around hue space so adjacent swatches remain
// easy to distinguish on the dark world map.
static const Color MISSION_TRACK_PALETTE[] = {
    {  0, 181, 255, 255}, {255, 138,   0, 255}, {  0, 209, 125, 255},
    {255,  77, 109, 255}, {182, 109, 255, 255}, {255, 212,  59, 255},
    {  0, 229, 255, 255}, {255,  91, 239, 255}, {167, 244,  50, 255},
    {255, 159, 159, 255}, {  0, 166, 166, 255}, {123,  97, 255, 255},
    {255, 107,   0, 255}, {128,  64, 192, 255}, {  6, 214, 160, 255},
    {239,  71, 111, 255}, { 58, 134, 255, 255}, {255, 176,   0, 255},
    {131,  56, 236, 255}, { 36, 161,  72, 255}, {245,  93, 106, 255},
    { 17, 138, 178, 255}, {251,  86,   7, 255}, {138, 201,  38, 255}
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
    // Mix the NORAD id before selecting a palette slot.  The previous direct
    // modulo assignment clustered nearby catalogue numbers and produced
    // frequent duplicate/near-duplicate mission colors.
    uint32_t hash = (uint32_t)strtoul(normalized, NULL, 10);
    hash ^= hash >> 16;
    hash *= 0x7feb352dU;
    hash ^= hash >> 15;
    hash *= 0x846ca68bU;
    hash ^= hash >> 16;
    return GetMissionTrackPaletteColor((int)(hash % (uint32_t)GetMissionTrackPaletteSize()));
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

static bool ParseJsonBool(const char *text, const char *key, bool defaultValue)
{
    if (!text || !key)
        return defaultValue;

    char needle[64];
    snprintf(needle, sizeof(needle), "\"%s\"", key);
    char *ptr = strstr(text, needle);
    if (!ptr)
        return defaultValue;

    ptr = strchr(ptr, ':');
    if (!ptr)
        return defaultValue;
    ptr++;

    while (*ptr && isspace((unsigned char)*ptr))
        ptr++;

    if (strncmp(ptr, "true", 4) == 0)
        return true;
    if (strncmp(ptr, "false", 5) == 0)
        return false;

    return defaultValue;
}

// read the json file and grab our settings
void LoadAppConfig(const char *filename, AppConfig *config)
{
    // default theme configuration
    strcpy(config->theme, "default");
    config->show_markers = true;      // default
    config->show_statistics = false;  // default
    config->highlight_sunlit = false; // default
    config->show_slant_range = false; // default
    config->show_scattering = false;  // default
    config->show_skybox = true;       // default
    config->show_first_run_dialog = false; //default
    config->hint_vsync = true;       // default
    config->custom_tle_source_count = 0;
    config->tle_proxy[0] = '\0';
    config->mission_track_color_count = 0;
    config->groundtrack_past_orbits = 1;
    config->groundtrack_future_orbits = 2;
    config->show_2d_mission_labels = true;
    config->show_2d_footprints = false;

    if (FileExists(filename))
    {
        char *text = LoadFileText(filename);
        if (text)
        {
            char hex[32];
            char *ptr;

#define PARSE_FLOAT(key, field)                                                                                                                                                                        \
    ptr = strstr(text, "\"" key "\"");                                                                                                                                                                 \
    if (ptr)                                                                                                                                                                                           \
    {                                                                                                                                                                                                  \
        ptr = strchr(ptr, ':');                                                                                                                                                                        \
        if (ptr)                                                                                                                                                                                       \
        {                                                                                                                                                                                              \
            sscanf(ptr + 1, "%f", &config->field);                                                                                                                                                     \
        }                                                                                                                                                                                              \
    }

#define PARSE_INT(key, field)                                                                                                                                                                          \
    ptr = strstr(text, "\"" key "\"");                                                                                                                                                                 \
    if (ptr)                                                                                                                                                                                           \
    {                                                                                                                                                                                                  \
        ptr = strchr(ptr, ':');                                                                                                                                                                        \
        if (ptr)                                                                                                                                                                                       \
        {                                                                                                                                                                                              \
            sscanf(ptr + 1, "%d", &config->field);                                                                                                                                                     \
        }                                                                                                                                                                                              \
    }

            ptr = strstr(text, "\"theme\"");
            if (ptr)
            {
                ptr = strchr(ptr, ':');
                if (ptr)
                {
                    char *quote_start = strchr(ptr, '"');
                    if (quote_start)
                    {
                        sscanf(quote_start + 1, "%63[^\"]", config->theme);
                    }
                }
            }

            PARSE_INT("window_width", window_width);
            PARSE_INT("window_height", window_height);
            PARSE_INT("target_fps", target_fps);
            PARSE_FLOAT("ui_scale", ui_scale);
            PARSE_FLOAT("earth_rotation_offset", earth_rotation_offset);
            PARSE_FLOAT("orbits_to_draw", orbits_to_draw);
            PARSE_INT("groundtrack_past_orbits", groundtrack_past_orbits);
            PARSE_INT("groundtrack_future_orbits", groundtrack_future_orbits);
            if (config->groundtrack_past_orbits < 0) config->groundtrack_past_orbits = 0;
            if (config->groundtrack_past_orbits > 10) config->groundtrack_past_orbits = 10;
            if (config->groundtrack_future_orbits < 0) config->groundtrack_future_orbits = 0;
            if (config->groundtrack_future_orbits > 10) config->groundtrack_future_orbits = 10;

            config->show_clouds = ParseJsonBool(text, "show_clouds", config->show_clouds);
            config->show_night_lights = ParseJsonBool(text, "show_night_lights", config->show_night_lights);
            config->show_markers = ParseJsonBool(text, "show_markers", config->show_markers);
            config->show_statistics = ParseJsonBool(text, "show_statistics", config->show_statistics);
            config->highlight_sunlit = ParseJsonBool(text, "highlight_sunlit", config->highlight_sunlit);
            config->show_slant_range = ParseJsonBool(text, "show_slant_range", config->show_slant_range);
            config->show_skybox = ParseJsonBool(text, "show_skybox", config->show_skybox);
            config->show_scattering = ParseJsonBool(text, "show_scattering", config->show_scattering);
            config->hint_vsync = ParseJsonBool(text, "hint_vsync", config->hint_vsync);
            config->show_first_run_dialog = ParseJsonBool(text, "show_first_run_dialog", config->show_first_run_dialog);
            config->show_2d_mission_labels = ParseJsonBool(text, "show_2d_mission_labels", config->show_2d_mission_labels);
            config->show_2d_footprints = ParseJsonBool(text, "show_2d_footprints", config->show_2d_footprints);

            ptr = strstr(text, "\"tle_proxy\"");
            if (ptr)
            {
                ptr = strchr(ptr, ':');
                if (ptr)
                {
                    char *quote_start = strchr(ptr, '\"');
                    if (quote_start)
                        sscanf(quote_start + 1, "%255[^\"]", config->tle_proxy);
                }
            }

            // load manual TLEs
            char *mt_ptr = strstr(text, "\"manual_tles\"");
            if (mt_ptr)
            {
                char *array_start = strchr(mt_ptr, '[');
                char *array_end = array_start ? strchr(array_start, ']') : NULL;
                if (array_start && array_end)
                {
                    char *curr = array_start + 1;
                    while (curr < array_end && config->manual_tle_count < MAX_MANUAL_TLES)
                    {
                        char *quote_start = strchr(curr, '"');
                        if (!quote_start || quote_start > array_end) break;
                        char *quote_end = strchr(quote_start + 1, '"');
                        if (!quote_end || quote_end > array_end) break;

                        int len = quote_end - (quote_start + 1);
                        if (len >= 512) len = 511;
                        strncpy(config->manual_tles[config->manual_tle_count], quote_start + 1, len);
                        config->manual_tles[config->manual_tle_count][len] = '\0';
                        config->manual_tle_count++;

                        curr = quote_end + 1;
                    }
                }
            }

            // load custom TLE sources
            char *cts_ptr = strstr(text, "\"custom_tle_sources\"");
            if (cts_ptr)
            {
                char *block_end = strchr(cts_ptr, ']');
                if (!block_end)
                    block_end = text + strlen(text);

                while ((cts_ptr = strstr(cts_ptr, "{")) && cts_ptr < block_end)
                {
                    if (config->custom_tle_source_count >= MAX_CUSTOM_TLE_SOURCES)
                        break;

                    char *obj_end = strchr(cts_ptr, '}');
                    if (!obj_end || obj_end > block_end)
                        obj_end = block_end;

                    char *name_ptr = strstr(cts_ptr, "\"name\"");
                    char *url_ptr = strstr(cts_ptr, "\"url\"");

                    if (name_ptr && name_ptr < obj_end && url_ptr && url_ptr < obj_end)
                    {
                        char *colon_name = strchr(name_ptr, ':');
                        if (colon_name && colon_name < obj_end)
                        {
                            char *quote_start = strchr(colon_name, '"');
                            if (quote_start && quote_start < obj_end)
                                sscanf(quote_start + 1, "%63[^\"]", config->custom_tle_sources[config->custom_tle_source_count].name);
                        }

                        char *colon_url = strchr(url_ptr, ':');
                        if (colon_url && colon_url < obj_end)
                        {
                            char *quote_start = strchr(colon_url, '"');
                            if (quote_start && quote_start < obj_end)
                                sscanf(quote_start + 1, "%255[^\"]", config->custom_tle_sources[config->custom_tle_source_count].url);
                        }

                        config->custom_tle_sources[config->custom_tle_source_count].selected = false;
                        config->custom_tle_source_count++;
                    }
                    cts_ptr = obj_end + 1;
                }
            }

            // load per-mission 2D ground-track color overrides
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
            char *hl_ptr = strstr(text, "\"home_location\"");
            if (hl_ptr)
            {
                char *name_ptr = strstr(hl_ptr, "\"name\"");
                char *lat_ptr = strstr(hl_ptr, "\"lat\"");
                char *lon_ptr = strstr(hl_ptr, "\"lon\"");
                char *alt_ptr = strstr(hl_ptr, "\"alt\"");
                char *obj_end = strchr(hl_ptr, '}');

                if (name_ptr && lat_ptr && lon_ptr && name_ptr < obj_end)
                {
                    char *colon_name = strchr(name_ptr, ':');
                    if (colon_name)
                    {
                        char *quote_start = strchr(colon_name, '"');
                        if (quote_start)
                            sscanf(quote_start + 1, "%63[^\"]", home_location.name);
                    }
                    char *colon_lat = strchr(lat_ptr, ':');
                    if (colon_lat)
                        sscanf(colon_lat + 1, "%f", &home_location.lat);

                    char *colon_lon = strchr(lon_ptr, ':');
                    if (colon_lon)
                        sscanf(colon_lon + 1, "%f", &home_location.lon);

                    home_location.alt = 0.0f;
                    if (alt_ptr && alt_ptr < obj_end)
                    {
                        char *colon_alt = strchr(alt_ptr, ':');
                        if (colon_alt)
                            sscanf(colon_alt + 1, "%f", &home_location.alt);
                    }
                }
            }

            // load the map markers safely to avoid silent parsing failures
            marker_count = 0;
            char *m_ptr = strstr(text, "\"markers\"");
            if (m_ptr)
            {
                char *block_end = strchr(m_ptr, ']');
                if (!block_end)
                    block_end = text + strlen(text);

                while ((m_ptr = strstr(m_ptr, "{")) && m_ptr < block_end)
                {
                    if (marker_count >= MAX_MARKERS)
                        break;

                    char *obj_end = strchr(m_ptr, '}');
                    if (!obj_end || obj_end > block_end)
                        obj_end = block_end;

                    char *name_ptr = strstr(m_ptr, "\"name\"");
                    char *lat_ptr = strstr(m_ptr, "\"lat\"");
                    char *lon_ptr = strstr(m_ptr, "\"lon\"");
                    char *alt_ptr = strstr(m_ptr, "\"alt\"");

                    // alt_ptr is optional now
                    if (name_ptr && name_ptr < obj_end && lat_ptr && lat_ptr < obj_end && lon_ptr && lon_ptr < obj_end)
                    {

                        char *colon_name = strchr(name_ptr, ':');
                        if (colon_name && colon_name < obj_end)
                        {
                            char *quote_start = strchr(colon_name, '"');
                            if (quote_start && quote_start < obj_end)
                                sscanf(quote_start + 1, "%63[^\"]", markers[marker_count].name);
                        }

                        char *colon_lat = strchr(lat_ptr, ':');
                        if (colon_lat && colon_lat < obj_end)
                            sscanf(colon_lat + 1, "%f", &markers[marker_count].lat);

                        char *colon_lon = strchr(lon_ptr, ':');
                        if (colon_lon && colon_lon < obj_end)
                            sscanf(colon_lon + 1, "%f", &markers[marker_count].lon);

                        markers[marker_count].alt = 0.0f;
                        if (alt_ptr && alt_ptr < obj_end)
                        {
                            char *colon_alt = strchr(alt_ptr, ':');
                            if (colon_alt && colon_alt < obj_end)
                                sscanf(colon_alt + 1, "%f", &markers[marker_count].alt);
                        }

                        marker_count++;
                    }
                    m_ptr = obj_end + 1;
                }
            }
            UnloadFileText(text);
        }
    }
    else {
        printf("INFO: No config file found at %s! Showing first run dialog!\n", filename);
        sscanf("default","%63[^\"]",config->theme);
        config->window_width = 1920;
        config->window_height = 1080;
        config->target_fps = 120;
        config->ui_scale = 1.15;
        config->earth_rotation_offset = 0.00;
        config->orbits_to_draw = 3.00;
        config->groundtrack_past_orbits = 1;
        config->groundtrack_future_orbits = 2;
        config->show_2d_mission_labels = true;
        config->show_2d_footprints = false;
        config->show_clouds = true;
        config->show_night_lights = true;
        config->show_markers = true;
        config->show_statistics = false;
        config->highlight_sunlit = false;
        config->show_slant_range = false;
        config->show_scattering = false;
        config->show_skybox = true;
        config->hint_vsync = true;
        sscanf("Home", "%63[^\"]", home_location.name);
        home_location.lat = 0.00;
        home_location.lon = 0.00;

        marker_count = 1;
        sscanf("Cape Canaveral", "%63[^\"]", markers[0].name);
        markers[0].lat = 28.3922f;
        markers[0].lon = -80.6077f;
        markers[0].alt = 0.0f;

        config->show_first_run_dialog = true;

        SaveAppConfig(filename, config);
        

    }

    // load colors from the selected theme file
    char theme_path[256];
    snprintf(theme_path, sizeof(theme_path), "themes/%s/theme.json", config->theme);

    if (FileExists(theme_path))
    {
        char *theme_text = LoadFileText(theme_path);
        if (theme_text)
        {
            char hex[32];
            char *ptr;

#define PARSE_COLOR(key, field)                                                                                                                                                                        \
    ptr = strstr(theme_text, "\"" key "\"");                                                                                                                                                           \
    if (ptr)                                                                                                                                                                                           \
    {                                                                                                                                                                                                  \
        ptr = strchr(ptr, ':');                                                                                                                                                                        \
        if (ptr)                                                                                                                                                                                       \
        {                                                                                                                                                                                              \
            ptr = strchr(ptr, '\"');                                                                                                                                                                   \
            if (ptr)                                                                                                                                                                                   \
            {                                                                                                                                                                                          \
                sscanf(ptr + 1, "%31[^\"]", hex);                                                                                                                                                      \
                config->field = ParseHexColor(hex, config->field);                                                                                                                                     \
            }                                                                                                                                                                                          \
        }                                                                                                                                                                                              \
    }

            PARSE_COLOR("bg_color", bg_color);
            PARSE_COLOR("orbit_normal", orbit_normal);
            PARSE_COLOR("orbit_highlighted", orbit_highlighted);
            PARSE_COLOR("sat_normal", sat_normal);
            PARSE_COLOR("sat_highlighted", sat_highlighted);
            PARSE_COLOR("sat_selected", sat_selected);
            PARSE_COLOR("text_main", text_main);
            PARSE_COLOR("text_secondary", text_secondary);
            PARSE_COLOR("ui_bg", ui_bg);
            PARSE_COLOR("periapsis", periapsis);
            PARSE_COLOR("apoapsis", apoapsis);
            PARSE_COLOR("footprint_bg", footprint_bg);
            PARSE_COLOR("footprint_border", footprint_border);

            PARSE_COLOR("ui_primary", ui_primary);
            PARSE_COLOR("ui_secondary", ui_secondary);
            PARSE_COLOR("ui_accent", ui_accent);
            PARSE_COLOR("window_border", window_border);
            PARSE_COLOR("window_border_focus", window_border_focus);

            PARSE_COLOR("scope_bg", scope_bg);
            PARSE_COLOR("scope_horizon", scope_horizon);
            PARSE_COLOR("overlay_dim", overlay_dim);

            UnloadFileText(theme_text);
        }
    }
}

void SaveAppConfig(const char *filename, AppConfig *config)
{
    FILE *file = fopen(filename, "w");
    if (!file)
        return;

    fprintf(file, "{\n");
    fprintf(file, "    \"theme\": \"%s\",\n", config->theme);
    fprintf(file, "    \"window_width\": %d,\n", config->window_width);
    fprintf(file, "    \"window_height\": %d,\n", config->window_height);
    fprintf(file, "    \"target_fps\": %d,\n", config->target_fps);
    fprintf(file, "    \"ui_scale\": %.2f,\n", config->ui_scale);
    fprintf(file, "    \"earth_rotation_offset\": %.2f,\n", config->earth_rotation_offset);
    fprintf(file, "    \"orbits_to_draw\": %.2f,\n", config->orbits_to_draw);
    fprintf(file, "    \"groundtrack_past_orbits\": %d,\n", config->groundtrack_past_orbits);
    fprintf(file, "    \"groundtrack_future_orbits\": %d,\n", config->groundtrack_future_orbits);
    fprintf(file, "    \"show_2d_mission_labels\": %s,\n", config->show_2d_mission_labels ? "true" : "false");
    fprintf(file, "    \"show_2d_footprints\": %s,\n", config->show_2d_footprints ? "true" : "false");
    fprintf(file, "    \"show_clouds\": %s,\n", config->show_clouds ? "true" : "false");
    fprintf(file, "    \"show_night_lights\": %s,\n", config->show_night_lights ? "true" : "false");
    fprintf(file, "    \"show_markers\": %s,\n", config->show_markers ? "true" : "false");
    fprintf(file, "    \"show_statistics\": %s,\n", config->show_statistics ? "true" : "false");
    fprintf(file, "    \"highlight_sunlit\": %s,\n", config->highlight_sunlit ? "true" : "false");
    fprintf(file, "    \"show_slant_range\": %s,\n", config->show_slant_range ? "true" : "false");
    fprintf(file, "    \"show_scattering\": %s,\n", config->show_scattering ? "true" : "false");
    fprintf(file, "    \"show_skybox\": %s,\n", config->show_skybox ? "true" : "false");
    fprintf(file, "    \"hint_vsync\": %s,\n", config->hint_vsync ? "true" : "false");
    fprintf(file, "    \"show_first_run_dialog\": %s,\n", config->show_first_run_dialog ? "true" : "false");
    fprintf(file, "    \"tle_proxy\": \"%s\",\n", config->tle_proxy);

    if (config->mission_track_color_count > 0)
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
    {
        fprintf(file, "    \"custom_tle_sources\": [\n");
        for (int i = 0; i < config->custom_tle_source_count; i++)
        {
            fprintf(file, "    {\"name\": \"%s\", \"url\": \"%s\"}%s\n", config->custom_tle_sources[i].name, config->custom_tle_sources[i].url, (i == config->custom_tle_source_count - 1) ? "" : ",");
        }
        fprintf(file, "    ],\n");
    }

    if (config->manual_tle_count > 0)
    {
        fprintf(file, "    \"manual_tles\": [\n");
        for (int i = 0; i < config->manual_tle_count; i++)
        {
            fprintf(file, "        \"%s\"%s\n", config->manual_tles[i], (i == config->manual_tle_count - 1) ? "" : ",");
        }
        fprintf(file, "    ],\n");
    }

    fprintf(file, "    \"home_location\": {\"name\": \"%s\", \"lat\": %.4f, \"lon\": %.4f, \"alt\": %.4f},\n", home_location.name, home_location.lat, home_location.lon, home_location.alt);

    fprintf(file, "    \"markers\": [\n");
    for (int i = 0; i < marker_count; i++)
    {
        fprintf(file, "    {\"name\": \"%s\", \"lat\": %.4f, \"lon\": %.4f, \"alt\": %.4f}%s\n", markers[i].name, markers[i].lat, markers[i].lon, markers[i].alt, (i == marker_count - 1) ? "" : ",");
    }
    fprintf(file, "    ]\n");
    fprintf(file, "}\n");
    fclose(file);
}

from pathlib import Path

config_path = Path("src/config.c")
ui_path = Path("src/ui.c")

config = config_path.read_text()
ui = ui_path.read_text()

config = config.replace(
    '#include <stdlib.h>\n#include <string.h>\n',
    '#include <stdlib.h>\n#include <stdint.h>\n#include <string.h>\n',
    1,
)

old_palette = '''static const Color MISSION_TRACK_PALETTE[] = {
    {  0, 174, 239, 255}, {255, 153,   0, 255}, {  0, 204, 136, 255},
    {238, 102, 119, 255}, {187, 119, 255, 255}, {255, 221,  87, 255},
    { 86, 180, 233, 255}, {230, 159,   0, 255}, {  0, 158, 115, 255},
    {213,  94,   0, 255}, {204, 121, 167, 255}, {120, 220, 120, 255}
};
'''
new_palette = '''// High-contrast categorical colors for automatic 2D mission tracks.  The
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
'''
if old_palette not in config:
    raise SystemExit("palette block not found")
config = config.replace(old_palette, new_palette, 1)

old_default = '''    unsigned long id = strtoul(normalized, NULL, 10);
    return GetMissionTrackPaletteColor((int)(id % (unsigned long)GetMissionTrackPaletteSize()));
'''
new_default = '''    // Mix the NORAD id before selecting a palette slot.  The previous direct
    // modulo assignment clustered nearby catalogue numbers and produced
    // frequent duplicate/near-duplicate mission colors.
    uint32_t hash = (uint32_t)strtoul(normalized, NULL, 10);
    hash ^= hash >> 16;
    hash *= 0x7feb352dU;
    hash ^= hash >> 15;
    hash *= 0x846ca68bU;
    hash ^= hash >> 16;
    return GetMissionTrackPaletteColor((int)(hash % (uint32_t)GetMissionTrackPaletteSize()));
'''
if old_default not in config:
    raise SystemExit("default color assignment not found")
config = config.replace(old_default, new_default, 1)

state_marker = '''static Satellite *last_selected_sat = NULL;
static Vector2 si_scroll = {0};
'''
state_replacement = '''static Satellite *last_selected_sat = NULL;
static Vector2 si_scroll = {0};
static Satellite *sat_color_picker_sat = NULL;
static bool sat_color_picker_open = false;
static bool edit_sat_color_hex = false;
static Color sat_color_picker_value = {255, 255, 255, 255};
static char sat_color_hex[8] = "#FFFFFF";

static bool IsValidMissionHex(const char *text)
{
    if (!text || strlen(text) != 7 || text[0] != '#') return false;
    for (int i = 1; i < 7; i++)
        if (!isxdigit((unsigned char)text[i])) return false;
    return true;
}
'''
if state_marker not in ui:
    raise SystemExit("satellite info state marker not found")
ui = ui.replace(state_marker, state_replacement, 1)

old_height = '                Rectangle contentRec = {0, 0, satInfoWindow.width - 32 * cfg->ui_scale, 700 * cfg->ui_scale};\n'
new_height = '                Rectangle contentRec = {0, 0, satInfoWindow.width - 32 * cfg->ui_scale, (sat_color_picker_open ? 1030 : 850) * cfg->ui_scale};\n'
if old_height not in ui:
    raise SystemExit("satellite info content height not found")
ui = ui.replace(old_height, new_height, 1)

old_ui = '''                DRAW_HEADER("2D Track Color");
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
                bool auto_color_clicked = GuiButton(auto_color, "Auto color");
                if (is_topmost && CheckCollisionPointRec(GetMousePosition(), viewRec) && auto_color_clicked)
                {
                    ResetMissionTrackColor(cfg, sat->norad_id);
                    SaveAppConfig("settings.json", cfg);
                }
                cur_y += 36 * cfg->ui_scale;
'''
new_ui = '''                DRAW_HEADER("2D Track Color");
                Color mission_color = GetMissionTrackColor(cfg, sat->norad_id);
                if (sat_color_picker_sat != sat)
                {
                    sat_color_picker_sat = sat;
                    sat_color_picker_open = false;
                    edit_sat_color_hex = false;
                    sat_color_picker_value = mission_color;
                    snprintf(sat_color_hex, sizeof(sat_color_hex), "#%02X%02X%02X", mission_color.r, mission_color.g, mission_color.b);
                }

                int palette_count = GetMissionTrackPaletteSize();
                int palette_rows = (palette_count + 5) / 6;
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
                        sat_color_picker_value = palette_color;
                        snprintf(sat_color_hex, sizeof(sat_color_hex), "#%02X%02X%02X", palette_color.r, palette_color.g, palette_color.b);
                    }
                }
                cur_y += (palette_rows * 32 + 4) * cfg->ui_scale;

                DrawUIText(customFont, "Hex:", cur_x + 5 * cfg->ui_scale, cur_y + 3 * cfg->ui_scale, 15 * cfg->ui_scale, cfg->text_main);
                Rectangle preview = {cur_x + 42 * cfg->ui_scale, cur_y, 28 * cfg->ui_scale, 24 * cfg->ui_scale};
                DrawRectangleRec(preview, mission_color);
                DrawRectangleLinesEx(preview, 1.0f * cfg->ui_scale, cfg->text_secondary);
                AdvancedTextBox((Rectangle){cur_x + 78 * cfg->ui_scale, cur_y, 92 * cfg->ui_scale, 24 * cfg->ui_scale}, sat_color_hex, 8, &edit_sat_color_hex, false);
                bool apply_hex = GuiButton((Rectangle){cur_x + 178 * cfg->ui_scale, cur_y, 58 * cfg->ui_scale, 24 * cfg->ui_scale}, "Apply");
                if (apply_hex && IsValidMissionHex(sat_color_hex))
                {
                    Color custom = ParseHexColor(sat_color_hex, mission_color);
                    custom.a = 255;
                    SetMissionTrackColor(cfg, sat->norad_id, custom);
                    SaveAppConfig("settings.json", cfg);
                    mission_color = custom;
                    sat_color_picker_value = custom;
                    snprintf(sat_color_hex, sizeof(sat_color_hex), "#%02X%02X%02X", custom.r, custom.g, custom.b);
                    edit_sat_color_hex = false;
                }
                cur_y += 32 * cfg->ui_scale;

                bool picker_clicked = GuiButton((Rectangle){cur_x + 5 * cfg->ui_scale, cur_y, 112 * cfg->ui_scale, 24 * cfg->ui_scale}, sat_color_picker_open ? "Hide picker" : "Custom picker");
                bool auto_color_clicked = GuiButton((Rectangle){cur_x + 125 * cfg->ui_scale, cur_y, 112 * cfg->ui_scale, 24 * cfg->ui_scale}, "Auto color");
                if (picker_clicked)
                {
                    sat_color_picker_open = !sat_color_picker_open;
                    sat_color_picker_value = mission_color;
                }
                if (is_topmost && CheckCollisionPointRec(GetMousePosition(), viewRec) && auto_color_clicked)
                {
                    ResetMissionTrackColor(cfg, sat->norad_id);
                    SaveAppConfig("settings.json", cfg);
                    mission_color = GetMissionTrackColor(cfg, sat->norad_id);
                    sat_color_picker_value = mission_color;
                    snprintf(sat_color_hex, sizeof(sat_color_hex), "#%02X%02X%02X", mission_color.r, mission_color.g, mission_color.b);
                    edit_sat_color_hex = false;
                }
                cur_y += 32 * cfg->ui_scale;

                if (sat_color_picker_open)
                {
                    Color before_picker = sat_color_picker_value;
                    GuiColorPicker((Rectangle){cur_x + 5 * cfg->ui_scale, cur_y, 220 * cfg->ui_scale, 130 * cfg->ui_scale}, NULL, &sat_color_picker_value);
                    sat_color_picker_value.a = 255;
                    if (before_picker.r != sat_color_picker_value.r || before_picker.g != sat_color_picker_value.g || before_picker.b != sat_color_picker_value.b)
                        snprintf(sat_color_hex, sizeof(sat_color_hex), "#%02X%02X%02X", sat_color_picker_value.r, sat_color_picker_value.g, sat_color_picker_value.b);
                    cur_y += 138 * cfg->ui_scale;
                    if (GuiButton((Rectangle){cur_x + 5 * cfg->ui_scale, cur_y, 220 * cfg->ui_scale, 24 * cfg->ui_scale}, "Use custom color"))
                    {
                        SetMissionTrackColor(cfg, sat->norad_id, sat_color_picker_value);
                        SaveAppConfig("settings.json", cfg);
                        mission_color = sat_color_picker_value;
                    }
                    cur_y += 36 * cfg->ui_scale;
                }
                else
                {
                    cur_y += 4 * cfg->ui_scale;
                }
'''
if old_ui not in ui:
    raise SystemExit("2D track color UI block not found")
ui = ui.replace(old_ui, new_ui, 1)

config_path.write_text(config)
ui_path.write_text(ui)

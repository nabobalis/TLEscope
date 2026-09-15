from pathlib import Path


def replace_once(text, old, new, label):
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{label}: expected 1 match, found {count}")
    return text.replace(old, new, 1)

# AppConfig: persist the 2D ground-track legend toggle.
p = Path("src/types.h")
s = p.read_text()
s = replace_once(
    s,
    "    bool show_2d_mission_labels;\n    bool show_2d_footprints;\n",
    "    bool show_2d_mission_labels;\n    bool show_2d_footprints;\n    bool show_2d_track_legend;\n",
    "types legend field",
)
p.write_text(s)

# Config defaults/load/save for the legend toggle.
p = Path("src/config.c")
s = p.read_text()
old = "    config->show_2d_mission_labels = true;\n    config->show_2d_footprints = false;\n"
if s.count(old) != 2:
    raise SystemExit(f"config defaults: expected 2 matches, found {s.count(old)}")
s = s.replace(old, old + "    config->show_2d_track_legend = true;\n")
s = replace_once(
    s,
    '            config->show_2d_footprints = ParseJsonBool(text, "show_2d_footprints", config->show_2d_footprints);\n',
    '            config->show_2d_footprints = ParseJsonBool(text, "show_2d_footprints", config->show_2d_footprints);\n'
    '            config->show_2d_track_legend = ParseJsonBool(text, "show_2d_track_legend", config->show_2d_track_legend);\n',
    "config parse legend",
)
s = replace_once(
    s,
    '    fprintf(file, "    \\"show_2d_footprints\\": %s,\\n", config->show_2d_footprints ? "true" : "false");\n',
    '    fprintf(file, "    \\"show_2d_footprints\\": %s,\\n", config->show_2d_footprints ? "true" : "false");\n'
    '    fprintf(file, "    \\"show_2d_track_legend\\": %s,\\n", config->show_2d_track_legend ? "true" : "false");\n',
    "config save legend",
)
p.write_text(s)

# UI: clearer proxy/error presentation and legend setting.
p = Path("src/ui.c")
s = p.read_text()
s = replace_once(
    s,
    '        snprintf(pull_error_detail, sizeof(pull_error_detail), "%s | %s | HTTP %ld", url, detail, http_code);\n',
    '        snprintf(pull_error_detail, sizeof(pull_error_detail), "Source: %s\\nError: %s\\nHTTP: %ld", url, detail, http_code);\n',
    "structured pull error",
)

old_settings = '''            GuiCheckBox((Rectangle){sw_x + 10 * cfg->ui_scale, sy, 20 * cfg->ui_scale, 20 * cfg->ui_scale}, "Mission Labels", &cfg->show_2d_mission_labels);\n            sy += 25 * cfg->ui_scale;\n            GuiCheckBox((Rectangle){sw_x + 10 * cfg->ui_scale, sy, 20 * cfg->ui_scale, 20 * cfg->ui_scale}, "Coverage Footprints", &cfg->show_2d_footprints);\n            sy += 30 * cfg->ui_scale;\n'''
new_settings = '''            GuiCheckBox((Rectangle){sw_x + 10 * cfg->ui_scale, sy, 20 * cfg->ui_scale, 20 * cfg->ui_scale}, "Mission Labels", &cfg->show_2d_mission_labels);\n            sy += 25 * cfg->ui_scale;\n            GuiCheckBox((Rectangle){sw_x + 10 * cfg->ui_scale, sy, 20 * cfg->ui_scale, 20 * cfg->ui_scale}, "Track Legend", &cfg->show_2d_track_legend);\n            sy += 25 * cfg->ui_scale;\n            GuiCheckBox((Rectangle){sw_x + 10 * cfg->ui_scale, sy, 20 * cfg->ui_scale, 20 * cfg->ui_scale}, "Coverage Footprints", &cfg->show_2d_footprints);\n            sy += 30 * cfg->ui_scale;\n'''
s = replace_once(s, old_settings, new_settings, "2D settings checkboxes")

old_error = '''            if (pull_error_detail[0] != '\\0')\n            {\n                char short_error[80];\n                size_t err_len = strlen(pull_error_detail);\n                snprintf(short_error, sizeof(short_error), "%.68s%s", pull_error_detail, err_len > 68 ? "..." : "");\n                DrawUIText(customFont, short_error, tm_x + 10 * cfg->ui_scale, tm_y + 96 * cfg->ui_scale, 12 * cfg->ui_scale, (Color){235, 110, 110, 255});\n                if (GuiButton((Rectangle){tm_x + tmMgrWindow.width - 62 * cfg->ui_scale, tm_y + 92 * cfg->ui_scale, 52 * cfg->ui_scale, 22 * cfg->ui_scale}, "Copy"))\n                    SetClipboardText(pull_error_detail);\n            }\n            else\n            {\n                DrawUIText(customFont, "Proxy blank = libcurl environment/direct connection", tm_x + 10 * cfg->ui_scale, tm_y + 96 * cfg->ui_scale, 12 * cfg->ui_scale, cfg->text_secondary);\n            }\n\n'''
new_error = '''            float tle_list_top = 96.0f * cfg->ui_scale;\n            if (pull_error_detail[0] != '\\0')\n            {\n                Rectangle error_rec = {tm_x + 10 * cfg->ui_scale, tm_y + 96 * cfg->ui_scale,\n                                       tmMgrWindow.width - 20 * cfg->ui_scale, 60 * cfg->ui_scale};\n                DrawTextRec(customFont, pull_error_detail, error_rec, 11 * cfg->ui_scale,\n                            1.0f * cfg->ui_scale, true, (Color){235, 110, 110, 255});\n                if (GuiButton((Rectangle){tm_x + tmMgrWindow.width - 94 * cfg->ui_scale, tm_y + 158 * cfg->ui_scale,\n                                          84 * cfg->ui_scale, 22 * cfg->ui_scale}, "Copy error"))\n                    SetClipboardText(pull_error_detail);\n                tle_list_top = 186.0f * cfg->ui_scale;\n            }\n\n'''
s = replace_once(s, old_error, new_error, "TLE error area")

old_scroll = '''            GuiScrollPanel((Rectangle){tm_x + 8 * cfg->ui_scale, tm_y + 122 * cfg->ui_scale, tmMgrWindow.width - 16 * cfg->ui_scale, tmMgrWindow.height - 122 * cfg->ui_scale - 8 * cfg->ui_scale}, NULL, contentRec, &tle_mgr_scroll, &viewRec);\n'''
new_scroll = '''            GuiScrollPanel((Rectangle){tm_x + 8 * cfg->ui_scale, tm_y + tle_list_top, tmMgrWindow.width - 16 * cfg->ui_scale, tmMgrWindow.height - tle_list_top - 8 * cfg->ui_scale}, NULL, contentRec, &tle_mgr_scroll, &viewRec);\n'''
s = replace_once(s, old_scroll, new_scroll, "TLE list top")
p.write_text(s)

# Main view: make the legend optional and responsive on small windows.
p = Path("src/main.c")
s = p.read_text()
start = s.index("            /* Screen-space legend: make past/NOW/future semantics explicit. */")
end = s.index("\n        }\n        else\n        {", start)
new_legend = r'''            /* Compact, responsive 2D ground-track legend. */
            if (cfg.show_2d_track_legend)
            {
                float screen_w = (float)GetScreenWidth();
                float legend_scale = fminf(cfg.ui_scale, fmaxf(0.72f, screen_w / 640.0f));
                float margin = 8.0f * legend_scale;
                float lx = margin;
                float ly = 48.0f * legend_scale;
                float lw = fminf(268.0f * legend_scale, screen_w - 2.0f * margin);
                float lh = 62.0f * legend_scale;
                if (lw < 180.0f * legend_scale) lw = 180.0f * legend_scale;

                DrawRectangleRounded((Rectangle){lx, ly, lw, lh}, 0.08f, 6, ApplyAlpha(cfg.ui_bg, 0.85f));
                DrawRectangleRoundedLinesEx((Rectangle){lx, ly, lw, lh}, 0.08f, 6, 1.0f, ApplyAlpha(cfg.ui_secondary, 0.7f));

                const char *title = TextFormat("Tracks: %d past / %d future", cfg.groundtrack_past_orbits, cfg.groundtrack_future_orbits);
                DrawUIText(customFont, title, lx + 8.0f * legend_scale, ly + 6.0f * legend_scale,
                           11.0f * legend_scale, cfg.text_main);

                float line_y = ly + 31.0f * legend_scale;
                float label_y = ly + 43.0f * legend_scale;
                float centers[3] = {lx + lw / 6.0f, lx + lw / 2.0f, lx + 5.0f * lw / 6.0f};
                Color key = cfg.text_main;

                for (int d = 0; d < 3; d++)
                    DrawLineEx((Vector2){centers[0] - (15 - d * 10) * legend_scale, line_y},
                               (Vector2){centers[0] - (9 - d * 10) * legend_scale, line_y},
                               2.0f * legend_scale, ApplyAlpha(key, 0.5f));
                DrawCircleV((Vector2){centers[1], line_y}, 3.5f * legend_scale, key);
                DrawLineEx((Vector2){centers[2] - 16.0f * legend_scale, line_y},
                           (Vector2){centers[2] + 16.0f * legend_scale, line_y},
                           2.0f * legend_scale, key);

                const char *labels[3] = {"PAST", "NOW", "FUTURE"};
                for (int i = 0; i < 3; i++)
                {
                    Vector2 size = MeasureTextEx(customFont, labels[i], 9.0f * legend_scale, 1.0f);
                    DrawUIText(customFont, labels[i], centers[i] - size.x * 0.5f, label_y,
                               9.0f * legend_scale, i == 0 ? cfg.text_secondary : cfg.text_main);
                }
            }'''
s = s[:start] + new_legend + s[end:]
p.write_text(s)

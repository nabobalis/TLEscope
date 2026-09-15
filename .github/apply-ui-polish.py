from pathlib import Path


def replace_once(text, old, new, label):
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{label}: expected 1 match, found {count}")
    return text.replace(old, new, 1)

# Persist a toggle for the 2D track legend.
p = Path("src/types.h")
s = p.read_text()
s = replace_once(
    s,
    "    bool show_2d_mission_labels;\n    bool show_2d_footprints;\n",
    "    bool show_2d_mission_labels;\n    bool show_2d_footprints;\n    bool show_2d_track_legend;\n",
    "types legend field",
)
p.write_text(s)

p = Path("src/config.c")
s = p.read_text()
s = replace_once(
    s,
    "    config->show_2d_footprints = false;\n",
    "    config->show_2d_footprints = false;\n    config->show_2d_track_legend = true;\n",
    "config legend default",
)
s = replace_once(
    s,
    '            config->show_2d_footprints = ParseJsonBool(text, "show_2d_footprints", config->show_2d_footprints);\n',
    '            config->show_2d_footprints = ParseJsonBool(text, "show_2d_footprints", config->show_2d_footprints);\n'
    '            config->show_2d_track_legend = ParseJsonBool(text, "show_2d_track_legend", config->show_2d_track_legend);\n',
    "config legend load",
)
s = replace_once(
    s,
    '    fprintf(file, "    \\"show_2d_footprints\\": %s,\\n", config->show_2d_footprints ? "true" : "false");\n'.replace('\\\\"', '\\"').replace('\\\\n', '\\n'),
    ('    fprintf(file, "    \\"show_2d_footprints\\": %s,\\n", config->show_2d_footprints ? "true" : "false");\n'
     '    fprintf(file, "    \\"show_2d_track_legend\\": %s,\\n", config->show_2d_track_legend ? "true" : "false");\n').replace('\\\\"', '\\"').replace('\\\\n', '\\n'),
    "config legend save",
)
p.write_text(s)

p = Path("src/ui.c")
s = p.read_text()

s = replace_once(
    s,
    "static bool show_exit_dialog = false;\nstatic bool ui_hidden = false;\n",
    "static bool show_exit_dialog = false;\nstatic bool show_tle_error_dialog = false;\nstatic bool ui_hidden = false;\n",
    "error dialog state",
)

s = replace_once(
    s,
    '        snprintf(pull_error_detail, sizeof(pull_error_detail), "%s | %s | HTTP %ld", url, detail, http_code);\n',
    '        snprintf(pull_error_detail, sizeof(pull_error_detail), "Source: %s\\nError: %s\\nHTTP status: %ld", url, detail, http_code);\n',
    "structured pull error",
)

s = replace_once(
    s,
    "    pull_error_detail[0] = '\\0';\n    pull_state = PULL_BUSY;\n",
    "    pull_error_detail[0] = '\\0';\n    show_tle_error_dialog = false;\n    pull_state = PULL_BUSY;\n",
    "clear error dialog on retry",
)

s = replace_once(
    s,
    "    if (h == (uintptr_t)-1L) { pull_state = PULL_ERROR; return; }\n",
    "    if (h == (uintptr_t)-1L) { snprintf(pull_error_detail, sizeof(pull_error_detail), \"Could not start the TLE download thread\"); pull_state = PULL_ERROR; return; }\n",
    "windows thread error",
)
s = replace_once(
    s,
    "    if (pthread_create(&pull_thread, NULL, PullTLEThread, NULL) != 0)\n    { pull_state = PULL_ERROR; return; }\n",
    "    if (pthread_create(&pull_thread, NULL, PullTLEThread, NULL) != 0)\n    { snprintf(pull_error_detail, sizeof(pull_error_detail), \"Could not start the TLE download thread\"); pull_state = PULL_ERROR; return; }\n",
    "pthread error",
)

s = replace_once(
    s,
    "        data_tle_epoch = time(NULL);\n        pull_state = PULL_IDLE;\n    }\n}\n\nstatic void CalculateLunarPass",
    "        data_tle_epoch = time(NULL);\n        pull_state = PULL_IDLE;\n    }\n    else if (pull_state == PULL_ERROR)\n    {\n        show_tle_error_dialog = true;\n        pull_state = PULL_IDLE;\n    }\n}\n\nstatic void CalculateLunarPass",
    "show download error dialog",
)

s = replace_once(
    s,
    "    if (ui_hidden && !show_exit_dialog && !cfg->show_first_run_dialog)\n        return false;\n    if (show_exit_dialog || cfg->show_first_run_dialog)\n        return true;\n",
    "    if (ui_hidden && !show_exit_dialog && !show_tle_error_dialog && !cfg->show_first_run_dialog)\n        return false;\n    if (show_exit_dialog || show_tle_error_dialog || cfg->show_first_run_dialog)\n        return true;\n",
    "mouse over modal dialogs",
)

s = replace_once(
    s,
    "    // Keep first-run and exit confirmation dialogs reachable even in clean view.\n    if (ui_hidden && !show_exit_dialog && !cfg->show_first_run_dialog)\n        return;\n",
    "    // Keep modal dialogs reachable even in clean view.\n    if (ui_hidden && !show_exit_dialog && !show_tle_error_dialog && !cfg->show_first_run_dialog)\n        return;\n",
    "clean view modal dialogs",
)

s = replace_once(
    s,
    '            GuiSetTooltip("Optional proxy URL, e.g. http://proxy.example:8080. Leave blank for libcurl defaults/environment.");\n',
    '            GuiSetTooltip("Optional proxy URL, e.g. http://proxy.example:8080. Leave blank to use the normal network settings.");\n',
    "proxy tooltip",
)

old_inline_error = '''            if (pull_error_detail[0] != '\\0')\n            {\n                char short_error[80];\n                size_t err_len = strlen(pull_error_detail);\n                snprintf(short_error, sizeof(short_error), "%.68s%s", pull_error_detail, err_len > 68 ? "..." : "");\n                DrawUIText(customFont, short_error, tm_x + 10 * cfg->ui_scale, tm_y + 96 * cfg->ui_scale, 12 * cfg->ui_scale, (Color){235, 110, 110, 255});\n                if (GuiButton((Rectangle){tm_x + tmMgrWindow.width - 62 * cfg->ui_scale, tm_y + 92 * cfg->ui_scale, 52 * cfg->ui_scale, 22 * cfg->ui_scale}, "Copy"))\n                    SetClipboardText(pull_error_detail);\n            }\n            else\n            {\n                DrawUIText(customFont, "Proxy blank = libcurl environment/direct connection", tm_x + 10 * cfg->ui_scale, tm_y + 96 * cfg->ui_scale, 12 * cfg->ui_scale, cfg->text_secondary);\n            }\n\n'''
s = replace_once(s, old_inline_error, "", "remove inline TLE error/status text")

s = replace_once(
    s,
    "            GuiScrollPanel((Rectangle){tm_x + 8 * cfg->ui_scale, tm_y + 122 * cfg->ui_scale, tmMgrWindow.width - 16 * cfg->ui_scale, tmMgrWindow.height - 122 * cfg->ui_scale - 8 * cfg->ui_scale}, NULL, contentRec, &tle_mgr_scroll, &viewRec);\n",
    "            GuiScrollPanel((Rectangle){tm_x + 8 * cfg->ui_scale, tm_y + 96 * cfg->ui_scale, tmMgrWindow.width - 16 * cfg->ui_scale, tmMgrWindow.height - 96 * cfg->ui_scale - 8 * cfg->ui_scale}, NULL, contentRec, &tle_mgr_scroll, &viewRec);\n",
    "move TLE list up",
)

old_settings = '''            GuiCheckBox((Rectangle){sw_x + 10 * cfg->ui_scale, sy, 20 * cfg->ui_scale, 20 * cfg->ui_scale}, "Mission Labels", &cfg->show_2d_mission_labels);\n            sy += 25 * cfg->ui_scale;\n            GuiCheckBox((Rectangle){sw_x + 10 * cfg->ui_scale, sy, 20 * cfg->ui_scale, 20 * cfg->ui_scale}, "Coverage Footprints", &cfg->show_2d_footprints);\n            sy += 30 * cfg->ui_scale;\n'''
new_settings = '''            GuiCheckBox((Rectangle){sw_x + 10 * cfg->ui_scale, sy, 20 * cfg->ui_scale, 20 * cfg->ui_scale}, "Mission Labels", &cfg->show_2d_mission_labels);\n            sy += 25 * cfg->ui_scale;\n            GuiCheckBox((Rectangle){sw_x + 10 * cfg->ui_scale, sy, 20 * cfg->ui_scale, 20 * cfg->ui_scale}, "Track Legend", &cfg->show_2d_track_legend);\n            sy += 25 * cfg->ui_scale;\n            GuiCheckBox((Rectangle){sw_x + 10 * cfg->ui_scale, sy, 20 * cfg->ui_scale, 20 * cfg->ui_scale}, "Coverage Footprints", &cfg->show_2d_footprints);\n            sy += 30 * cfg->ui_scale;\n'''
s = replace_once(s, old_settings, new_settings, "legend setting")

error_dialog = r'''
    if (show_tle_error_dialog)
    {
        DrawRectangle(0, 0, GetScreenWidth(), GetScreenHeight(), ApplyAlpha(cfg->overlay_dim, 150.0f / 180.0f));
        float ew = fminf(520.0f * cfg->ui_scale, fmaxf(260.0f, (float)GetScreenWidth() - 24.0f));
        float eh = fminf(240.0f * cfg->ui_scale, fmaxf(170.0f, (float)GetScreenHeight() - 24.0f));
        Rectangle errorRec = {(GetScreenWidth() - ew) / 2.0f, (GetScreenHeight() - eh) / 2.0f, ew, eh};
        if (DrawMaterialWindow(errorRec, "TLE Download Error", cfg, customFont, true))
            show_tle_error_dialog = false;

        float dialog_scale = fminf(cfg->ui_scale, fmaxf(0.75f, ew / 520.0f));
        DrawUIText(customFont, "The TLE refresh failed. Your existing TLE data was kept.",
                   errorRec.x + 14.0f, errorRec.y + 42.0f, 12.0f * dialog_scale, cfg->text_main);
        Rectangle detailRec = {errorRec.x + 14.0f, errorRec.y + 66.0f,
                               errorRec.width - 28.0f, errorRec.height - 116.0f};
        DrawTextRec(customFont, pull_error_detail[0] ? pull_error_detail : "Unknown download error",
                    detailRec, 11.0f * dialog_scale, 1.0f, true, (Color){235, 110, 110, 255});
        if (GuiButton((Rectangle){errorRec.x + errorRec.width - 92.0f, errorRec.y + errorRec.height - 38.0f,
                                  78.0f, 26.0f}, "Close"))
            show_tle_error_dialog = false;
    }

'''
s = replace_once(s, "    if (show_exit_dialog)\n    {\n", error_dialog + "    if (show_exit_dialog)\n    {\n", "draw error dialog")
p.write_text(s)

# Main view: optional, compact legend which scales down on narrow windows.
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

                DrawRectangleRounded((Rectangle){lx, ly, lw, lh}, 0.08f, 6, ApplyAlpha(cfg.ui_bg, 0.85f));
                DrawRectangleRoundedLinesEx((Rectangle){lx, ly, lw, lh}, 0.08f, 6, 1.0f, ApplyAlpha(cfg.ui_secondary, 0.7f));
                DrawUIText(customFont, TextFormat("Tracks: %d past / %d future", cfg.groundtrack_past_orbits, cfg.groundtrack_future_orbits),
                           lx + 8.0f * legend_scale, ly + 6.0f * legend_scale,
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

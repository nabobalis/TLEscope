from pathlib import Path

path = Path("src/ui.c")
text = path.read_text()


def replace_once(old, new):
    global text
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"expected one match, found {count}: {old[:120]!r}")
    text = text.replace(old, new, 1)


replace_once(
    'static char sat_search_text[64] = "";\nstatic bool edit_sat_search = false;\n',
    'static char sat_search_text[64] = "";\nstatic bool edit_sat_search = false;\nstatic bool sat_mgr_active_only = false;\n',
)

replace_once(
    '''            bool doCheckAll = GuiButton((Rectangle){sm_x + smWindow.width - 75 * cfg->ui_scale, sm_y + 35 * cfg->ui_scale, 30 * cfg->ui_scale, 24 * cfg->ui_scale}, "#80#");
            bool doUncheckAll = GuiButton((Rectangle){sm_x + smWindow.width - 40 * cfg->ui_scale, sm_y + 35 * cfg->ui_scale, 30 * cfg->ui_scale, 24 * cfg->ui_scale}, "#79#");

            int filtered_indices[MAX_SATELLITES], filtered_count = 0;
''',
    '''            bool doCheckAll = GuiButton((Rectangle){sm_x + smWindow.width - 75 * cfg->ui_scale, sm_y + 35 * cfg->ui_scale, 30 * cfg->ui_scale, 24 * cfg->ui_scale}, "#80#");
            bool doUncheckAll = GuiButton((Rectangle){sm_x + smWindow.width - 40 * cfg->ui_scale, sm_y + 35 * cfg->ui_scale, 30 * cfg->ui_scale, 24 * cfg->ui_scale}, "#79#");

            int active_count = 0;
            for (int i = 0; i < sat_count; i++)
                if (satellites[i].is_active) active_count++;

            bool active_only_before = sat_mgr_active_only;
            GuiCheckBox((Rectangle){sm_x + 10 * cfg->ui_scale, sm_y + 65 * cfg->ui_scale, 18 * cfg->ui_scale, 18 * cfg->ui_scale}, "Active only", &sat_mgr_active_only);
            DrawUIText(customFont, TextFormat("%d active", active_count),
                       sm_x + smWindow.width - 86 * cfg->ui_scale, sm_y + 67 * cfg->ui_scale,
                       14 * cfg->ui_scale, cfg->text_secondary);
            if (active_only_before != sat_mgr_active_only)
                sat_mgr_scroll = (Vector2){0};

            int filtered_indices[MAX_SATELLITES], filtered_count = 0;
''',
)

replace_once(
    '''            for (int i = 0; i < sat_count; i++)
            {
                if (string_contains_ignore_case(satellites[i].name, sat_search_text) || 
''',
    '''            for (int i = 0; i < sat_count; i++)
            {
                if (sat_mgr_active_only && !satellites[i].is_active)
                    continue;

                if (string_contains_ignore_case(satellites[i].name, sat_search_text) || 
''',
)

replace_once(
    'GuiScrollPanel((Rectangle){sm_x + 8 * cfg->ui_scale, sm_y + 70 * cfg->ui_scale, smWindow.width - 16 * cfg->ui_scale, smWindow.height - 70 * cfg->ui_scale - 8 * cfg->ui_scale}, NULL, contentRec, &sat_mgr_scroll, &viewRec);',
    'GuiScrollPanel((Rectangle){sm_x + 8 * cfg->ui_scale, sm_y + 92 * cfg->ui_scale, smWindow.width - 16 * cfg->ui_scale, smWindow.height - 92 * cfg->ui_scale - 8 * cfg->ui_scale}, NULL, contentRec, &sat_mgr_scroll, &viewRec);',
)

path.write_text(text)

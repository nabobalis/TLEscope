from pathlib import Path

p = Path("src/ui.c")
text = p.read_text()
text = text.replace("250 * cfg->ui_scale, 650 * cfg->ui_scale", "250 * cfg->ui_scale, 700 * cfg->ui_scale")
old = '''                Rectangle auto_color = {cur_x + 5 * cfg->ui_scale, cur_y, 120 * cfg->ui_scale, 24 * cfg->ui_scale};
                if (is_topmost && CheckCollisionPointRec(GetMousePosition(), viewRec) && GuiButton(auto_color, "Auto color"))
                {
                    ResetMissionTrackColor(cfg, sat->norad_id);
                    SaveAppConfig("settings.json", cfg);
                }
'''
new = '''                Rectangle auto_color = {cur_x + 5 * cfg->ui_scale, cur_y, 120 * cfg->ui_scale, 24 * cfg->ui_scale};
                bool auto_color_clicked = GuiButton(auto_color, "Auto color");
                if (is_topmost && CheckCollisionPointRec(GetMousePosition(), viewRec) && auto_color_clicked)
                {
                    ResetMissionTrackColor(cfg, sat->norad_id);
                    SaveAppConfig("settings.json", cfg);
                }
'''
if text.count(old) != 1:
    raise RuntimeError(f"expected one Auto color block, found {text.count(old)}")
text = text.replace(old, new, 1)
p.write_text(text)

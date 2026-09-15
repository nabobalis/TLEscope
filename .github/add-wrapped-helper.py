from pathlib import Path

p = Path("src/ui.c")
s = p.read_text()

anchor = 'void DrawUIText(Font font, const char *text, float x, float y, float size, Color color) { DrawTextEx(font, text, (Vector2){x, y}, size, 1.0f, color); }\n'
helper = r'''

static void DrawWrappedUIText(Font font, const char *text, Rectangle bounds, float size, Color color)
{
    if (!text || bounds.width <= 0 || bounds.height <= 0) return;
    char line[512];
    int len = 0;
    float y = bounds.y;
    float line_height = size + 3.0f;

    for (const char *p = text; ; p++)
    {
        char c = *p;
        bool flush = (c == '\n' || c == '\0');
        if (!flush && len < (int)sizeof(line) - 2)
        {
            line[len++] = c;
            line[len] = '\0';
            if (MeasureTextEx(font, line, size, 1.0f).x > bounds.width && len > 1)
            {
                char carry = line[--len];
                line[len] = '\0';
                if (y + size > bounds.y + bounds.height) return;
                DrawTextEx(font, line, (Vector2){bounds.x, y}, size, 1.0f, color);
                y += line_height;
                line[0] = carry;
                line[1] = '\0';
                len = 1;
            }
        }
        if (flush)
        {
            if (len > 0)
            {
                if (y + size > bounds.y + bounds.height) return;
                DrawTextEx(font, line, (Vector2){bounds.x, y}, size, 1.0f, color);
                y += line_height;
                len = 0;
                line[0] = '\0';
            }
            if (c == '\0') break;
        }
    }
}
'''

if s.count(anchor) != 1:
    raise SystemExit("DrawUIText anchor not found")
s = s.replace(anchor, anchor + helper, 1)

old = '''        DrawTextRec(customFont, pull_error_detail[0] ? pull_error_detail : "Unknown download error",\n                    detailRec, 11.0f * dialog_scale, 1.0f, true, (Color){235, 110, 110, 255});\n'''
new = '''        DrawWrappedUIText(customFont, pull_error_detail[0] ? pull_error_detail : "Unknown download error",\n                          detailRec, 11.0f * dialog_scale, (Color){235, 110, 110, 255});\n'''
if s.count(old) != 1:
    raise SystemExit("DrawTextRec call not found")

p.write_text(s.replace(old, new, 1))

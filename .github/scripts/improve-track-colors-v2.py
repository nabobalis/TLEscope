from pathlib import Path
import runpy

runpy.run_path('.github/scripts/improve-track-colors.py', run_name='__main__')

header = Path('src/config.h')
text = header.read_text()
marker = 'void SaveAppConfig(const char *filename, AppConfig *config);\n\n'
replacement = 'void SaveAppConfig(const char *filename, AppConfig *config);\nColor ParseHexColor(const char *hexStr, Color fallback);\n\n'
if marker not in text:
    raise SystemExit('config.h insertion point not found')
header.write_text(text.replace(marker, replacement, 1))

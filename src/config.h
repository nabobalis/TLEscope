#ifndef CONFIG_H
#define CONFIG_H

#include "types.h"

void LoadAppConfig(const char *filename, AppConfig *config);
void SaveAppConfig(const char *filename, AppConfig *config);
Color ParseHexColor(const char *hexStr, Color fallback);

int GetMissionTrackPaletteSize(void);
Color GetMissionTrackPaletteColor(int index);
Color GetMissionTrackColor(const AppConfig *config, const char *norad_id);
void SetMissionTrackColor(AppConfig *config, const char *norad_id, Color color);
void ResetMissionTrackColor(AppConfig *config, const char *norad_id);

#endif // CONFIG_H

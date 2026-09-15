/* tools_registry.cpp - The single registry of all tool panels. */
#include "tools_registry.h"
#include "tools_common.h"
#include "tools.h"
#include "IconsFontAwesome6.h"

const PanelDef g_panel_defs[PANEL_COUNT] = {
    { PANEL_SAT_MGR,      "Satellite Manager",  ICON_FA_SATELLITE,       PANEL_CAT_CORE,  SIDEBAR_LEFT,  true,  true,  DrawPanelSatMgr },
    { PANEL_DATA_SOURCES, "Data Sources",        ICON_FA_DATABASE,        PANEL_CAT_CORE,  SIDEBAR_LEFT,  true,  true,  DrawPanelDataSourcesWithProxy },
    { PANEL_LAYERS,       "Layers",              ICON_FA_LAYER_GROUP,     PANEL_CAT_CORE,  SIDEBAR_LEFT,  true,  true,  DrawPanelLayers, DrawSceneLayers },
    { PANEL_SCOPE,        "Scope",               ICON_FA_CROSSHAIRS,      PANEL_CAT_EXTRA, SIDEBAR_LEFT,  false, false, DrawPanelScope },
    { PANEL_ROTATOR,      "Rotator Control",     ICON_FA_TURN_UP,         PANEL_CAT_EXTRA, SIDEBAR_LEFT,  false, false, DrawPanelRotator },
    { PANEL_SAT_INFO,     "Satellite Info",      ICON_FA_CIRCLE_INFO,     PANEL_CAT_CORE,  SIDEBAR_RIGHT, true,  true,  DrawPanelSatInfo },
    { PANEL_PASSES,       "Satellite Passes",    ICON_FA_ROUTE,           PANEL_CAT_CORE,  SIDEBAR_RIGHT, false, true,  DrawPanelPasses },
    { PANEL_POLAR_PLOT,   "Polar Plot",          ICON_FA_COMPASS,         PANEL_CAT_CORE,  SIDEBAR_RIGHT, false, true,  DrawPanelPolarPlot, DrawScenePolarPlot },
    { PANEL_DOPPLER,      "Doppler Analysis",    ICON_FA_TOWER_BROADCAST, PANEL_CAT_EXTRA, SIDEBAR_RIGHT, false, false, DrawPanelDoppler },
    { PANEL_LOG,          "Log",                 ICON_FA_LIST,            PANEL_CAT_DEBUG, SIDEBAR_RIGHT, false, false, DrawPanelLog },
    { PANEL_TRXDB,        "TRXDB NORAD TEST",    ICON_FA_SATELLITE_DISH,  PANEL_CAT_EXTRA, SIDEBAR_RIGHT, false, false, DrawPanelTrxdb },
};

const int g_panel_count = PANEL_COUNT;

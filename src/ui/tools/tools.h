#ifndef TOOLS_H
#define TOOLS_H

#include "core/config.h"
#include "ui/ui.h"
#include "tools_scene.h"

void DrawPanelSatMgr(UIContext *ctx, AppConfig *cfg);
void DrawPanelDataSources(UIContext *ctx, AppConfig *cfg);
void DrawPanelDataSourcesWithProxy(UIContext *ctx, AppConfig *cfg);
void DrawPanelLayers(UIContext *ctx, AppConfig *cfg);
void DrawPanelTimeCtrl(UIContext *ctx, AppConfig *cfg);
void DrawPanelScope(UIContext *ctx, AppConfig *cfg);
void DrawPanelRotator(UIContext *ctx, AppConfig *cfg);
void DrawPanelSatInfo(UIContext *ctx, AppConfig *cfg);
void DrawPanelPasses(UIContext *ctx, AppConfig *cfg);
void DrawPanelPolarPlot(UIContext *ctx, AppConfig *cfg);
void DrawPanelDoppler(UIContext *ctx, AppConfig *cfg);
void DrawPanelLog(UIContext *ctx, AppConfig *cfg);
void DrawPanelTrxdb(UIContext *ctx, AppConfig *cfg);

void DrawSceneLayers(SceneContext *sctx, AppConfig *cfg);
void DrawScenePolarPlot(SceneContext *sctx, AppConfig *cfg);

#endif /* TOOLS_H */

/* tool_layers.cpp - Layers panel */
#include "tools.h"
#include "tools_common.h"
#include "core/theme.h"
#include "core/config.h"
#include "ui/labels.h"
#include "ui/tools/tools_settings.h"
#include <cmath>
#include <raylib.h>
#include "imgui.h"
#include "IconsFontAwesome6.h"

static const char *GRID_KEY = "map2d.latlon_grid";

void DrawPanelLayers(UIContext *ctx, AppConfig *cfg)
{
    (void)ctx; ImGui::PushTextWrapPos(0.0f); const float icon_w=24.0f;
    auto row=[&](const char *label,bool *value,const char *icon,const char *tip){ImGui::PushStyleColor(ImGuiCol_Text,ThemeColor(*value?g_theme.ui.ui_accent:g_theme.ui.text_secondary));ImU32 col=ImGui::GetColorU32(ImGuiCol_Text);ImVec2 sz=ImGui::CalcTextSize(icon),p=ImGui::GetCursorScreenPos();ImGui::GetWindowDrawList()->AddText(ImVec2(p.x+(icon_w-sz.x)*0.5f,p.y),col,icon);ImGui::PopStyleColor();ImGui::Dummy(ImVec2(icon_w,ImGui::GetFrameHeight()));ImGui::SameLine();ImGui::Checkbox(label,value);if(tip&&ImGui::IsItemHovered())ImGui::SetTooltip("%s",tip);};
    row("Clouds",&cfg->show_clouds,ICON_FA_CLOUD,"Show cloud layer (C)"); row("Night Lights",&cfg->show_night_lights,ICON_FA_MOON,"Show night-side city lights (N)"); row("Markers",&cfg->show_markers,ICON_FA_MAP_PIN,"Show ground markers (L)"); row("Scattering",&cfg->show_scattering,ICON_FA_SUN,"Atmospheric scattering effect"); row("Skybox",&cfg->show_skybox,ICON_FA_STAR,"Show starfield skybox"); row("Highlight Sunlit",&cfg->highlight_sunlit,ICON_FA_BOLT,"Highlight sunlit portions of orbits"); row("Slant Range",&cfg->show_slant_range,ICON_FA_RULER,"Show slant range line to home"); row("Ground Coverage",&cfg->show_ground_coverage,ICON_FA_ROUTE,"Show the line-of-sight ground coverage footprint"); row("Apsides",&cfg->show_apsides,ICON_FA_CIRCLE_DOT,"Show perigee/apogee markers and altitude labels");
    bool enabled=ToolSettingGetBool(cfg,GRID_KEY,false);if(ImGui::Checkbox("2D Lat/Lon Grid",&enabled))ToolSettingSetBool(cfg,GRID_KEY,enabled);
    ImGui::Separator(); bool labels=ToolSettingGetBool(cfg,LABELS_KEY_ENABLED,true);if(ImGui::Checkbox("Labels",&labels))ToolSettingSetBool(cfg,LABELS_KEY_ENABLED,labels);int mode=ToolSettingGetInt(cfg,LABELS_KEY_MODE,LABELS_MODE_ACTIVE_ONLY);const char *modes[]={"Active only","All","None"};ImGui::SetNextItemWidth(-1);if(ImGui::Combo("##label_mode",&mode,modes,3))ToolSettingSetInt(cfg,LABELS_KEY_MODE,mode);bool alt=ToolSettingGetBool(cfg,LABELS_KEY_ALTITUDE,false);if(ImGui::Checkbox("Label Altitude",&alt))ToolSettingSetBool(cfg,LABELS_KEY_ALTITUDE,alt);float size=ToolSettingGetFloat(cfg,LABELS_KEY_SIZE,1.0f);if(ImGui::SliderFloat("Label Size",&size,0.5f,1.5f,"%.2fx"))ToolSettingSetFloat(cfg,LABELS_KEY_SIZE,size);bool bg=ToolSettingGetBool(cfg,LABELS_KEY_BG,true);if(ImGui::Checkbox("Label Background",&bg))ToolSettingSetBool(cfg,LABELS_KEY_BG,bg);int max_count=ToolSettingGetInt(cfg,LABELS_KEY_MAX_COUNT,200);if(ImGui::SliderInt("Max Labels",&max_count,10,1000))ToolSettingSetInt(cfg,LABELS_KEY_MAX_COUNT,max_count);ImGui::PopTextWrapPos();
}
void DrawSceneLayers(SceneContext *sctx,AppConfig *cfg){if(!sctx->is_2d_view||!sctx->camera2d||!ToolSettingGetBool(cfg,GRID_KEY,false))return;float zoom=fmaxf(sctx->camera2d->zoom,0.10f),thin=0.8f/zoom,strong=1.1f/zoom;Color tc=g_theme.ui.text_main;tc.a=(unsigned char)(tc.a*0.15f);Color sc=g_theme.ui.text_main;sc.a=(unsigned char)(sc.a*0.28f);for(int lon=-150;lon<=150;lon+=30){float x=((float)lon/360.0f)*sctx->map_w;DrawLineEx({x,-sctx->map_h*0.5f},{x,sctx->map_h*0.5f},lon==0?strong:thin,lon==0?sc:tc);}for(int lat=-60;lat<=60;lat+=30){float y=-((float)lat/180.0f)*sctx->map_h;DrawLineEx({-sctx->map_w*0.5f,y},{sctx->map_w*0.5f,y},lat==0?strong:thin,lat==0?sc:tc);}}

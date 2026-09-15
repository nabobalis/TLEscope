/* tool_data_sources_proxy.cpp - persisted proxy wrapper for Data Sources */
#include "tools.h"
#include "core/config.h"
#include "ui/tools/tools_settings.h"
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include "imgui.h"

static const char *PROXY_KEY = "data.proxy";

static void ApplyProxy(const char *proxy)
{
#if defined(_WIN32) || defined(_WIN64)
    _putenv_s("HTTP_PROXY", proxy ? proxy : "");
    _putenv_s("HTTPS_PROXY", proxy ? proxy : "");
    _putenv_s("ALL_PROXY", proxy ? proxy : "");
#else
    if (proxy && proxy[0])
    {
        setenv("HTTP_PROXY", proxy, 1);
        setenv("HTTPS_PROXY", proxy, 1);
        setenv("ALL_PROXY", proxy, 1);
    }
    else
    {
        unsetenv("HTTP_PROXY");
        unsetenv("HTTPS_PROXY");
        unsetenv("ALL_PROXY");
    }
#endif
}

void DrawPanelDataSourcesWithProxy(UIContext *ctx, AppConfig *cfg)
{
    static bool initialized = false;
    static char proxy[256] = "";
    if (!initialized)
    {
        const char *saved = ToolSettingGetString(cfg, PROXY_KEY, "");
        snprintf(proxy, sizeof(proxy), "%s", saved ? saved : "");
        ApplyProxy(proxy);
        initialized = true;
    }

    if (ImGui::CollapsingHeader("Network Proxy"))
    {
        ImGui::TextWrapped("Optional proxy for network data pulls. Leave blank to use the normal libcurl environment/direct connection.");
        ImGui::SetNextItemWidth(-1.0f);
        ImGui::InputText("##data_proxy", proxy, sizeof(proxy));
        if (ImGui::Button("Apply and Save"))
        {
            ToolSettingSetString(cfg, PROXY_KEY, proxy);
            ApplyProxy(proxy);
            SaveAppConfig("settings.json", cfg);
        }
        ImGui::SameLine();
        if (ImGui::Button("Clear"))
        {
            proxy[0] = '\0';
            ToolSettingSetString(cfg, PROXY_KEY, "");
            ApplyProxy("");
            SaveAppConfig("settings.json", cfg);
        }
    }

    DrawPanelDataSources(ctx, cfg);
}

from pathlib import Path

# types.h: persist an optional libcurl proxy override.
p = Path('src/types.h')
s = p.read_text()
old = '''    CustomTLESource custom_tle_sources[MAX_CUSTOM_TLE_SOURCES];\n    int custom_tle_source_count;\n\n    char manual_tles[MAX_MANUAL_TLES][512];\n'''
new = '''    CustomTLESource custom_tle_sources[MAX_CUSTOM_TLE_SOURCES];\n    int custom_tle_source_count;\n    char tle_proxy[256];\n\n    char manual_tles[MAX_MANUAL_TLES][512];\n'''
if old not in s:
    raise SystemExit('types.h proxy insertion marker not found')
s = s.replace(old, new, 1)
p.write_text(s)

# config.c: load/save proxy setting.
p = Path('src/config.c')
s = p.read_text()
old = '''    config->custom_tle_source_count = 0;\n    config->mission_track_color_count = 0;\n'''
new = '''    config->custom_tle_source_count = 0;\n    config->tle_proxy[0] = '\\0';\n    config->mission_track_color_count = 0;\n'''
if old not in s:
    raise SystemExit('config defaults marker not found')
s = s.replace(old, new, 1)

old = '''            config->show_2d_mission_labels = ParseJsonBool(text, "show_2d_mission_labels", config->show_2d_mission_labels);\n            config->show_2d_footprints = ParseJsonBool(text, "show_2d_footprints", config->show_2d_footprints);\n\n            // load manual TLEs\n'''
new = '''            config->show_2d_mission_labels = ParseJsonBool(text, "show_2d_mission_labels", config->show_2d_mission_labels);\n            config->show_2d_footprints = ParseJsonBool(text, "show_2d_footprints", config->show_2d_footprints);\n\n            ptr = strstr(text, "\\\"tle_proxy\\\"");\n            if (ptr)\n            {\n                ptr = strchr(ptr, ':');\n                if (ptr)\n                {\n                    char *quote_start = strchr(ptr, '\\"');\n                    if (quote_start)\n                        sscanf(quote_start + 1, "%255[^\\\"]", config->tle_proxy);\n                }\n            }\n\n            // load manual TLEs\n'''
if old not in s:
    raise SystemExit('config load marker not found')
s = s.replace(old, new, 1)

old = '''    fprintf(file, "    \\\"show_first_run_dialog\\\": %s,\\n", config->show_first_run_dialog ? "true" : "false");\n\n    if (config->mission_track_color_count > 0)\n'''
new = '''    fprintf(file, "    \\\"show_first_run_dialog\\\": %s,\\n", config->show_first_run_dialog ? "true" : "false");\n    fprintf(file, "    \\\"tle_proxy\\\": \\\"%s\\\",\\n", config->tle_proxy);\n\n    if (config->mission_track_color_count > 0)\n'''
if old not in s:
    raise SystemExit('config save marker not found')
s = s.replace(old, new, 1)
p.write_text(s)

# ui.c: capture curl errors, preserve old data on failure, and expose proxy/error UI.
p = Path('src/ui.c')
s = p.read_text()
old = '''static volatile int pull_state = PULL_IDLE;\nstatic volatile bool pull_partial = false;\nstatic AppConfig *pull_cfg = NULL;\n'''
new = '''static volatile int pull_state = PULL_IDLE;\nstatic volatile bool pull_partial = false;\nstatic char pull_error_detail[512] = "";\nstatic bool edit_tle_proxy = false;\nstatic AppConfig *pull_cfg = NULL;\n'''
if old not in s:
    raise SystemExit('ui pull state marker not found')
s = s.replace(old, new, 1)

old_start = s.index('static bool DownloadTLESource(CURL *curl, const char *url, FILE *out)')
old_end = s.index('\nstatic void ReloadTLEsLocally', old_start)
new_func = r'''static bool DownloadTLESource(CURL *curl, const char *url, FILE *out, const AppConfig *cfg)
{
    if (!curl || !url || !out) return false;

    struct MemoryStruct chunk;
    chunk.memory = malloc(1);
    chunk.size = 0;
    char curl_error[CURL_ERROR_SIZE] = {0};

    curl_easy_setopt(curl, CURLOPT_URL, url);
    curl_easy_setopt(curl, CURLOPT_WRITEDATA, (void *)&chunk);
    curl_easy_setopt(curl, CURLOPT_WRITEFUNCTION, write_memory_callback);
    curl_easy_setopt(curl, CURLOPT_FOLLOWLOCATION, 1L);
    curl_easy_setopt(curl, CURLOPT_ACCEPT_ENCODING, ""); /* handle compression */
    curl_easy_setopt(curl, CURLOPT_ERRORBUFFER, curl_error);
    curl_easy_setopt(curl, CURLOPT_CONNECTTIMEOUT, 15L);
    curl_easy_setopt(curl, CURLOPT_TIMEOUT, 45L);

    /* libcurl already honors http_proxy/HTTPS_PROXY/ALL_PROXY.  This optional
       setting is mainly for GUI-launched apps that do not inherit shell proxy
       variables (common on managed macOS systems). */
    if (cfg && cfg->tle_proxy[0] != '\0')
        curl_easy_setopt(curl, CURLOPT_PROXY, cfg->tle_proxy);

    char user_agent[256];
    snprintf(user_agent, sizeof(user_agent), "Mozilla 5.0 (compatible; TLEscope/%s; +https://github.com/aweeri/TLEscope)", TLESCOPE_VERSION);
    curl_easy_setopt(curl, CURLOPT_USERAGENT, user_agent);

#if defined(_WIN32) || defined(_WIN64)
    curl_easy_setopt(curl, CURLOPT_SSL_VERIFYPEER, 0L);
#endif

    CURLcode res = curl_easy_perform(curl);
    long http_code = 0;
    curl_easy_getinfo(curl, CURLINFO_RESPONSE_CODE, &http_code);

    bool ok = (res == CURLE_OK && http_code == 200);
    if (ok)
    {
        fwrite(chunk.memory, 1, chunk.size, out);
        fprintf(out, "\r\n");
    }
    else
    {
        const char *detail = curl_error[0] ? curl_error : curl_easy_strerror(res);
        snprintf(pull_error_detail, sizeof(pull_error_detail), "%s | %s | HTTP %ld", url, detail, http_code);
        printf("Failed to download %s: %s (HTTP %ld)\n", url, detail, http_code);
    }

    free(chunk.memory);
    return ok;
}
'''
s = s[:old_start] + new_func + s[old_end:]

old_start = s.index('static void *PullTLEThread(void *arg)')
old_end = s.index('\n#if defined(_WIN32) || defined(_WIN64)\nstatic void PullTLEThreadWin', old_start)
new_thread = r'''static void *PullTLEThread(void *arg)
{
    (void)arg;
    AppConfig *cfg = pull_cfg;

    FILE *out = fopen("data.tle.tmp", "wb");
    if (!out)
    {
        snprintf(pull_error_detail, sizeof(pull_error_detail), "Could not create data.tle.tmp");
        __sync_synchronize();
        pull_state = PULL_ERROR;
        return NULL;
    }

    unsigned int mask = 0, ret_mask = 0, cust_mask = 0;
    for (int i = 0; i < 25; i++)
        if (celestrak_selected[i]) mask |= (1 << i);
    for (int i = 0; i < NUM_RETLECTOR_SOURCES; i++)
        if (retlector_selected[i]) ret_mask |= (1 << i);
    for (int i = 0; i < cfg->custom_tle_source_count; i++)
        if (cfg->custom_tle_sources[i].selected) cust_mask |= (1 << i);

    fprintf(out, "# EPOCH:%ld MASK:%u CUST_MASK:%u RET_MASK:%u\r\n", (long)time(NULL), mask, cust_mask, ret_mask);

    int ok_count = 0, fail_count = 0;
    if (mask == 0 && ret_mask == 0 && cust_mask == 0)
    {
        snprintf(pull_error_detail, sizeof(pull_error_detail), "No TLE sources selected");
        fail_count = 1;
    }
    else
    {
        CURL *curl = curl_easy_init();
        if (curl)
        {
            for (int i = 0; i < NUM_RETLECTOR_SOURCES; i++)
                if (ret_mask & (1 << i))
                { if (DownloadTLESource(curl, RETLECTOR_SOURCES[i].url, out, cfg)) ok_count++; else fail_count++; }

            for (int i = 0; i < 25; i++)
                if (mask & (1 << i))
                { if (DownloadTLESource(curl, SOURCES[i].url, out, cfg)) ok_count++; else fail_count++; }

            for (int i = 0; i < cfg->custom_tle_source_count; i++)
                if (cust_mask & (1 << i))
                { if (DownloadTLESource(curl, cfg->custom_tle_sources[i].url, out, cfg)) ok_count++; else fail_count++; }

            curl_easy_cleanup(curl);
        }
        else
        {
            snprintf(pull_error_detail, sizeof(pull_error_detail), "Failed to initialize libcurl");
            fail_count = 1;
            printf("Failed to initialize libcurl.\n");
        }
    }

    fclose(out);

    if (ok_count > 0)
    {
#if defined(_WIN32) || defined(_WIN64)
        remove("data.tle");
#endif
        if (rename("data.tle.tmp", "data.tle") != 0)
        {
            snprintf(pull_error_detail, sizeof(pull_error_detail), "Downloaded TLEs but could not replace data.tle");
            remove("data.tle.tmp");
            __sync_synchronize();
            pull_state = PULL_ERROR;
            return NULL;
        }
    }
    else
    {
        /* A failed refresh must never wipe the last known-good TLE cache. */
        remove("data.tle.tmp");
    }

    pull_partial = (ok_count > 0 && fail_count > 0);
    __sync_synchronize(); /* publish error text/partial flag before state */
    if (ok_count == 0) pull_state = PULL_ERROR;
    else pull_state = PULL_DONE;
    return NULL;
}
'''
s = s[:old_start] + new_thread + s[old_end:]

old = '''static void PullTLEData(AppConfig *cfg)\n{\n    if (pull_state == PULL_BUSY) return;\n    pull_state = PULL_BUSY;\n    pull_partial = false;\n    pull_cfg = cfg;\n'''
new = '''static void PullTLEData(AppConfig *cfg)\n{\n    if (pull_state == PULL_BUSY) return;\n    pull_error_detail[0] = '\\0';\n    pull_state = PULL_BUSY;\n    pull_partial = false;\n    pull_cfg = cfg;\n'''
if old not in s:
    raise SystemExit('PullTLEData reset marker not found')
s = s.replace(old, new, 1)

old = '''        &edit_doppler_freq, &edit_doppler_res, &edit_doppler_file,\n        &edit_sat_search, &edit_min_el,\n'''
new = '''        &edit_doppler_freq, &edit_doppler_res, &edit_doppler_file,\n        &edit_sat_search, &edit_tle_proxy, &edit_min_el,\n'''
if old not in s:
    raise SystemExit('UI edit flags marker not found')
s = s.replace(old, new, 1)

old = '''                if (GuiButton((Rectangle){tm_x + tmMgrWindow.width - 110 * cfg->ui_scale, tm_y + 30 * cfg->ui_scale, 100 * cfg->ui_scale, 26 * cfg->ui_scale}, btn_label))\n                {\n                    PullTLEData(cfg);\n                }\n                if (pull_state == PULL_BUSY) GuiEnable();\n            }\n\n            float total_height = 28 * cfg->ui_scale + (retlector_expanded ? NUM_RETLECTOR_SOURCES * 25 * cfg->ui_scale : 0);\n'''
new = '''                if (GuiButton((Rectangle){tm_x + tmMgrWindow.width - 110 * cfg->ui_scale, tm_y + 30 * cfg->ui_scale, 100 * cfg->ui_scale, 26 * cfg->ui_scale}, btn_label))\n                {\n                    SaveAppConfig("settings.json", cfg);\n                    PullTLEData(cfg);\n                }\n                if (pull_state == PULL_BUSY) GuiEnable();\n            }\n\n            GuiLabel((Rectangle){tm_x + 10 * cfg->ui_scale, tm_y + 65 * cfg->ui_scale, 50 * cfg->ui_scale, 24 * cfg->ui_scale}, "Proxy:");\n            AdvancedTextBox((Rectangle){tm_x + 62 * cfg->ui_scale, tm_y + 65 * cfg->ui_scale, tmMgrWindow.width - 132 * cfg->ui_scale, 24 * cfg->ui_scale},\n                            cfg->tle_proxy, sizeof(cfg->tle_proxy), &edit_tle_proxy, false);\n            GuiSetTooltip("Optional proxy URL, e.g. http://proxy.example:8080. Leave blank for libcurl defaults/environment.");\n            if (GuiButton((Rectangle){tm_x + tmMgrWindow.width - 62 * cfg->ui_scale, tm_y + 65 * cfg->ui_scale, 52 * cfg->ui_scale, 24 * cfg->ui_scale}, "Save"))\n                SaveAppConfig("settings.json", cfg);\n\n            if (pull_error_detail[0] != '\\0')\n            {\n                char short_error[80];\n                size_t err_len = strlen(pull_error_detail);\n                snprintf(short_error, sizeof(short_error), "%.68s%s", pull_error_detail, err_len > 68 ? "..." : "");\n                DrawUIText(customFont, short_error, tm_x + 10 * cfg->ui_scale, tm_y + 96 * cfg->ui_scale, 12 * cfg->ui_scale, (Color){235, 110, 110, 255});\n                if (GuiButton((Rectangle){tm_x + tmMgrWindow.width - 62 * cfg->ui_scale, tm_y + 92 * cfg->ui_scale, 52 * cfg->ui_scale, 22 * cfg->ui_scale}, "Copy"))\n                    SetClipboardText(pull_error_detail);\n            }\n            else\n            {\n                DrawUIText(customFont, "Proxy blank = libcurl environment/direct connection", tm_x + 10 * cfg->ui_scale, tm_y + 96 * cfg->ui_scale, 12 * cfg->ui_scale, cfg->text_secondary);\n            }\n\n            float total_height = 28 * cfg->ui_scale + (retlector_expanded ? NUM_RETLECTOR_SOURCES * 25 * cfg->ui_scale : 0);\n'''
if old not in s:
    raise SystemExit('TLE manager apply marker not found')
s = s.replace(old, new, 1)

old = '''            GuiScrollPanel((Rectangle){tm_x + 8 * cfg->ui_scale, tm_y + 65 * cfg->ui_scale, tmMgrWindow.width - 16 * cfg->ui_scale, tmMgrWindow.height - 65 * cfg->ui_scale - 8 * cfg->ui_scale}, NULL, contentRec, &tle_mgr_scroll, &viewRec);\n'''
new = '''            GuiScrollPanel((Rectangle){tm_x + 8 * cfg->ui_scale, tm_y + 122 * cfg->ui_scale, tmMgrWindow.width - 16 * cfg->ui_scale, tmMgrWindow.height - 122 * cfg->ui_scale - 8 * cfg->ui_scale}, NULL, contentRec, &tle_mgr_scroll, &viewRec);\n'''
if old not in s:
    raise SystemExit('TLE manager scroll marker not found')
s = s.replace(old, new, 1)

p.write_text(s)

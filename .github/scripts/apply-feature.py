from pathlib import Path


def replace_once(path, old, new):
    p = Path(path)
    text = p.read_text()
    if old not in text:
        raise SystemExit(f"expected block not found in {path}")
    text = text.replace(old, new, 1)
    p.write_text(text)


main_start = """                    if (is_hl && !(is_pov_mode && &satellites[i] == selected_sat))\n                    {\n                        int segments = fmin(4000, fmax(50, (int)(400 * cfg.orbits_to_draw)));\n"""
main_end = """                    float sat_mx, sat_my;\n"""
main_path = Path("src/main.c")
main_text = main_path.read_text()
start = main_text.find(main_start)
if start < 0:
    raise SystemExit("2D selected-only ground-track block not found")
end = main_text.find(main_end, start)
if end < 0:
    raise SystemExit("end of 2D ground-track block not found")

replacement = r'''                    /* Draw ground tracks for all active satellites on the 2D map.\n                     * Keep the selected/hovered satellite brighter, but do not add\n                     * coverage footprints for every active satellite. To protect\n                     * large constellation views, fall back to the focused satellite\n                     * when more than 64 satellites are active. */\n                    bool draw_multi_tracks = (active_render_count <= 64);\n                    bool draw_this_track = draw_multi_tracks || is_hl;\n                    if (draw_this_track && !(is_pov_mode && &satellites[i] == selected_sat))\n                    {\n                        float orbit_span = fmaxf(cfg.orbits_to_draw, 0.25f);\n                        int segments = (int)fminf(1200.0f, fmaxf(120.0f, 200.0f * orbit_span));\n                        Vector2 track_pts[1201];\n                        bool is_sunlit_arr[1201];\n\n                        double period_days = (2.0 * PI / satellites[i].mean_motion) / 86400.0;\n                        double span_days = period_days * orbit_span;\n                        double time_step = span_days / segments;\n                        double start_epoch = current_epoch - (span_days * 0.5);\n                        int now_index = segments / 2;\n\n                        Vector3 base_sun_dir = {0};\n                        if (cfg.highlight_sunlit)\n                            base_sun_dir = Vector3Normalize(calculate_sun_position(current_epoch));\n\n                        for (int j = 0; j <= segments; j++)\n                        {\n                            double t = start_epoch + (j * time_step);\n                            double t_unix = get_unix_from_epoch(t);\n                            Vector3 raw_pos = calculate_position(&satellites[i], t_unix);\n                            get_map_coordinates(raw_pos, epoch_to_gmst(t), cfg.earth_rotation_offset, map_w, map_h, &track_pts[j].x, &track_pts[j].y);\n                            if (cfg.highlight_sunlit)\n                                is_sunlit_arr[j] = !is_sat_eclipsed(raw_pos, base_sun_dir);\n                        }\n\n                        Color base_track_color = is_hl ? cfg.orbit_highlighted : cfg.orbit_normal;\n                        for (int offset_i = -1; offset_i <= 1; offset_i++)\n                        {\n                            float x_off = offset_i * map_w;\n                            for (int j = 1; j <= segments; j++)\n                            {\n                                if (fabs(track_pts[j].x - track_pts[j - 1].x) < map_w * 0.6f)\n                                {\n                                    float time_alpha = (j <= now_index) ? 0.40f : 0.90f;\n                                    Color drawCol = ApplyAlpha(base_track_color, sat_alpha * time_alpha);\n                                    if (cfg.highlight_sunlit)\n                                    {\n                                        Color light_color = is_sunlit_arr[j] ? cfg.sat_highlighted : cfg.orbit_normal;\n                                        drawCol = ApplyAlpha(light_color, sat_alpha * time_alpha);\n                                    }\n                                    DrawLineEx((Vector2){track_pts[j - 1].x + x_off, track_pts[j - 1].y},\n                                               (Vector2){track_pts[j].x + x_off, track_pts[j].y},\n                                               (is_hl ? 2.5f : 1.5f) / Camera2DParams.zoom, drawCol);\n                                }\n                            }\n\n                            /* Keep apsis markers as a focused-satellite detail instead\n                             * of multiplying them across the whole mission overview. */\n                            if (is_hl)\n                            {\n                                Vector2 peri2d, apo2d;\n                                get_apsis_2d(&satellites[i], current_epoch, false, gmst_deg, cfg.earth_rotation_offset, map_w, map_h, &peri2d);\n                                get_apsis_2d(&satellites[i], current_epoch, true, gmst_deg, cfg.earth_rotation_offset, map_w, map_h, &apo2d);\n                                DrawTexturePro(\n                                    periMark, (Rectangle){0, 0, periMark.width, periMark.height}, (Rectangle){peri2d.x + x_off, peri2d.y, mark_size_2d, mark_size_2d},\n                                    (Vector2){mark_size_2d / 2.f, mark_size_2d / 2.f}, 0.0f, ApplyAlpha(cfg.periapsis, sat_alpha)\n                                );\n                                DrawTexturePro(\n                                    apoMark, (Rectangle){0, 0, apoMark.width, apoMark.height}, (Rectangle){apo2d.x + x_off, apo2d.y, mark_size_2d, mark_size_2d},\n                                    (Vector2){mark_size_2d / 2.f, mark_size_2d / 2.f}, 0.0f, ApplyAlpha(cfg.apoapsis, sat_alpha)\n                                );\n                            }\n                        }\n                    }\n\n'''.replace('\\n', '\n')
main_text = main_text[:start] + replacement + main_text[end:]
main_path.write_text(main_text)

replace_once(
    "Makefile",
    """# macOS (Apple Silicon / Intel)\nCC_MACOS = clang\n""",
    """# macOS (Apple Silicon / Intel)\nCC_MACOS = clang\nMACOS_DEPLOYMENT_TARGET ?= 11.0\n""",
)
replace_once(
    "Makefile",
    """bin/TLEscope-macos: $(SRC) | bin\n\t@if ! $(MACOS_PKG_CONFIG_ENV) pkg-config --exists raylib 2>/dev/null; then echo \"Error: raylib not found. Install with: brew install raylib\"; exit 1; fi\n\t$(CC_MACOS) $(CFLAGS) $(RAYLIB_CFLAGS) -o $@ $^ $(LDFLAGS_MACOS)\n""",
    """bin/TLEscope-macos: $(SRC) | bin\n\t@if [ -z \"$(RAYLIB_LIBS)\" ] && ! $(MACOS_PKG_CONFIG_ENV) pkg-config --exists raylib 2>/dev/null; then echo \"Error: raylib not found. Install with: brew install raylib\"; exit 1; fi\n\tMACOSX_DEPLOYMENT_TARGET=$(MACOS_DEPLOYMENT_TARGET) $(CC_MACOS) $(CFLAGS) -mmacosx-version-min=$(MACOS_DEPLOYMENT_TARGET) $(RAYLIB_CFLAGS) -o $@ $^ $(LDFLAGS_MACOS)\n""",
)

workflow = Path(".github/workflows/build.yml")
w = workflow.read_text()
w = w.replace("runs-on: macos-latest\n", "runs-on: macos-15-intel\n", 1)
old_steps = '''      - name: Install macOS Build Dependencies\n        run: |\n          brew install raylib pkg-config\n\n      - name: Compile and Bundle .app\n        # bundler compiles the icon + ad-hoc signs natively on the runner\n        run: make app\n'''
new_steps = '''      - name: Build static Raylib for a self-contained Intel app\n        env:\n          RAYLIB_VERSION: "5.5"\n          MACOSX_DEPLOYMENT_TARGET: "11.0"\n        run: |\n          curl -fsSL "https://github.com/raysan5/raylib/archive/refs/tags/${RAYLIB_VERSION}.tar.gz" -o raylib.tar.gz\n          tar -xzf raylib.tar.gz\n          make -C "raylib-${RAYLIB_VERSION}/src" \\\n            PLATFORM=PLATFORM_DESKTOP \\\n            RAYLIB_LIBTYPE=STATIC \\\n            CUSTOM_CFLAGS="-mmacosx-version-min=${MACOSX_DEPLOYMENT_TARGET} -DGL_SILENCE_DEPRECATION"\n          mkdir -p .deps/raylib/include .deps/raylib/lib\n          cp "raylib-${RAYLIB_VERSION}/src/raylib.h" \\\n             "raylib-${RAYLIB_VERSION}/src/raymath.h" \\\n             "raylib-${RAYLIB_VERSION}/src/rlgl.h" \\\n             .deps/raylib/include/\n          cp "raylib-${RAYLIB_VERSION}/src/libraylib.a" .deps/raylib/lib/\n\n      - name: Compile and Bundle Intel .app\n        env:\n          MACOSX_DEPLOYMENT_TARGET: "11.0"\n        run: |\n          make app \\\n            RAYLIB_CFLAGS="-I$PWD/.deps/raylib/include" \\\n            RAYLIB_LIBS="$PWD/.deps/raylib/lib/libraylib.a" \\\n            MACOS_DEPLOYMENT_TARGET="$MACOSX_DEPLOYMENT_TARGET"\n          file dist/TLEscope.app/Contents/MacOS/TLEscope | grep -q 'x86_64'\n          if otool -L dist/TLEscope.app/Contents/MacOS/TLEscope | grep -E '/(opt/homebrew|usr/local)/'; then\n            echo "Found a non-system runtime dependency in the app bundle"\n            exit 1\n          fi\n          codesign --verify --deep --strict dist/TLEscope.app\n'''
if old_steps not in w:
    raise SystemExit("macOS workflow block not found")
w = w.replace(old_steps, new_steps, 1)
workflow.write_text(w)

readme = Path("README.md")
r = readme.read_text()
old_download = '''### **Download from GitHub**\nTo download TLEscope, grab a portable zip from the [Relases tab](https://github.com/aweeri/TLEscope/releases), then extract it's contents into a directory of choice.\n'''
new_download = '''### **Download from GitHub**\nTo download TLEscope, grab a portable zip from the [Relases tab](https://github.com/aweeri/TLEscope/releases), then extract it's contents into a directory of choice.\n\nThe GitHub Actions macOS build produces a normal `TLEscope.app` inside `TLEscope-macOS.zip`. It is built for Intel (`x86_64`) with a macOS 11 deployment target and a statically linked Raylib, so users do not need Homebrew or a local compiler. Pull requests also produce the downloadable macOS artifact under the workflow run's **Artifacts** section.\n'''
if old_download not in r:
    raise SystemExit("README download section not found")
r = r.replace(old_download, new_download, 1)
readme.write_text(r)

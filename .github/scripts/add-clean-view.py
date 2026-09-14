from pathlib import Path

p = Path('src/ui.c')
s = p.read_text()

state_old = '''static bool show_tle_warning = false;\nstatic bool show_exit_dialog = false;\n'''
state_new = '''static bool show_tle_warning = false;\nstatic bool show_exit_dialog = false;\nstatic bool ui_hidden = false;\n'''
if state_old not in s:
    raise SystemExit('UI state marker not found')
s = s.replace(state_old, state_new, 1)

mouse_old = '''bool IsMouseOverUI(AppConfig *cfg)\n{\n    if (show_exit_dialog || cfg->show_first_run_dialog)\n        return true;\n'''
mouse_new = '''bool IsMouseOverUI(AppConfig *cfg)\n{\n    if (ui_hidden && !show_exit_dialog && !cfg->show_first_run_dialog)\n        return false;\n    if (show_exit_dialog || cfg->show_first_run_dialog)\n        return true;\n'''
if mouse_old not in s:
    raise SystemExit('IsMouseOverUI marker not found')
s = s.replace(mouse_old, mouse_new, 1)

start_old = '''void DrawGUI(UIContext *ctx, AppConfig *cfg, Font customFont)\n{\n    FinishPullIfDone(ctx, cfg);\n\n    *ctx->show_scope = show_scope_dialog;\n    *ctx->scope_az = scope_az;\n    *ctx->scope_el = scope_el;\n    *ctx->scope_beam = scope_beam;\n'''
start_new = '''void DrawGUI(UIContext *ctx, AppConfig *cfg, Font customFont)\n{\n    FinishPullIfDone(ctx, cfg);\n\n    // H toggles a clean map view.  Map content (satellites, labels and ground\n    // tracks) is rendered outside DrawGUI, so hiding the UI leaves those\n    // mission overlays visible while suppressing toolbar/status/dialog chrome.\n    if (!IsUITyping() && IsKeyPressed(KEY_H))\n        ui_hidden = !ui_hidden;\n\n    *ctx->show_scope = ui_hidden ? false : show_scope_dialog;\n    *ctx->scope_az = scope_az;\n    *ctx->scope_el = scope_el;\n    *ctx->scope_beam = scope_beam;\n\n    // Keep first-run and exit confirmation dialogs reachable even in clean view.\n    if (ui_hidden && !show_exit_dialog && !cfg->show_first_run_dialog)\n        return;\n'''
if start_old not in s:
    raise SystemExit('DrawGUI marker not found')
s = s.replace(start_old, start_new, 1)

p.write_text(s)

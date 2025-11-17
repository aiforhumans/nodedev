# 🤖Xtremetools Mirroring Strategy

Use a symbolic link so that edits in this workspace immediately reflect inside the ComfyUI portable installation.

## Prerequisites
- Run Command Prompt or PowerShell **as Administrator** (required for `mklink`).
- Ensure `C:\ComfyUI_windows_portable\ComfyUI\custom_nodes` exists.

## Steps
1. Delete any existing `🤖Xtremetools` folder inside the ComfyUI `custom_nodes` directory (back it up first if needed).
2. From an elevated terminal, run:
   ```cmd
   mklink /D "C:\ComfyUI_windows_portable\ComfyUI\custom_nodes\🤖Xtremetools" "C:\nodedev\🤖Xtremetools"
   ```
3. Confirm the link by listing the target directory and ensuring files appear immediately after edits in this workspace.

## Maintenance
- Keep this workspace as the source of truth; the symlink ensures ComfyUI reads files directly.
- If the portable installation is moved, delete the old link (`rmdir` on the link path) and recreate it pointing to the new location.

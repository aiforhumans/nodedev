## Plan: Scaffold ComfyUI Node Workspace

Create the required folder layout, note mirroring needs, and prep for future custom-node development so assets stay synchronized with the ComfyUI portable install.

### Steps
1. Verify workspace root `c:\nodedev` is clean and confirm no conflicting directories exist.
2. Create top-level folders `Docs`, `.github`, `.venv`, `tests`, `Xtremetools` in `c:\nodedev`.
3. Document mirror requirement: plan how `Xtremetools` will sync to `C:\ComfyUI_windows_portable\ComfyUI\custom_nodes\Xtremetools` (e.g., script or symlink).
4. Add placeholder README or index files inside each folder to capture intended usage and keep version control friendly.
5. gather information about node development best practices for ComfyUI to inform future work from [text](https://docs.comfy.org/custom-nodes/walkthrough)
6. Set up a basic virtual environment in `.venv` for Python dependencies related to node development.
7. Create a simple test script in `tests` to validate the environment setup.
8. Review the folder structure and ensure everything is in place for future development.
9. Mirror strategy symlink: Use a symbolic link to connect `Xtremetools` in the workspace to the ComfyUI custom nodes directory. This allows for real-time synchronization of changes made in the workspace with the ComfyUI installation.
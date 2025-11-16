# ComfyUI Custom Node Best Practices

_Source: https://docs.comfy.org/custom-nodes/walkthrough (retrieved Nov 16 2025)_

- **Project scaffolding:** Use `comfy node scaffold` from within `ComfyUI/custom_nodes` to generate a cookiecutter-based project with proper metadata, licensing, and optional client assets.
- **Node definition contract:** Each node class must define `CATEGORY`, `INPUT_TYPES`, `RETURN_TYPES`, and `FUNCTION`; inputs and outputs follow ComfyUI’s standardized type names (e.g., `IMAGE` indicates an image batch tensor).
- **Typed tensors:** Image tensors are stored as `torch.Tensor` in `[B,H,W,C]` format; use tensor utilities (`flatten`, `mean`, `unsqueeze`) to manipulate batches safely and always return tuples to match declared outputs.
- **Registration:** Update `NODE_CLASS_MAPPINGS` (and optionally `NODE_DISPLAY_NAME_MAPPINGS`) in `__init__.py` so ComfyUI can discover the class; restart the server after edits.
- **Configurable UI:** Extend `INPUT_TYPES` to expose widgets (lists, sliders, etc.) for user-selectable parameters, and reflect those parameters inside the node’s main function.
- **Frontend feedback:** Import `PromptServer` and use `send_sync` to push status messages; pair with a small JS extension under `web/js` and export `WEB_DIRECTORY` to hook client-side behavior.
- **Licensing & metadata:** Choose an appropriate open-source license during scaffolding and keep `version`, `project_short_description`, and author fields accurate for distribution.

# LM Studio Integration Notes

## Requirements
- Install [LM Studio](https://lmstudio.ai/) locally and launch the server interface.
- Load at least one chat-capable model; the default ComfyUI nodes assume the server listens on `http://localhost:1234`.
- For remote hosts or different ports, supply the custom URL via the `server_url` input on the node.

## Provided Nodes
- `XtremetoolsLMStudioText` (category `Xtremetools/LM Studio`)
  - Inputs: prompt, optional user/system prompts, server URL, model name, temperature, and max tokens.
  - Outputs: generated text plus an info string summarizing model, finish reason, token usage, and latency.

## Base Helper
- `base/lm_studio.py` exposes `LMStudioBaseNode`, which wraps the `/v1/chat/completions` endpoint via `urllib.request`.
- Shared behaviors: message construction, JSON + error handling, latency tracking, and info string formatting.
- Extend this base class for additional nodes (batching, streaming, ControlNet-aware prompt builders, etc.).

## Troubleshooting
- `LMStudioAPIError` surfaces connectivity issues, missing models, and invalid responses; ComfyUI will surface the exception.
- **HTTP 400** usually means LM Studio has no model loaded. Open LM Studio, load a chat model, or set the `model` input on the node to match the identifier listed under `/v1/models`.
- Ensure LM Studio is running before executing the workflow; restarting ComfyUI may be necessary after adding new nodes.
- Use the included pytest suite (`python -m pytest`) to validate alias wiring and HTTP mocks without needing a live LM Studio server.

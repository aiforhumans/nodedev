# Plan: GitHub MCP Testing Integration

## Success Criteria (Guardrails)
- ≥90% of `NODE_CLASS_MAPPINGS` covered by MCP harness smoke calls.
- MCP-focused `pytest -m mcp` completes in ≤60 s locally; CI runs it nightly and can toggle via marker.
- Schema snapshots alert on drift for every node (`INPUT_TYPES`, `RETURN_TYPES`, `RETURN_NAMES`, `FUNCTION`, `CATEGORY`).

## Workstream Overview
1. Catalog GitHub MCP capabilities + stubbing requirements.
2. Build reusable MCP harness (adapter + fake client) with shared fixtures.
3. Capture deterministic node schema snapshots and update tooling.
4. Run end-to-end workflow scenarios through MCP adapters.
5. Wire automation hooks and contributor docs so the flow is sustainable.

## Workstream Details

### 1. Catalog MCP Capabilities
- Draft `docs/mcp-tooling.md` describing github-mcp-server tool families we care about (contexts, repos, discussions, workflows) and how nodes map to them.
- For each MCP call, decide whether existing fake HTTP/GraphQL layers can satisfy it; record any missing stubs so future tests stay offline.
- Maintain a gating checklist (auth needed? state mutation? high rate limits?) to pre-classify tools as stubbed, skipped, or read-only.

### 2. Prototype MCP Harness
- Under `tests/mcp/`, add `harness.py` housing:
  - `MCPToolAdapter`: exposes a node as a MCP-style tool schema + callable handler, mirroring github-mcp-server `toolsnaps` ergonomics.
  - `FakeMCPClient`: receives dict-based `CallToolRequest` payloads, invokes adapters, and logs transcripts/assertions.
- Provide fixtures that spin up adapters for the canonical chain (WorkflowRequest → Generator → Validator → Exporter → PostProcessor) so tests can compose flows quickly.

### 3. Snapshot Node Schemas
- Persist snapshots in `tests/snapshots/node_contracts/*.json` (one file per node, sorted keys for diffability).
- `tests/mcp/test_node_contracts.py` iterates `NODE_CLASS_MAPPINGS`, builds schema dicts, and compares against stored snapshots.
- Expose a `--update-node-snapshots` pytest flag hooked into `tests/snapshot_utils.py` helpers; write structure + default values only to limit churn.

### 4. End-to-End Workflow Runs
- `tests/mcp/test_workflow_e2e.py` should traverse WorkflowRequest + LM Studio settings/helpers + WorkflowGenerator + Validator + Exporter + `post_process_workflow`.
- Assertions: ASCII-only telemetry (`info.encode('ascii')`), unique node/link IDs, tuple-compliant outputs, and deterministic fake LM Studio / GitHub responses reused from fixtures.
- Capture transcripts from `FakeMCPClient` so failures highlight which tool interaction diverged.

### 5. Automation Hooks & Docs
- Add `[pytest] markers = mcp: ...` to `pytest.ini`; document CI usage (nightly required, PR optional via `PYTEST_ADDOPTS="-m mcp"`).
- Update `Docs/LM_STUDIO.md` + `Docs/BEST_PRACTICES.md` + release checklist with: how to run MCP tests, regenerate snapshots, and troubleshoot harness failures.
- Optional helper: `scripts/update_mcp_snapshots.py` calling `pytest --update-node-snapshots -m mcp --maxfail=1` for contributors needing one-step refresh.

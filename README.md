# latent-superpowers

Shared agent skills with a portable core and generated adapters for multiple coding assistants.

## Layout

- `core/`: agent-agnostic skill logic, references, and manifests
- `adapters/`: generated wrappers for Codex, Claude Code, Gemini, and OpenCode
- `tools/`: generators and installation helpers

## Current Status

- `hydra` has been ported into the shared-core layout
- the live Codex Hydra skill is installed from the generated Codex adapter

## Typical Workflow

1. Edit a shared skill under `core/<skill>/`
2. Regenerate wrappers with `python3 tools/generate_adapters.py --skill <skill>`
3. Install the Codex adapter with `python3 tools/install_adapter.py --skill <skill> --adapter codex --mode symlink`

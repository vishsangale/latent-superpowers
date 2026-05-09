# latent-superpowers

Shared agent skills with a portable core and generated adapters for multiple coding assistants.

## Layout

- `core/`: agent-agnostic skill logic, references, and manifests
- `adapters/`: generated wrappers for Codex, Claude Code, Gemini, and OpenCode
- `tools/`: generators and installation helpers

## Skills

- `hydra`
- `wandb`
- `mlflow`
- `ablation-analysis`
- `profiling-optimization`
- `local-dashboard`
- `paper-to-code`
- `experiment-runner`
- `eval-benchmark`
- `dataset-pipeline`
- `reproducibility`
- `slurm-cluster`
- `arxiver-bringup`
- `arxiver-verify-hypothesis`
- `arxiver-add-adapter`

## Typical Workflow

1. Edit a shared skill under `core/<skill>/`
2. Regenerate wrappers with `python3 tools/generate_adapters.py --skill <skill>`
3. Install the Codex adapter with `python3 tools/install_adapter.py --skill <skill> --adapter codex --mode symlink`

## Development

Install dev dependencies:

```bash
python3 -m pip install -r requirements-dev.txt
```

Validate the whole repo:

```bash
python3 tools/validate_repo.py
```

Install all live Codex adapters at once:

```bash
python3 tools/install_codex_adapters.py --mode symlink --force
```

GitHub Actions runs the same repo validator on pushes and pull requests via [`/.github/workflows/validate.yml`](.github/workflows/validate.yml).

# Reproducibility Defaults

Every single result must be reproducible without the user relying on memory.

## Logging Requirements
Your training scaffold or configuration must log:
- **Random Seeds:** Torch, numpy, random, etc.
- **Hyperparameters:** Batch size, learning rate, and any ad-hoc constant used.
- **Hardware/Env Specs:** Consider checking dependency versions (e.g. `pip freeze`) and logging them into MLflow/W&B.

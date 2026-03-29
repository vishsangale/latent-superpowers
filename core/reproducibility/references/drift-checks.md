# Drift Checks

The default drift checks are local and practical:

- git commit SHA
- current branch
- dirty worktree status
- Python executable and version
- selected environment variables

Interpretation:

- Dirty repo mismatch: code changed relative to the saved snapshot, even if the commit SHA is the same.
- Python mismatch: environment changed enough that behavior may differ.
- Env mismatch: the run may be targeting a different backend, dataset root, or credential scope.
- Git unavailable: reproducibility is blocked because code state cannot be verified from version control metadata.

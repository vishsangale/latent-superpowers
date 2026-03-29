# Workflow

- Start with `inspect_slurm_project.py` to see what the repo already exposes for cluster execution.
- Use `generate_sbatch.py` for one command at a time when you want a clear dry-run artifact before submission.
- Use `plan_job_array.py` once a local manifest already exists; do not rebuild the sweep by hand.
- Use `summarize_slurm_log.py` and `parse_sacct.py` after jobs run so failures are categorized instead of guessed from raw scheduler text.

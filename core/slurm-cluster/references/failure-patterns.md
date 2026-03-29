# Failure Patterns

The log summarizer classifies common Slurm failures into a few practical buckets:

- `oom`: out-of-memory or cgroup kill messages
- `timeout`: time limit exceeded
- `module`: missing module or command-not-found style failures
- `python-traceback`: Python traceback detected
- `node-failure`: node failure or launch failure messages
- `unknown`: no known signature matched

# Workflow

1. Point the dashboard at local MLflow and W&B sources.
2. Build a normalized run index first.
3. Surface source health, warnings, and run counts before trusting any comparison.
4. Serve simple JSON APIs plus one static HTML view with refresh, filtering, and shortlist review.
5. Prefer grouped comparisons with an explicit metric and direction over raw run dumps when answering research questions.
6. Use tradeoff and project-rollup views to understand the current filtered slice before drilling into individual runs.
7. Keep artifact browsing local and read-only, but support preview and download for common local files.

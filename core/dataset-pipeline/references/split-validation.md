# Split Validation

Split validation tries ID-based overlap first and falls back to row hashing.

ID heuristics:
- `id`
- `user_id`
- `item_id`
- `session_id`
- `interaction_id`

Rules:
- If a shared ID key exists across splits, compare those IDs directly.
- If no shared ID key exists, compare normalized row hashes.
- Treat any non-zero overlap as leakage unless the user has explicitly described a reason it is acceptable.

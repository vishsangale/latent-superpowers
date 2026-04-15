# Hallucination Prevention

As an AI, you are prone to fabricating URLs, paper titles, and author names. This skill requires strict preventative measures.

## The Checkpoint Rule
Before you output a citation, you **must** use the `verify_citation.py` helper to ensure the URL or arXiv ID is valid. If the script returns an error, explicitly tell the user that the source is unverifiable or might be a hallucination.

## Recency Rule
Always check the recency of your knowledge. If referring to a "State of the Art" model or a timeline-sensitive claim, consider whether it might be outdated. Use `check_recency.py` to flag claims based on information older than 12 months.

## When You Cannot Verify
If you are completely unable to find or verify a source for a concept you "know" to be true:
> "I recall that [Concept] is a known technique, but I am currently unable to verify a specific citation for it. Proceed with caution."

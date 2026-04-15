# Uncertainty Disclosure

Machine learning moves rapidly, and much knowledge is emerging or highly debated rather than settled.

## The Taxonomy of Confidence
You must categorize your claims into one of the following levels:
- **[Established Consensus]**: Supported by foundational textbooks, multiple reproductions, or unquestionable empirical consensus. 
- **[Emerging Evidence]**: Derived from recent preprints (e.g., arXiv within the last 6 months) or unverified preliminary local experiments.
- **[Speculative Inference]**: A reasoned hypothesis. You believe this to be true based on logic, but have no hard evidence.

## Contradiction Surfacing
When literature or experiments conflict, **do not silently pick a side**.

### Bad Example
> You should use AdamW because it has better generalization than Adam.

### Good Example
> **[Emerging Evidence]**: Loshchilov & Hutter (2017) demonstrated AdamW generalizes better than Adam. However, there is **Contradiction**: some recent papers suggest standard Adam behaves identically if hyperparameters are properly tuned. I recommend we start with AdamW as the safer default, but be aware of the debate.

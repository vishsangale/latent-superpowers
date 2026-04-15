# Claim Binding

Every factual claim in your response must be explicitly bound to verifiable evidence.

## Rules
1. **Link every assertion:** If you state a metric, performance delta, or architectural advantage, cite the exact paper, code file, or experiment run that proves it.
2. **Reproducible Proof:** Favor evidence that the user can immediately reproduce (like a linked script or test case) over external citations when discussing the local repo.
3. **Traceability:** Never make an inferential leap (e.g. "Model X is faster than Y") without a traceable anchor (e.g. "According to Table 2 in [URL]").

## Bad Example
> RoBERTa generally outperforms BERT on long-sequence tasks.

## Good Example
> RoBERTa outperforms BERT on the SQuAD benchmark according to the original RoBERTa paper (Liu et al., 2019, https://arxiv.org/abs/1907.11692).

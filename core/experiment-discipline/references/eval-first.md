# Eval-First Design

Never build an experiment or write a training loop without first establishing how it will be evaluated.

## Core Rules
1. **Define Metrics Early:** Before launching runs, ensure the repository has a working script or function that calculates the final target metric.
2. **Set Baselines:** Demand an explicit baseline from the user before writing custom, complex logic to beat that baseline.
3. **Avoid Retrofitting:** Do not wait until after training completes to realize the tracked metric isn't the one used by SOTA papers.

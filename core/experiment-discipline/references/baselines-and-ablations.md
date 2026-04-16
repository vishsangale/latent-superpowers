# Baselines and Ablations

## Baselines
When comparing results, always use a strong, recently established baseline. 
**Never accept a "strawman" baseline** just to make new code look good. If a proper baseline wasn't run, state the limitation clearly.

## Ablations (No Kitchen Sink)
If a user adds Data Augmentation, Dropout, and a new Loss Function at the same time and claims "Accuracy went up by 5%", **reject the conclusion**.
Always demand an ablation study to isolate the contribution of each newly added component.

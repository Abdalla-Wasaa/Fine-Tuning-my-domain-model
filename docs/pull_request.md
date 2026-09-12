## Problem and behavior

Add an independent AfyaPlus Week 4 fine-tuning capstone covering operational workflows. The pipeline validates 200 synthetic SOP-grounded examples into group-disjoint 160/20/20 splits, trains completion-only QLoRA, merges the exact base revision, filters local responses, and evaluates 20 paired outputs with an independent judge.

Relates to #1, #2, #3, #4, #5. The issues exist; these references do not imply closure.

## Validation

Offline tests cover data errors and leakage, safety routing, mandatory disclaimer, completion masking, judge result validation, metric handling, loss diagnosis, and evidence checks. Vast.ai is the selected training provider; provider-specific stop wrappers share failure-path tests. Python compilation and shell syntax checks pass. See reports/local_checks.txt for the recorded run.

## Outstanding evidence

Keep this PR draft until a Vast.ai CUDA run, actual adapter/merged weights, five model samples, complete evaluation, billing and explicit provider STOPPED verification are attached. Pending CSV cells are intentionally blank. The SOP is synthetic teaching material requiring facility-owner review.

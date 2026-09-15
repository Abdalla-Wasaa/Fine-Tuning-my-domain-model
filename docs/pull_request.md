## Problem and result

Complete the independent AfyaPlus Week 4 capstone using the required LLaMA 3.1 8B model and 200 reviewed, source-derived Kenyan operational examples. Wasaa Abdalla approved all 100 underlying cases; deterministic 160/20/20 splits have zero validation errors and no scenario overlap. The verbally approved Vast.ai provider substitution is documented as student-reported approval.

Actual QLoRA training completed three epochs and 30 optimizer steps. BF16 merging and five safety-filtered samples completed. The 20-question comparison uses identical NF4/BF16 inference for base and tuned models and an independent OpenRouter GPT-4o-mini judge. ROUGE-L improves from 0.3257 to 1.0000, but judge quality declines from 4.55 to 3.85 and groundedness from 0.980 to 0.775. The report preserves these results, flags inconsistent judge rationales, and recommends holding deployment.

## Evidence and validation

Trainer state, loss curve, token/data hashes, sample responses, per-question analysis, comparison CSV, and stakeholder memo are included. Checksummed adapter and merged model assets are stored in release v0.2.0-capstone, with upstream license notices. Provider API confirms stopped. Itemized instance charges are USD 2.884 at the recorded snapshot; judge receipts total USD 0.00203655. Retained storage can continue accruing charges.

39 offline tests pass; data validation and shell syntax checks pass. Full submission verification checks published artifact digests, recorded reviewer approval, actual run evidence, evaluation, and provider state. Historical Qwen results remain clearly separated under experiments/qwen-teaching-v1.

Closes #1, closes #2, closes #3, closes #4, closes #5.

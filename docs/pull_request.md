## Problem and behavior

Align the AfyaPlus capstone with the required LLaMA 3.1 8B model and authoritative Kenyan sources. Replace the synthetic teaching corpus with 200 source-derived examples and scenario-disjoint 160/20/20 splits. Wasaa Abdalla explicitly confirmed review and approval of all 100 underlying cases; the dated, hash-bound ledger records that approval.

Implement citation validation, training provenance and exact-token checks, merge resource checks, safety-filtered inference, and paired evaluation scripts. Record the student-reported verbal instructor approval for Vast.ai. Preserve earlier Qwen results under experiments/qwen-teaching-v1 rather than presenting them as results for the replacement model or corpus.

Relates to #1, #2, #3, #4, #5.

## Validation

Dataset validation: 200 examples, zero errors, no scenario overlap, 100 verified clause/page anchors. All 36 offline tests pass. Training shell scripts pass syntax checks. Hugging Face access to the pinned LLaMA configuration was verified (HTTP 200).

## Remaining work

Keep this PR draft. Required LLaMA training, merged weights, sample outputs, paired evaluation, final measured stakeholder memo, and billed-cost/stop evidence are not complete. The current Vast instance has insufficient free storage margin and the local workstation lacks RAM for the configured float32 merge. CSV rows explicitly remain pending. Do not use historical Qwen metrics as replacement-run evidence.

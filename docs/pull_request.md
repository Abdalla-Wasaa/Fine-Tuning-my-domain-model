## Problem and behavior

Implement the independent AfyaPlus Week 4 capstone with 200 synthetic operational examples, scenario-disjoint 160/20/20 splits, completion-only QLoRA, exact-base merging, conservative inference safety, and a 20-question paired benchmark.

Actual Vast.ai RTX 3090 training completed 30 steps in 95.04 seconds. CPU merging and 40 comparison generations completed on the instance; five pipeline samples and all 20 OpenRouter judge results are saved. Judge quality increased from 2.15 to 5.00/5 and raw ROUGE-L from 0.1465 to 1.0000. Both models received reference SOP context; this measures instruction following on ten synthetic scenarios, not clinical validation.

Relates to #1, #2, #3, #4, #5.

## Validation

30 offline tests pass. The complete merged model was recovered through resumable SSH transfer and SHA256-verified; all five offline local samples exactly match the remote outputs. The provider stop CLI completed successfully and subsequent SSH connections were refused; this is not an explicit provider STOPPED response. Real trainer state, loss curve, dataset hashes, merge provenance, per-question results and judge receipts accompany the report. Training-only GPU cost is estimated at USD 0.0049; the total bill is not verified.

## Remaining work

Keep draft while final billed cost and explicit provider-stop evidence remain outstanding. The teaching SOP needs facility-owner approval before use. Model weights are excluded from Git.

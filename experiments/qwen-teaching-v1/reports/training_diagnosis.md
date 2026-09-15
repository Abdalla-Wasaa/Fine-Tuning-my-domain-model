# Recorded training diagnosis

The Vast.ai RTX 3090 run completed all 30 optimizer steps in 95.045 seconds using the pinned Qwen2.5-0.5B-Instruct revision and four-bit QLoRA configuration. The remote exit code was zero. The retrieved trainer_state.json records validation loss of 0.000483 at step 10, 0.000275 at step 20, and 0.000251 at step 30.

This is a healthy downward validation-loss trend under the declared heuristic: validation loss did not rebound while training loss declined. It does not prove clinical safety or broad domain generalization. The unusually low losses are consistent with the task design: the supplied SOP excerpt contains the reference workflow, and training teaches the model to reproduce it with the fixed disclaimer. Test prompts must receive the same context when comparing base and tuned models.

The initial evaluation was executed before training, but Trainer reset its in-memory log history when training began; the final trainer_state.json therefore contains epoch-end validation results only. No unrecorded baseline loss is inferred. Quality improvement must come from the separate held-out comparison rather than the loss curve.

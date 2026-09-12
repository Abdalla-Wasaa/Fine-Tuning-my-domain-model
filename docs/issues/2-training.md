Implement and execute pinned QLoRA training on Nebius. Preserve trainer_state.json, immutable base revision, data hashes, adapter weights, loss curve and diagnosis. Upload artifacts durably and verify the instance is STOPPED immediately after the run.

Acceptance: actual CUDA run evidence, billed cost and provider stop verification. CPU integration tests are not capstone training evidence.

# Existing Week 4 artifact audit

Inspected `wk4/afyaplus-finetune/venv` without changing classwork or exposing credentials.

- `afyaplus-llama-adapter/adapter_config.json` identifies `meta-llama/Llama-3.2-1B-Instruct`, not the rubric-required LLaMA 3.1 8B. Adapter weights exist (13,648,488 bytes); the base revision is unspecified.
- Checkpoint 30 records three epochs and 30 steps. Validation loss decreases from 2.31918 to 1.38923 to 1.27904. This supports learning over the recorded checkpoints, but does not establish operational correctness or provenance.
- Root JSONL splits contain 160/20/20 examples, with no exact normalized question overlap between splits. The raw 200 records contain question and answer fields only; source citations and named verification evidence are absent from those records. Near-duplicate leakage was not assessed here.
- The expected `afyaplus-llama-merged` directory is absent from this folder. A merge script alone does not establish a successful merge.
- `local_inference.py` lacks the mandatory output disclaimer and loads model weights at import time despite its import-safe comment. Its short prohibited-word list does not establish clinical safety.
- No top-level `fine_tune.py` or evaluation report was found in this folder.

These are useful historical classwork artifacts. They cannot be presented as training or evaluation evidence for the replacement source-backed dataset or the required 8B model. Retain the capstone's separate scripts and safety controls. A different model requires a documented instructor exception before it can satisfy the explicit model requirement.

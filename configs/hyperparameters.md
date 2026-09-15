# LLaMA 3.1 8B training design

The required model is `meta-llama/Llama-3.1-8B-Instruct`, pinned to revision `0e9e39f249a16976918f6564b8830bc894c89659`. Download access requires the user's approved Hugging Face account. No model licence acceptance is performed by the scripts.

- Four-bit NF4 with double quantization and BF16 compute when available (FP16 otherwise) reduces frozen-weight memory. Target a CUDA GPU with 24 GiB VRAM or more; actual capacity must be checked on the selected host.
- LoRA rank 16, alpha 32 and dropout 0.05 apply to attention and MLP projections. This provides modest adaptation capacity without updating the full model.
- Batch size 1 and accumulation 16 retain an effective batch of 16 while reducing peak activation memory compared with the earlier Qwen experiment.
- Three epochs over 160 examples produce 30 optimizer steps. Learning rate 1e-4, cosine decay, 10% warmup and weight decay 0.01 are starting choices, not tuned outcomes. Validation chooses the best epoch checkpoint.
- Maximum sequence length 1024, completion-only loss, no packing or truncation, and gradient checkpointing bound memory. Exact lengths for all three splits are recorded before training; test data is tokenized for length checking only, never used for optimization or checkpoint selection.
- Seed 42 fixes data splitting and training seeds. Kernels may still cause numerical variation.
- Training logs each optimizer step and evaluates each epoch. The pretraining validation loss is explicitly restored into the saved history so the loss plot includes step zero. The diagnosis heuristic flags a validation rebound with falling training loss as possible overfit and less than 2% validation improvement as possible underfit. These are heuristics, not evidence of clinical safety.

The float32 CPU merge/inference path needs at least 40 GiB available RAM; use a machine with 64 GiB installed and at least 80 GiB free disk for base weights, environment and merged shards. A small-memory workstation cannot run this path. The prior Qwen setup and measured results are archived under `experiments/qwen-teaching-v1/`.

## Lower-memory execution profile

The replacement instance provides 16 GB VRAM and 32 GB system RAM. Training retains the documented batch size of one, gradient accumulation, NF4 and gradient checkpointing. For this instance use `python merge_model.py --precision bfloat16`: it merges into non-quantized BF16 base weights, saves BF16 weights, and records precision in the merge manifest. This reduces weight memory from roughly 32 GB to 16 GB, with a 22 GiB available-RAM preflight. BF16 rounding differs from the default float32 merge; no equivalence of outputs is claimed.

Use `--precision bfloat16 --device auto` for both inference and evaluation on this instance. Automatic placement limits GPU weights to 12 GiB and offloads remaining layers to CPU, reserving GPU space for generation. Both comparison models use identical precision and placement settings, which are included in the generation cache identity. These settings do not quantize the merged model.

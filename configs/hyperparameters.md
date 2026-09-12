# Training design and rationale

- Base: Qwen/Qwen2.5-0.5B-Instruct, an Apache-2.0 instruct model small enough for CPU merging and inference. It is a teaching baseline, not a clinical model. See its [model card](https://huggingface.co/Qwen/Qwen2.5-0.5B-Instruct).
- The configured Hub revision is resolved to an immutable commit before training and saved in run_manifest.json. Merging and baseline inference use that exact revision. For reruns set configs/train.json revision to the recorded SHA.
- QLoRA: NF4 four-bit weights, double quantization, BF16 compute when supported (FP16 otherwise), paged AdamW. This reduces trainable-memory needs while retaining a frozen base. See [PEFT quantization guidance](https://huggingface.co/docs/peft/developer_guides/quantization).
- Rank 16, alpha 32, dropout 0.05, attention and MLP projection targets: modest adapter capacity with regularization on a small dataset.
- Three epochs, learning rate 1e-4, cosine schedule, warmup 10%, weight decay 0.01: conservative initial settings, selected before looking at test results. They are a reasoned starting point, not empirically optimized settings.
- Batch 2 × accumulation 8 = effective batch 16 on one GPU. With 160 training rows, this yields 10 optimizer steps per epoch, 30 total. Log each step; evaluate/save each epoch and select minimum validation loss.
- Context 1024 tokens, no packing or truncation. Full chat tokenization must have the generation prompt as an exact prefix; labels mask system/user tokens with -100. Padding labels are also -100. Only completion tokens contribute to training loss.
- Seed 42, deterministic split, greedy inference. GPU kernels can still introduce small numeric differences. Version pins and artifact hashes support auditing.
- Diagnosis uses recorded loss trends: validation rise >5% with falling training loss flags possible overfit; <2% validation improvement flags possible underfit/optimization problems. These are transparent heuristics, not definitive statistical diagnoses. Always inspect the curve and held-out outputs.

Uses the standard [Transformers 4.51.3 Trainer](https://huggingface.co/docs/transformers/v4.51.3/en/main_classes/trainer), so no TRL version-dependent trainer wrapper is needed.

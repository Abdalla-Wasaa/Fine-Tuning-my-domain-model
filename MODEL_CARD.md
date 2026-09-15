---
base_model: meta-llama/Llama-3.1-8B-Instruct
license: llama3.1
pipeline_tag: text-generation
---
# Llama-3.1-AfyaPlus-Operations

Built with Llama. This is an educational operational-guidance model, derived from the pinned Meta Llama 3.1 8B Instruct revision in configs/train.json. Use remains subject to the upstream Llama 3.1 Community License and Acceptable Use Policy distributed with the release.

Training uses 160 examples, with 20 validation and 20 held-out test examples. Wasaa Abdalla confirmed review of all 100 underlying source-derived cases. No patient records are used. The model is trained to repeat supplied operational guidance and append a disclaimer; this is not a general medical reasoning model or a verified AfyaPlus facility SOP.

The merged weights are BF16. The recorded benchmark loads both base and tuned weights with NF4 double quantization and BF16 compute on a 16 GB GPU. ROUGE-L improves, but the independent judge quality score declines and some judge groundedness rationales contradict exact source matches. See reports/evaluation_report.md for actual results and limitations. Do not deploy without further human evaluation and facility approval.

This model provides non-diagnostic operational guidance only.

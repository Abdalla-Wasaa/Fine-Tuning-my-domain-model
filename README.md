# AfyaPlus: fine-tune a domain operations model

Independent Week 4 capstone for appointment workflows, triage escalation routing, registration, and system access. The project lives in `wk4_capstone_project/` locally and occupies the root of the dedicated target repository. No classwork files are modified or imported at runtime.

**Current state:** real QLoRA training completed on a Vast.ai RTX 3090 (30 steps, 95.04 seconds). The adapter was merged on the instance; five inference samples and 20 paired OpenRouter-judged evaluations are saved. Raw ROUGE-L increased from 0.1465 to 1.0000 and judge quality from 2.15 to 5.00/5 on this synthetic, SOP-supplied benchmark. The trained adapter is retrieved and SHA256-verified. Local merged-weight verification, final billing and provider-stop confirmation remain outstanding. See [status](reports/status.json), [training diagnosis](reports/training_diagnosis.md), [evaluation](reports/evaluation_report.md), and [memo](memo.md).

> This model provides non-diagnostic operational guidance only.

## Architecture

Curated JSONL → source validation → grouped 160/20/20 split → completion-only QLoRA → adapter and run provenance → exact-base CPU merge → local inference with SOP retrieval and conservative safety gate → paired base/tuned evaluation with an independent judge → report and memo.

The supplied SOP is synthetic teaching material, not an approved AfyaPlus policy. Each of 100 scenarios has two paraphrases kept in the same split. Evaluation provides the relevant SOP directly to both models: it measures contextual instruction following, not retrieval accuracy. The 20 test questions are only ten independent scenarios. See [curation note](data_curation_note.md).

## Project structure

```text
curated_dataset.jsonl        Source dataset placed in project root
policies.json               Versioned synthetic teaching SOP and source IDs
data_prep.py                Format, validate and split data
data/{train,val,test}.jsonl  160 / 20 / 20 formatted chat examples
configs/train.json          Training hyperparameters
configs/hyperparameters.md  Model choice and rationale
fine_tune.py                Single-GPU Nebius/Vast QLoRA training
training_utils.py           Completion token masking and loss diagnosis
merge_model.py              Merge exact base revision in CPU float32
local_inference.py          Local generation, retrieval and five sample queries
safety.py                   Input routing and fail-closed output gate
evaluate_models.py          Paired 20-question benchmark and LLM judging
report_results.py           Comparison analysis and measured stakeholder memo
comparison_results.csv      Completed metrics on 20 paired questions
reports/                    Validation, execution evidence and analysis
scripts/train_nebius.sh     Time limit, durable upload and provider stop
scripts/record_cost.py      Actual billed compute cost calculation
scripts/verify_submission.py Evidence completeness gate
tests/                      Offline correctness and safety checks
artifacts/                  Ignored adapter and merged weight storage
```

## Reproduction

### 1. Environment setup

Use Python 3.11 or 3.12. Training needs a CUDA-capable Nebius or Vast.ai GPU with compatible NVIDIA drivers; local merging and inference use CPU. Reserve approximately 8 GB available RAM and 8 GB disk for the 0.5B model, adapter, checkpoints, and merged weights; actual usage varies. Verify capacity before reserving a paid instance.

```bash
git clone https://github.com/Abdalla-Wasaa/Fine-Tuning-my-domain-model.git wk4_capstone_project
cd wk4_capstone_project
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

The base is [Qwen2.5-0.5B-Instruct](https://huggingface.co/Qwen/Qwen2.5-0.5B-Instruct), selected for manageable local inference and an openly downloadable instruct baseline. The configuration pins an immutable Hub revision, which the training run verifies and records. The pinned environment was executed successfully on the Vast.ai RTX 3090; package versions are recorded in reports/training_run.json.

### 2. Data preparation

Place the curated dataset in the project root as `curated_dataset.jsonl` (already included), then run:

```bash
python data_prep.py
python -m pytest -q
```

Preparation enforces 200 records, four categories, 25 scenario groups per category, two paraphrases per group, source alignment, no duplicate normalized questions, and basic identifier screening. Output: `data/` and `reports/validation_report.json`, with zero errors and hashes. Exact tokenizer length checks occur before training; overlong records fail instead of being truncated. Synthetic records still require human policy-owner approval before real use.

### 3. Fine-tuning on Nebius inside tmux

Use a dedicated instance, authenticated Nebius CLI with get/stop permissions for that instance, `tmux`, GNU `timeout`, and an AWS CLI configured for your durable S3-compatible artifact store (including its endpoint). Ensure the boot disk persists on stop. Install dependencies and download the base model before the bounded training window. Training details and loss diagnosis thresholds are in [hyperparameters](configs/hyperparameters.md).

```bash
tmux new -s afyaplus-training
source .venv/bin/activate
export NEBIUS_INSTANCE_ID='your-dedicated-instance-id'
export MAX_RUN_SECONDS='1800' # example only: derive this from your approved budget and rate
export ARTIFACT_URI='s3://your-bucket/afyaplus-capstone/run-001'
bash scripts/train_nebius.sh
```

The wrapper executes `python fine_tune.py`, archives the adapter plus reports to durable storage, and immediately requests a provider-level stop. Exit/error traps and a separate watchdog also attempt stop after failure or the time limit. Upload is included in that limit. If upload fails, recover the adapter from the retained disk; do not retrain blindly. These are best-effort controls: API outages or VM/process failures can defeat them. Monitor from a second machine and verify the provider reports STOPPED. [Nebius stop command](https://docs.nebius.com/cli/reference/compute/instance/stop).

From a separate authenticated workstation after the stop request:

```bash
nebius compute instance get --id "$NEBIUS_INSTANCE_ID" --format json | python scripts/sanitize_provider.py > reports/provider_stop_verification.json
```

Check that the returned state is STOPPED; if it is still running, immediately run `nebius compute instance stop --id "$NEBIUS_INSTANCE_ID"` or stop it in the console. Do not rely on guest shutdown alone. Storage may still be billed. No infrastructure is provisioned by these scripts.

Successful training saves `artifacts/adapter/trainer_state.json`, adapter weights/tokenizer, run manifest, `reports/trainer_state.json`, `reports/training_run.json`, and `reports/loss_curve.png`. The manifest records the exact base revision, data hashes, package versions, GPU, best checkpoint, duration, and evidence-based loss diagnosis. Run the merge and evaluation locally after stopping GPU compute.

### 4. Download adapter, merge and sample

```bash
mkdir -p artifacts
aws s3 cp "$ARTIFACT_URI/adapter-and-reports.tar.gz" artifacts/adapter-and-reports.tar.gz
tar -xzf artifacts/adapter-and-reports.tar.gz
python merge_model.py
python local_inference.py
```

Create `artifacts/` first on a fresh workstation. The archive comes from your own trusted run. Merging uses float32 CPU weights and the exact saved base revision, not four-bit weights. Five actual generated responses (including raw text and gate actions) are saved to `reports/sample_responses.json`. Every user-visible response ends in the mandatory disclaimer.

The safety gate releases only sentences found verbatim in the supplied SOP, redirects recognized clinical/emergency requests, and otherwise returns a safe referral. This is intentionally strict and may reject useful model paraphrases. Raw outputs are diagnostic evaluation artifacts and must not be shown as safe user guidance. Lexical retrieval is a baseline with no accuracy guarantee; it needs separate validation.

### 5. Evaluation and stakeholder report

Configure a separate, capable judge through exported environment variables. Secrets are read from exported variables or an explicitly supplied local `.env` path; they are never written to results. The judge uses the standard chat-completions HTTP format; its endpoint must support JSON-object responses.

```bash
export JUDGE_BASE_URL='https://your-provider.example/v1'
export JUDGE_MODEL='your-independent-judge-model'
read -rs -p 'Judge API key: ' JUDGE_API_KEY
export JUDGE_API_KEY
python evaluate_models.py
```

This performs 40 local generations and 20 paired judge requests. It saves all responses, presentation order, reviewer reasons and usage receipts. Output: `comparison_results.csv`, `reports/evaluation_report.md`, and `memo.md`. Both models receive identical prompts, oracle context and greedy decoding. Candidate order alternates. Raw ROUGE-L excludes the disclaimer. Quality uses a 1–5 anchored rubric; groundedness estimates the fraction of SOP-supported claims. Guarded ROUGE and intervention rates are separate. An API failure leaves partial evidence in `reports/evaluation_progress.json` and prevents a completed comparison claim; rerun after resolving the error. Automated judge scores need human spot checks.

Record actual billed duration (including setup/idle time) and actual contracted price, then regenerate the memo:

```bash
python scripts/record_cost.py --billed-seconds ACTUAL_SECONDS --hourly-rate-usd ACTUAL_RATE --billing-reference YOUR_USAGE_REFERENCE
python report_results.py
python scripts/verify_submission.py
```

Do not substitute training seconds for billed uptime. The calculator excludes storage, network, and reviewer API charges. Relative change is `(tuned - base) / base × 100`; it is undefined when the baseline is zero. The final gate must pass before claiming a complete submission.

## Git workflow and evidence

See [CONTRIBUTING](CONTRIBUTING.md). Use issue-linked semantic commits and a feature PR into main. Issues #1–#5 and draft PR #6 now exist after the token permissions were updated. Keep PRs draft while live evidence is outstanding. Never commit `.claude/`, `CLAUDE.md`, `AGENTS.md`, credentials or binary weights. Save weights to durable artifact storage and commit run hashes and retrieval instructions. Local tests and CI do not constitute proof of a GPU run or improved model quality.

For an optional CPU library compatibility test, run `python scripts/smoke_model_stack.py`. It downloads only the base tokenizer and trains a tiny random model for two steps. Its report is explicitly excluded from capstone training evidence.

The CPU compatibility smoke test passed with PyTorch 2.6.0+cpu, Transformers 4.51.3, and PEFT 0.15.2. All 200 examples tokenized successfully (maximum 190 tokens), two tiny-model optimizer steps completed, adapter merge preserved logits within tolerance, and the saved model reloaded and generated. See `reports/model_stack_smoke.json`; this is not the required CUDA run.

## Vast.ai and OpenRouter setup

The selected provider is now Vast.ai, replacing the originally requested Nebius run. Report the actual provider in training evidence; this is a documented platform substitution. The actual run used instance 50789605, RTX 3090 with 24 GB VRAM. Confirm the current instance, full hourly price, storage/transfer charges and SSH port in the console. The user has a USD 10 balance; this is a ceiling, not a target spend.

`fine_tune.py --provider vast` uses the same QLoRA configuration and records Vast.ai in its manifest. Once the SSH connection, stop permissions and durable artifact destination are configured, run inside tmux:

```bash
export VAST_INSTANCE_ID='50789605' # confirm this is the current dedicated instance
export MAX_RUN_SECONDS='1800' # example; calculate from the verified rate and remaining budget
export ARTIFACT_URI='s3://your-bucket/afyaplus-capstone/run-001'
bash scripts/train_vast.sh
```

This optional automatic wrapper requires `vastai`, `aws`, and configured stop/upload credentials. It follows the same tested failure cleanup and time limit as the Nebius wrapper. Do not run the Nebius wrapper on Vast.ai. From a separately authenticated workstation, save final provider evidence:

```bash
vastai show instance 50789605 --raw | python scripts/sanitize_provider.py > reports/provider_stop_verification.json
```

The evidence checker requires `actual_status: stopped`; an intended stop, frozen or crashed container does not qualify. Stopped instances retain disk data and incur storage charges. Retrieve and verify artifacts before considering destruction, which permanently deletes data. See [Vast.ai lifecycle documentation](https://docs.vast.ai/guides/instances/manage-instances).

The independent evaluation judge can be your existing OpenRouter model:

```bash
export JUDGE_BASE_URL='https://openrouter.ai/api/v1'
export JUDGE_MODEL='openai/gpt-4o-mini'
read -rsp 'OpenRouter API key: ' JUDGE_API_KEY
printf '\n'
export JUDGE_API_KEY
```

The correct model name uses the letter `o` in `4o`. It is independent of the Qwen model being fine-tuned. The evaluator makes 20 paired judge requests after model artifacts are available; charges are separate from Vast.ai. If the key already exists in a local `.env`, provide only its path and variable name for configuration, never its value in chat. See [OpenRouter API setup](https://openrouter.ai/docs/quickstart). To use an existing local credential explicitly, run `python evaluate_models.py --judge-env /path/to/local/.env --judge-key-var OPENROUTER_API_KEY`. This defaults the judge to OpenRouter and `openai/gpt-4o-mini`; keep the file outside Git.

### Recovering the completed Vast.ai run

The initial SSH transfer was incomplete. Do not extract a partial archive. When the same instance is running and its ports have been confirmed, this direct-TLS helper downloads and verifies the adapter against its remote SHA256:

```bash
python scripts/download_vast_artifacts.py --host 188.116.34.4 --ssh-port 21147 --https-port 30553 --instance-id 50789605
```

It trusts only the server certificate obtained through the existing verified SSH connection, sends credentials only to the direct instance IP, refuses redirects, and verifies both size and SHA256 before replacing the destination. The helper uses 64 KiB parallel ranges and resumes by comparing chunk hashes obtained through SSH. A final whole-file SHA256 check is mandatory. The adapter is the priority; `--include-base` optionally retrieves the cached public base model too. Stop GPU compute after verified retrieval; merge and evaluate locally. Port assignments must be rechecked after a restart.

If the judge API fails after local generation, `python evaluate_models.py --reuse-generations` can reuse the saved generations only when the model manifest, test hash and prompt/generation code hashes still match. It requests fresh judge scores and does not reuse partial score results.

### Recorded execution

The actual run used an isolated `/workspace/capstone-env`, the pinned requirements, and `timeout 1200 python fine_tune.py --provider vast` inside tmux. A separate provider-stop watchdog bounded the instance lifetime. Because no S3 destination was configured, artifacts were retained on the instance disk and retrieved over authenticated SSH/direct pinned HTTPS. CPU merging and all 40 generations completed on that instance while the public base-model download on the workstation was stalled. Only the resulting text comparisons were sent from the workstation to OpenRouter; the credential remained local. `--reuse-generations` checks the model manifest, dataset and source-code hashes before scoring these saved responses.

For the same split-compute workflow without putting judge credentials on the instance, run `OMP_NUM_THREADS=4 MKL_NUM_THREADS=4 python evaluate_models.py --generate-only` after merging, followed by `python local_inference.py`. Retrieve `artifacts/evaluation_generations.json`, `artifacts/merged/merge_manifest.json`, and `reports/sample_responses.json`. Then run `python evaluate_models.py --reuse-generations --judge-env /path/to/local/.env` on the workstation. The cache validates the exact model, test data, and generation source hashes.

### Download the preserved trained adapter

The verified adapter is preserved as a [GitHub prerelease](https://github.com/Abdalla-Wasaa/Fine-Tuning-my-domain-model/releases/tag/v0.1.0-capstone). Binary weights remain outside Git history.

```bash
gh release download v0.1.0-capstone --repo Abdalla-Wasaa/Fine-Tuning-my-domain-model --pattern 'afyaplus-adapter-v0.1.0.tar.gz' --pattern SHA256SUMS
sha256sum -c SHA256SUMS
tar -xzf afyaplus-adapter-v0.1.0.tar.gz
python merge_model.py
python local_inference.py
```

Merging downloads the pinned public base model and needs a working Hugging Face connection. The original remote merge is evidenced by the hashes in `reports/evaluation_run.json`; the workstation copy is not yet verified.

# AfyaPlus: fine-tune a domain operations model

Independent Week 4 capstone for appointment workflows, triage escalation routing, registration, and system access. The project lives in `wk4_capstone_project/` locally and occupies the root of the dedicated target repository. No classwork files are modified or imported at runtime.

**Current state:** scripts and the 200-example dataset are implemented; local tests pass. Actual Nebius training, saved merged weights, model sample responses, evaluated scores, billing, and provider-stop evidence are pending access to compute and an independent judge. `comparison_results.csv` deliberately contains empty metrics with explicit pending statuses. Do not submit this state as a completed training run. See [status](reports/status.json) and the [stakeholder memo](memo.md).

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
fine_tune.py                Single-GPU Nebius QLoRA training
training_utils.py           Completion token masking and loss diagnosis
merge_model.py              Merge exact base revision in CPU float32
local_inference.py          Local generation, retrieval and five sample queries
safety.py                   Input routing and fail-closed output gate
evaluate_models.py          Paired 20-question benchmark and LLM judging
report_results.py           Comparison analysis and measured stakeholder memo
comparison_results.csv      Pending until actual evaluation completes
reports/                    Validation, execution evidence and analysis
scripts/train_nebius.sh     Time limit, durable upload and provider stop
scripts/record_cost.py      Actual billed compute cost calculation
scripts/verify_submission.py Evidence completeness gate
tests/                      Offline correctness and safety checks
artifacts/                  Ignored adapter and merged weight storage
```

## Reproduction

### 1. Environment setup

Use Python 3.11 or 3.12. Training needs a CUDA-capable Nebius GPU with compatible NVIDIA drivers; local merging and inference use CPU. Reserve approximately 8 GB available RAM and 8 GB disk for the 0.5B model, adapter, checkpoints, and merged weights; actual usage varies. Verify capacity before reserving a paid instance.

```bash
git clone https://github.com/Abdalla-Wasaa/Fine-Tuning-my-domain-model.git wk4_capstone_project
cd wk4_capstone_project
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

The base is [Qwen2.5-0.5B-Instruct](https://huggingface.co/Qwen/Qwen2.5-0.5B-Instruct), selected for manageable local inference and an openly downloadable instruct baseline. The configuration pins an immutable Hub revision, which the training run verifies and records. The entire pinned GPU environment still needs verification on the actual Nebius instance.

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
nebius compute instance get --id "$NEBIUS_INSTANCE_ID" --format json > reports/provider_stop_verification.json
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

Configure a separate, capable judge through exported environment variables. No secrets are loaded from classroom `.env` files. The judge uses the standard chat-completions HTTP format; its endpoint must support JSON-object responses.

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

See [CONTRIBUTING](CONTRIBUTING.md). Use issue-linked semantic commits and a feature PR into main. The initial token could read the repository but could not create issues; intended #1–#5 references remain pending until permissions are corrected. Keep PRs draft while live evidence is outstanding. Never commit `.claude/`, `CLAUDE.md`, `AGENTS.md`, credentials or binary weights. Save weights to durable artifact storage and commit run hashes and retrieval instructions. Local tests and CI do not constitute proof of a GPU run or improved model quality.

For an optional CPU library compatibility test, run `python scripts/smoke_model_stack.py`. It downloads only the base tokenizer and trains a tiny random model for two steps. Its report is explicitly excluded from capstone training evidence.

The CPU compatibility smoke test passed with PyTorch 2.6.0+cpu, Transformers 4.51.3, and PEFT 0.15.2. All 200 examples tokenized successfully (maximum 190 tokens), two tiny-model optimizer steps completed, adapter merge preserved logits within tolerance, and the saved model reloaded and generated. See `reports/model_stack_smoke.json`; this is not the required CUDA run.

# AfyaPlus LLaMA 3.1 8B operational assistant

Week 4 capstone for Kenyan health operations: appointment access, registration, system access, and administrative escalation. Clinical decisions remain with qualified healthcare providers.

**Submission status: not yet complete.** The replacement corpus contains 200 source-derived examples with 160/20/20 splits, zero structural/citation errors, and 100 clause/page references to official Kenyan sources. Wasaa Abdalla confirmed review and approval of all 100 cases, recorded on 2026-09-15. LLaMA training, merging and evaluation have not run on this corpus. The existing HF_TOKEN successfully accessed the pinned Meta model configuration (HTTP 200 on 2026-09-14), and the current workstation lacks sufficient RAM for the unquantized 8B merge/inference stage. No replacement scores are invented. See `reports/status.json` and `reports/preflight_report.json`.

The earlier completed Qwen experiment is preserved under `experiments/qwen-teaching-v1/`; its metrics and release assets do not qualify as LLaMA results. Its source code is reproducible at commit `3619102f79b0c5fbe33ce5daa067c158a65dc184`.

> This model provides non-diagnostic operational guidance only.

## Project structure

- `data/{train,val,test}.jsonl`: formatted 160/20/20 chat records; all paraphrases of a scenario stay in one split.
- `curated_dataset.jsonl`, `policies.json`: source-derived operational questions and interpretations.
- `data_sources/`: source PDFs, extracted text, versioned URLs and checksums.
- `curation/source_cases.tsv`, `curation/review.csv`: clause-level provenance and named human-review ledger.
- `data_prep.py`, `provenance.py`: formatting, validation, source integrity and review checks.
- `fine_tune.py`, `configs/train.json`: pinned LLaMA 3.1 8B QLoRA configuration.
- `merge_model.py`: float32 CPU merge into weight shards; rejects mismatched historical adapters.
- `local_inference.py`, `safety.py`: local generation and conservative operational safety filter.
- `evaluate_models.py`: 20 paired comparisons with ROUGE-L, independent judge and groundedness.
- `comparison_results.csv`: explicit pending rows until the replacement evaluation completes.
- `report_results.py`, `memo.md`: measured recommendation generated only from a completed comparison.
- `scripts/`: preflight, provider-stop wrappers, billing recording and final verification.
- `experiments/qwen-teaching-v1/`: clearly separated historical evidence.

## Sources and manual review

The source snapshots are the [Data Protection Act](https://new.kenyalaw.org/akn/ke/act/2019/24/eng@2022-12-31/source), [Health Act](https://new.kenyalaw.org/akn/ke/act/2017/21/eng@2026-07-10/source), and [Data Protection (General) Regulations](https://new.kenyalaw.org/akn/ke/act/ln/2021/263/eng%402022-12-31/source), published by Kenya Law. Embedded attribution and licensing notices are preserved. The PDFs/text are review snapshots, not a guarantee of current legal interpretation.

Each example links to a clause, physical PDF page and exact anchor. The answers are AI-assisted operational paraphrases, not verbatim published FAQs or facility-approved SOPs. Automated anchor matching cannot establish that every interpretation is correct. The rubric's manual-verification requirement remains mandatory: a named human must check both questions and the answer against the source, assess current applicability, and record `approved` or `rejected`, reviewer, date (`YYYY-MM-DD`) and notes in `curation/review.csv`. Do not automatically approve the sheet or claim clinician review that did not occur. Changes to questions, guidance or source citations invalidate the review hash.

`python curation/build_candidate.py` reproduces the draft candidate under `curation/replacement/`; it does not overwrite the root human-review ledger. Edits to source cases require rebuilding and deliberately updating the root corpus and ledger before review. Read `data_curation_note.md` for scope and gaps.

## How to reproduce

### 1. Environment setup

Use Linux and Python 3.11/3.12. Training targets a CUDA GPU with at least 24 GiB VRAM. For the current float32 merge and CPU inference, use at least 40 GiB **available** RAM (a 64 GiB machine is recommended) and 80 GiB free disk. The 7.6 GiB workstation used for the earlier Qwen run is insufficient for this path. These are planning requirements, not a measured LLaMA benchmark.

```bash
git clone https://github.com/Abdalla-Wasaa/Fine-Tuning-my-domain-model.git wk4_capstone_project
cd wk4_capstone_project
git switch feat/afyaplus-capstone  # until the completed capstone PR is merged
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Obtain approved access to [Meta LLaMA 3.1 8B Instruct](https://huggingface.co/meta-llama/Llama-3.1-8B-Instruct) on your Hugging Face account and export `HF_TOKEN` securely. Never commit credentials. The pinned revision is recorded in `configs/train.json`; all training, merging and base inference must use it.

### 2. Data preparation

Place the curated dataset in the project root as `curated_dataset.jsonl` (included), complete the human review, then run:

```bash
python data_prep.py
python -m pytest -q
python scripts/preflight.py --provider nebius --check-model-access
```

The preflight can read only `HF_TOKEN` from an explicitly supplied local file using `--hf-env /path/to/local.env`. A structural validation pass does not mean human review passed. Training also performs exact tokenizer checks for all splits and saves minimum, median, 95th percentile and maximum lengths in `reports/token_validation_report.json`; no truncation is allowed.

### 3. Fine-tuning on Nebius inside tmux

Before starting paid compute, resolve source review, model access and memory/storage requirements. Configure the Nebius CLI with permissions for the dedicated instance and an S3-compatible durable artifact destination. Install the pinned requirements and obtain the base weights. Derive the time limit from the actual rate and available credits; the existing $10 deposit is not evidence of the remaining balance.

```bash
tmux new -s afyaplus-training
source .venv/bin/activate
export NEBIUS_INSTANCE_ID='your-instance-id'
export MAX_RUN_SECONDS='1800'  # choose from the verified budget/rate
export ARTIFACT_URI='s3://your-bucket/afyaplus-capstone/llama-run-001'
bash scripts/train_nebius.sh  # executes python fine_tune.py
```

`fine_tune.py` refuses unreviewed data. Hyperparameters and rationale are in `configs/hyperparameters.md`. The wrapper saves/uploads the adapter and reports, then requests a provider-level stop; failure traps and a watchdog also attempt stop. Verify the stopped state from the console or a separate authenticated workstation. Do not leave GPU compute running for CPU merge/evaluation. Storage and transfer can still be charged.

Wasaa Abdalla reports that the instructor verbally agreed to Vast.ai during class. This student-reported provider exception is recorded in `reports/instructor_exceptions.json`; it is not written instructor confirmation or a model exception. Configure `VAST_INSTANCE_ID` and use `scripts/train_vast.sh`. No new cloud instance is created by these scripts.

### 4. Download adapter, merge and run locally

On the sufficiently provisioned CPU machine:

```bash
mkdir -p artifacts
aws s3 cp "$ARTIFACT_URI/adapter-and-reports.tar.gz" artifacts/adapter-and-reports.tar.gz
tar -xzf artifacts/adapter-and-reports.tar.gz
python scripts/preflight.py --stage merge --provider nebius
python merge_model.py
python local_inference.py
```

The archive must come from your trusted completed LLaMA run and contain `artifacts/adapter/`. Use an empty merge output directory to avoid stale shards. Hashes are streamed to avoid reading multi-gigabyte weights into memory. Five sample responses are written with the mandatory disclaimer. The safety gate releases only supported guidance sentences; it can reject useful paraphrases. Clinical requests are redirected. This is not clinical validation or a guarantee of retrieval quality.

### 5. Evaluation and memo

Use the same merged artifact and held-out test files. Configure an independent judge:

```bash
export JUDGE_BASE_URL='https://openrouter.ai/api/v1'
export JUDGE_MODEL='openai/gpt-4o-mini'
# Export JUDGE_API_KEY securely, or supply a local dotenv file below.
python evaluate_models.py --judge-env /path/to/local.env --judge-key-var OPENROUTER_API_KEY
```

The evaluator makes 40 local generations and 20 paired judge requests. It saves `comparison_results.csv`, per-question responses and reasons, the three largest/smallest changes, and the memo. Both models receive the same source-derived operational guidance; this evaluates context following, not retrieval accuracy or clinical competence. Twenty questions represent ten independent scenarios. ROUGE excludes the disclaimer; safety intervention rates are separate.

To keep judge credentials on a separate workstation, run `python evaluate_models.py --generate-only` on the inference machine, retrieve `artifacts/evaluation_generations.json` and the merge manifest, then use `--reuse-generations` with local judge credentials. Cache hashes must match model, data and generation code. Never reuse historical Qwen outputs for this corpus.

Record actual billed compute time/rate from the provider usage record, including setup and idle time:

```bash
python scripts/record_cost.py --billed-seconds ACTUAL_SECONDS --hourly-rate-usd ACTUAL_RATE --billing-reference YOUR_USAGE_REFERENCE
nebius compute instance get --id "$NEBIUS_INSTANCE_ID" --format json | python scripts/sanitize_provider.py > reports/provider_stop_verification.json
python report_results.py
python scripts/verify_submission.py
```

The cost calculator excludes storage, network and judge charges; identify those separately. Do not substitute optimizer time for billed uptime. The final gate checks model identity, source/review hashes, exact tokenizer evidence, artifact hashes, 20 completed paired evaluations, five samples, cost and stopped-state evidence. Even a passing gate needs human provenance review.

## Submission and Git workflow

Use issue-linked semantic commits and PR review as documented in `CONTRIBUTING.md`. PR #6 remains draft while the replacement run is blocked. When all rubric evidence is complete, merge into `main` so the submitted root repository link exposes the deliverables. Publish trained artifacts separately with checksums; never commit model weights, `.env`, `.claude/`, `CLAUDE.md` or `AGENTS.md`.

This model provides non-diagnostic operational guidance only.

Dataset reviewer: Wasaa Abdalla. Read [the review pack](curation/REVIEW_PACK.md) and enter actual decisions and dates in [the review ledger](curation/review.csv). Assignment does not establish completed review.

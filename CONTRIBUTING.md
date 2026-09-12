# Contributing

Use main as the integration branch and short-lived feat/, fix/, or docs/ branches. Open a pull request against main; keep it draft while required run evidence is missing. Require passing CI and review before merging. Do not force-push shared branches.

Use semantic commit messages with issue references:

- `feat(data): validate grouped dataset (#1)`
- `feat(training): add reproducible QLoRA pipeline (#2)`
- `feat(inference): merge and guard model outputs (#3)`
- `feat(eval): compare paired model outputs (#4)`
- `docs: document reproduction and stakeholder evidence (#5)`

Issue numbers #1–#5 are reserved in the planned workflow but must be created when repository token permissions allow. References alone do not prove the issues exist. Do not close training/evaluation issues without actual artifacts and verified results.

Run `python data_prep.py`, `python -m pytest -q`, and `bash -n scripts/train_nebius.sh` before proposing changes. Run `python scripts/verify_submission.py` before claiming the full capstone is complete. CI checks source/data; it does not certify GPU training.

Never commit secrets, environments, model binaries, `.claude/`, `CLAUDE.md`, or `AGENTS.md`. Review staged paths and `git diff --cached` before committing. Model weights belong in durable artifact storage; commit their provenance/hashes and retrieval instructions. Dataset changes require source-owner review and fresh splits, training, and evaluation. Do not select training settings using test scores.

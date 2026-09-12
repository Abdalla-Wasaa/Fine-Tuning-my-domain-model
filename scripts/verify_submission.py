"""Fail closed if the capstone lacks consistent actual run evidence."""
import csv
import json
import math
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common import ROOT, DISCLAIMER, read_jsonl, sha256


def stopped(status):
    """Accept only an explicit STOPPED state in the provider's status object."""
    if not isinstance(status, dict):
        return False
    if 'actual_status' in status:
        return status['actual_status'] == 'stopped'
    if 'state' in status:
        return status['state'] == 'STOPPED'
    return any(stopped(v) for v in status.values() if isinstance(v, dict))


def check(root=ROOT):
    errors = []
    required = ['reports/validation_report.json', 'reports/trainer_state.json', 'reports/loss_curve.png',
                'reports/training_run.json', 'artifacts/adapter/adapter_model.safetensors',
                'artifacts/adapter/run_manifest.json', 'artifacts/merged/merge_manifest.json',
                'reports/sample_responses.json', 'reports/evaluation_run.json',
                'reports/evaluation_details.json', 'reports/evaluation_report.md',
                'reports/compute_cost.json', 'reports/provider_stop_verification.json']
    for file in required:
        if not (root / file).is_file() or (root / file).stat().st_size == 0:
            errors.append(f'Missing real evidence: {file}')
    rows = list(csv.DictReader((root / 'comparison_results.csv').open()))
    test_ids = {r['id'] for r in read_jsonl(root / 'data/test.jsonl')}
    if len(rows) != 20 or {r['id'] for r in rows} != test_ids or any(r['status'] != 'completed' for r in rows):
        errors.append('20 completed paired evaluations matching test IDs required')
    else:
        for row in rows:
            for model in ('base', 'tuned'):
                for metric, low, high in [('rouge_l', 0, 1), ('llm_judge', 1, 5), ('groundedness', 0, 1), ('guarded_rouge_l', 0, 1)]:
                    try:
                        value = float(row[f'{model}_{metric}'])
                        assert math.isfinite(value) and low <= value <= high
                    except (ValueError, KeyError, AssertionError):
                        errors.append(f"Invalid metric: {row['id']} {model}_{metric}")
    def read(name):
        path = root / name
        if not path.exists():
            return None
        try:
            return json.loads(path.read_text())
        except ValueError:
            errors.append(f'Invalid JSON evidence: {name}')
            return None
    validation = read('reports/validation_report.json')
    if validation and validation.get('error_count') != 0:
        errors.append('Dataset validation contains errors')
    training = read('reports/training_run.json')
    if training is not None:
        if training.get('status') != 'completed' or training.get('training_seconds', 0) <= 0:
            errors.append('Successful timed training evidence required')
        for split in ('train', 'val', 'test'):
            if training.get('data_sha256', {}).get(split) != sha256(root / f'data/{split}.jsonl'):
                errors.append(f'Training {split} hash mismatch')
    state = read('reports/trainer_state.json')
    if state and (state.get('global_step', 0) <= 0 or not any('eval_loss' in r for r in state.get('log_history', []))):
        errors.append('Trainer state lacks optimizer steps or validation loss')
    samples = read('reports/sample_responses.json')
    if samples is not None:
        if len(samples) < 5 or any(not r.get('response', '').endswith(DISCLAIMER) for r in samples):
            errors.append('Five inference responses with mandatory disclaimer required')
        if not any(r.get('raw') for r in samples):
            errors.append('Samples must include actual model generation')
    merge = read('artifacts/merged/merge_manifest.json')
    if merge is not None:
        if not merge.get('weights'):
            errors.append('Merged weight hashes missing')
        for name, digest in merge.get('weights', {}).items():
            path = root / 'artifacts/merged' / name
            if not path.is_file() or sha256(path) != digest:
                errors.append(f'Merged weight missing or hash mismatch: {name}')
        adapter = root / 'artifacts/adapter/adapter_model.safetensors'
        if adapter.exists() and sha256(adapter) != merge.get('adapter_sha256'):
            errors.append('Merged adapter hash mismatch')
    evaluation = read('reports/evaluation_run.json')
    if evaluation is not None:
        if evaluation.get('status') != 'completed' or evaluation.get('test_sha256') != sha256(root / 'data/test.jsonl'):
            errors.append('Evaluation status or test hash mismatch')
        if merge is not None and evaluation.get('merge') != merge:
            errors.append('Evaluation does not match current merged model')
    provider = read('reports/provider_stop_verification.json')
    if provider is not None and not stopped(provider.get('status', provider)):
        errors.append('Provider has not explicitly confirmed STOPPED')
    costs = read('reports/compute_cost.json')
    if costs is not None:
        try:
            seconds, rate, total = [float(costs[k]) for k in ('billed_seconds', 'hourly_rate_usd', 'compute_usd')]
            assert all(math.isfinite(x) and x >= 0 for x in (seconds, rate, total)) and seconds > 0
            assert math.isclose(total, seconds / 3600 * rate)
        except (ValueError, KeyError, AssertionError):
            errors.append('Invalid compute billing evidence')
    return errors


if __name__ == '__main__':
    problems = check()
    print('\n'.join(problems) if problems else 'Submission evidence complete; human provenance review still required')
    raise SystemExit(bool(problems))

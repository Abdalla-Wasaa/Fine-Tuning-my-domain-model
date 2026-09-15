"""Synthetic score fixtures stay in pytest's temporary directory only."""
import csv
import json
from common import DISCLAIMER
from evaluate_models import FIELDS
import report_results


def test_report_ranks_real_deltas_and_labels_missing_cost(tmp_path, monkeypatch):
    monkeypatch.setattr(report_results, 'ROOT', tmp_path)
    (tmp_path / 'reports').mkdir()
    rows, details = [], []
    for i in range(20):
        row = {k: '' for k in FIELDS}
        row.update(id=str(i), scenario_id=str(i//2), category='fixture', status='completed')
        for name in ('base', 'tuned'):
            row.update({f'{name}_rouge_l': 0.5, f'{name}_llm_judge': 3 if name == 'base' else 1 + i/5,
                        f'{name}_groundedness': 0.9, f'{name}_guarded_rouge_l': 0.5,
                        f'{name}_safety_action': 'supported_verbatim'})
        rows.append(row)
        details.append({'id': str(i), 'question': f'Fixture {i}', 'context': 'Reference.', 'base_raw': 'Reference.', 'tuned_raw': 'Reference.',
                        'judge': {'base': {'reason': 'Fixture base'}, 'tuned': {'reason': 'Fixture tuned', 'groundedness': 0.9}}})
    with (tmp_path / 'comparison_results.csv').open('w') as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS); writer.writeheader(); writer.writerows(rows)
    (tmp_path / 'reports/evaluation_details.json').write_text(json.dumps(details))
    report_results.generate_report()
    report = (tmp_path / 'reports/evaluation_report.md').read_text()
    assert report.index('### 19:') < report.index('### 18:')
    assert 'including regressions' in report
    assert 'Judge consistency limitation' in report
    assert '|---|---:|---:|---:|\n| rouge_l' in report
    memo = (tmp_path / 'memo.md').read_text()
    assert 'unverified' in memo and DISCLAIMER in memo


def test_relative_zero_baseline():
    assert report_results.relative(0, 1) == 'not defined (zero baseline)'
    assert report_results.relative(2, 3) == '+50.0%'

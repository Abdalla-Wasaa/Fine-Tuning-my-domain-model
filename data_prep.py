"""Validate curated source data and produce deterministic, group-disjoint splits."""
import argparse
from collections import Counter, defaultdict
import json
import random
import re
from pathlib import Path
from common import ROOT, DISCLAIMER, messages, read_jsonl, sha256, write_json


def validate(rows, policies):
    errors, seen_ids, seen_questions = [], set(), set()
    groups = defaultdict(list)
    rules = {r['id']: r for r in policies['rules']}
    if len(rows) < 200:
        errors.append('At least 200 records required for a 20-example 10% test split.')
    required = ('id', 'scenario_id', 'category', 'source_id', 'question', 'answer')
    for i, row in enumerate(rows):
        if not isinstance(row, dict) or any(not isinstance(row.get(k), str) or not row[k].strip() for k in required):
            errors.append(f'Row {i}: missing/non-string required field')
            continue
        if row['id'] in seen_ids:
            errors.append(f'Row {i}: duplicate ID')
        seen_ids.add(row['id'])
        question = re.sub(r'\W+', ' ', row['question'].lower()).strip()
        if question in seen_questions:
            errors.append(f'Row {i}: duplicate normalized question')
        seen_questions.add(question)
        rule = rules.get(row['source_id'])
        if not rule or row['category'] != rule['category'] or row['answer'] != rule['guidance']:
            errors.append(f'Row {i}: answer/category is not grounded in cited SOP')
        if row['scenario_id'] != row['source_id']:
            errors.append(f'Row {i}: scenario/source mismatch')
        for field in ('question', 'answer'):
            if re.search(r'[\w.+-]+@[\w.-]+\.[a-zA-Z]{2,}|\b\+?\d[\d -]{8,}\d\b', row[field]):
                errors.append(f'Row {i}: possible personal identifier')
        groups[row['scenario_id']].append(row)
    by_category = Counter()
    for group, members in groups.items():
        if len(members) != 2:
            errors.append(f'{group}: expected exactly two paraphrases per scenario')
        by_category[members[0]['category']] += 1
    if set(by_category) != {'appointments', 'escalation', 'registration', 'access'}:
        errors.append('Expected all four domain categories')
    if any(n % 10 != 5 for n in by_category.values()):
        # 25 groups: 20 train + alternating 2/3 validation/test per category.
        errors.append('Category group count must be 25 for this fixed benchmark')
    if any(n != 25 for n in by_category.values()):
        errors.append('Expected exactly 25 scenario groups per category')
    return errors


def prepare(source=ROOT / 'curated_dataset.jsonl', output=ROOT / 'data', report=ROOT / 'reports/validation_report.json'):
    policies = json.loads((ROOT / 'policies.json').read_text())
    try:
        rows = read_jsonl(source)
        errors = validate(rows, policies)
    except (ValueError, TypeError) as exc:
        rows, errors = [], [f'Invalid JSONL: {exc}']
    result = {'records': len(rows), 'errors': errors, 'error_count': len(errors),
              'source_sha256': sha256(source), 'policy_sha256': sha256(ROOT / 'policies.json'),
              'seed': 42, 'token_check': 'Exact tokenizer length enforced before training; no truncation permitted.'}
    if errors:
        write_json(report, result)
        raise ValueError('; '.join(errors))
    groups = defaultdict(list)
    for row in rows:
        groups[row['scenario_id']].append(row)
    rng = random.Random(42)
    splits = {'train': [], 'val': [], 'test': []}
    for index, category in enumerate(sorted({r['category'] for r in rows})):
        ids = sorted(g for g, members in groups.items() if members[0]['category'] == category)
        rng.shuffle(ids)
        val_groups = 2 if index % 2 == 0 else 3
        for split, group_ids in [('train', ids[:20]), ('val', ids[20:20+val_groups]), ('test', ids[20+val_groups:])]:
            for group in group_ids:
                for row in groups[group]:
                    context = row['answer']
                    splits[split].append({**row, 'context': context,
                        'messages': messages(row['question'], context) + [
                            {'role': 'assistant', 'content': context + '\n\n' + DISCLAIMER}]})
    assert [len(splits[s]) for s in splits] == [160, 20, 20]
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    for split, records in splits.items():
        (output / f'{split}.jsonl').write_text(''.join(json.dumps(r) + '\n' for r in records))
    result['splits'] = {s: {'count': len(rs), 'categories': dict(Counter(r['category'] for r in rs)),
                           'sha256': sha256(output / f'{s}.jsonl')} for s, rs in splits.items()}
    result['group_overlap'] = 0
    write_json(report, result)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, default=ROOT / 'curated_dataset.jsonl')
    parser.add_argument('--output', type=Path, default=ROOT / 'data')
    args = parser.parse_args()
    print(json.dumps(prepare(args.input, args.output), indent=2))


if __name__ == '__main__':
    main()

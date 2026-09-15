"""Create a readable review pack without changing any review decisions."""
import csv
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]


def main():
    sources = {s['id']: s for s in json.loads((ROOT/'data_sources/manifest.json').read_text())}
    rules = {r['id']: r for r in json.loads((ROOT/'policies.json').read_text())['rules']}
    with (ROOT/'curation/review.csv').open() as f:
        rows = list(csv.DictReader(f))
    lines = ['# AfyaPlus dataset review pack', '',
             'Assigned reviewer: Wasaa Abdalla. Assignment is not approval.', '',
             'Review 100 cases (two questions per case). Record decisions in `review.csv`.', '',
             'For each case: read the cited section and PDF, then check both questions and the answer. '
             'Confirm that every operational instruction is supported, terminology is clear, and no diagnosis, '
             'treatment, invented facility policy, fee, or deadline is introduced. '
             'Check surrounding exceptions and current applicability. These sources establish general requirements; '
             'they do not prove AfyaPlus has adopted a particular local SOP.', '',
             'Set decision to `approved` only after checking; otherwise use `rejected` and explain the correction '
             'in notes. Enter the actual review date as YYYY-MM-DD. Keep scenario_id and review_hash unchanged. '
             'Do not edit answer text only in the CSV: report corrections so the dataset can be regenerated '
             'and reviewed again. Leave uncertain cases pending. No clinical qualification is inferred.', '',
             'Sources were refreshed from official Kenya Law canonical pages on 2026-09-15. '
             'Automated checks verify file hashes and clause/page anchors, not the correctness of interpretation.', '']
    for row in rows:
        citation = rules[row['scenario_id']]['citation']
        source = sources[citation['document_id']]
        text = (ROOT/source['text']).read_text()
        number = int(citation['clause'].split('(')[0])
        start = re.search(rf'(?m)^{number}\.\n', text)
        end = re.search(r'(?m)^\d+\.\n', text[start.end():])
        section = text[start.start():start.end()+end.start() if end else len(text)].strip()
        lines.extend([f"## {row['scenario_id']}", '',
            f"Source: [{source['title']}]({source['url']}); version {source['version']}; clause {citation['clause']}; PDF page {citation['pdf_page']}.", '',
            f"[Local PDF](../{source['pdf']}#page={citation['pdf_page']})", '',
            f"**Question 1:** {row['question_1']}", '', f"**Question 2:** {row['question_2']}", '',
            f"**Proposed answer:** {row['guidance']}", '',
            '**Cited section (check exceptions as well as the matching phrase):**', '',
            '```text', section, '```', '',
            f"Current decision: {row['decision']}. Record your decision and notes in review.csv.", ''])
    (ROOT/'curation/REVIEW_PACK.md').write_text('\n'.join(lines)+'\n')
    print(f'Prepared {len(rows)} cases; decisions unchanged.')


if __name__ == '__main__':
    main()

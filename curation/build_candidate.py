"""Build a reviewable source-derived corpus; never assert human review occurred."""
import csv
import hashlib
import json
from pathlib import Path
import re
import unicodedata

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'curation/replacement'


def normalize(text):
    return ' '.join(unicodedata.normalize('NFKC', text).split()).casefold()


def build():
    sources = {s['id']: s for s in json.loads((ROOT / 'data_sources/manifest.json').read_text())}
    cases = list(csv.DictReader((ROOT / 'curation/source_cases.tsv').open(), delimiter='\t'))
    assert len(cases) == 100
    rules, rows, reviews = [], [], []
    counts = {}
    for case in cases:
        source = sources[case['document']]
        assert hashlib.sha256((ROOT / source['pdf']).read_bytes()).hexdigest() == source['sha256']
        text = (ROOT / source['text']).read_text()
        number = int(case['clause'].split('(')[0])
        start = re.search(rf'(?m)^{number}\.\n', text)
        assert start, f'Missing section: {case}'
        following = re.search(r'(?m)^\d+\.\n', text[start.end():])
        end = start.end() + following.start() if following else len(text)
        section = text[start.start():end]
        assert normalize(case['anchor']) in normalize(section), f'Anchor not in cited section: {case}'
        # Match the anchor in a physical page, restricted to pages intersecting this section.
        pages = list(re.finditer(r'--- PDF PAGE (\d+) ---\n', text))
        page = None
        for i, marker in enumerate(pages):
            page_end = pages[i+1].start() if i+1 < len(pages) else len(text)
            a, b = max(start.start(), marker.end()), min(end, page_end)
            if a < b and normalize(case['anchor']) in normalize(text[a:b]):
                page = int(marker.group(1)); break
        assert page, f'Anchor spans a page boundary or not found: {case}'
        category = case['category']; counts[category] = counts.get(category, 0) + 1
        id = f'{category}-{counts[category]:02d}'
        citation = {'document_id': source['id'], 'clause': case['clause'], 'pdf_page': page,
                    'url': source['url'], 'anchor': case['anchor'], 'document_sha256': source['sha256']}
        rule = {'id': id, 'category': category, 'scenario': case['scenario'], 'guidance': case['guidance'],
                'citation': citation, 'review_status': 'pending_human_review'}
        rules.append(rule)
        questions = [f"What should AfyaPlus staff in Kenya do when {case['scenario']}?",
                     f"At an AfyaPlus facility in Kenya, how should staff handle this: {case['scenario']}?"]
        digest = hashlib.sha256(json.dumps({'rule': rule, 'questions': questions}, sort_keys=True).encode()).hexdigest()
        for i, question in enumerate(questions, 1):
            rows.append({'id': f'{id}-{i}', 'scenario_id': id, 'category': category, 'source_id': id,
                         'question': question, 'answer': case['guidance'], 'citation': citation,
                         'review_hash': digest})
        reviews.append({'scenario_id': id, 'review_hash': digest, 'source_url': source['url'],
                        'clause': case['clause'], 'pdf_page': page, 'anchor': case['anchor'],
                        'question_1': questions[0], 'question_2': questions[1], 'guidance': case['guidance'],
                        'decision': 'pending', 'reviewer': '', 'reviewed_at': '', 'notes': ''})
    assert set(counts.values()) == {25}
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / 'curated_dataset.jsonl').write_text(''.join(json.dumps(r, ensure_ascii=False)+'\n' for r in rows))
    (OUT / 'policies.json').write_text(json.dumps({'version': '2.0', 'status': 'Source-derived operational interpretations; human review pending; not facility-approved SOPs', 'rules': rules}, indent=2)+'\n')
    review_path = OUT / 'review.csv'
    if review_path.exists():
        prior = {r['review_hash']: r for r in csv.DictReader(review_path.open())}
        for row in reviews:
            if row['review_hash'] in prior:
                row.update({k: prior[row['review_hash']][k] for k in ('decision','reviewer','reviewed_at','notes')})
    with review_path.open('w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=list(reviews[0]), lineterminator='\n'); writer.writeheader(); writer.writerows(reviews)
    (OUT / 'source_validation.json').write_text(json.dumps({'records':len(rows),'scenario_groups':len(rules),
        'source_anchor_checks':len(rules),'error_count':0,'human_review_complete':False,
        'scope':'Exact anchors found in cited sections/pages of hash-verified source snapshots; this does not verify every interpretation or current legal applicability.'},indent=2)+'\n')
    print(f'Built {len(rows)} source-derived examples; {len(rules)} clause/page anchors verified. Human review pending.')


if __name__ == '__main__':
    build()

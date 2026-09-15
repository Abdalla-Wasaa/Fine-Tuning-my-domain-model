"""Fail closed on missing citations, changed sources, or unrecorded human review."""
import csv
from datetime import date
import hashlib
import json
from pathlib import Path
import re
import unicodedata
from common import ROOT, read_jsonl


def normalize(value):
    return ' '.join(unicodedata.normalize('NFKC', value).split()).casefold()


def validate_provenance(root=ROOT, require_human=False):
    root = Path(root)
    errors = []
    try:
        sources = {s['id']: s for s in json.loads((root/'data_sources/manifest.json').read_text())}
        rules = json.loads((root/'policies.json').read_text())['rules']
        rows = read_jsonl(root/'curated_dataset.jsonl')
        reviews_list = list(csv.DictReader((root/'curation/review.csv').open()))
        reviews = {r['scenario_id']:r for r in reviews_list}
        if len(reviews_list) != len(reviews): errors.append('Duplicate human-review entries')
        texts = {}
        for id, source in sources.items():
            for key, digest_key in [('pdf','sha256'),('text','text_sha256')]:
                if hashlib.sha256((root/source[key]).read_bytes()).hexdigest() != source[digest_key]:
                    errors.append(f'{id}: changed {key} source snapshot')
            texts[id] = (root/source['text']).read_text()
        for rule in rules:
            id = rule['id']; citation = rule['citation']; source = sources[citation['document_id']]
            if citation['document_sha256'] != source['sha256'] or citation['url'] != source['url']:
                errors.append(f'{id}: citation does not match source manifest')
            text = texts[source['id']]; number = int(citation['clause'].split('(')[0])
            match = re.search(rf'(?m)^{number}\.\n',text)
            if not match:
                errors.append(f'{id}: cited section missing'); continue
            following = re.search(r'(?m)^\d+\.\n', text[match.end():])
            end = match.end()+following.start() if following else len(text)
            if normalize(citation['anchor']) not in normalize(text[match.start():end]):
                errors.append(f'{id}: cited anchor not in cited section')
            pages = re.split(r'--- PDF PAGE \d+ ---\n',text)[1:]
            page = citation['pdf_page']
            if not isinstance(page,int) or not 1 <= page <= len(pages) or normalize(citation['anchor']) not in normalize(pages[page-1]):
                errors.append(f'{id}: cited anchor not on cited page')
            members = [r for r in rows if r['scenario_id']==id]
            digest = hashlib.sha256(json.dumps({'rule':rule,'questions':[r['question'] for r in members]},sort_keys=True).encode()).hexdigest()
            if len(members)!=2 or any(r.get('review_hash')!=digest or r.get('citation')!=citation or r['answer']!=rule['guidance'] for r in members):
                errors.append(f'{id}: examples changed since review preparation')
            review = reviews.get(id,{})
            if review.get('review_hash') != digest:
                errors.append(f'{id}: review ledger does not match examples')
            if require_human:
                try:
                    assert review.get('decision')=='approved' and review.get('reviewer','').strip()
                    reviewed = date.fromisoformat(review.get('reviewed_at',''))
                    assert reviewed <= date.today()
                except (ValueError,AssertionError):
                    errors.append(f'{id}: named, dated human source review required')
    except (OSError,ValueError,KeyError,TypeError) as exc:
        errors.append(f'Invalid or missing provenance evidence: {type(exc).__name__}')
    return errors


def provider_errors(provider, root=ROOT):
    if provider == 'nebius': return []
    try:
        value = json.loads((Path(root)/'reports/instructor_exceptions.json').read_text())
        record = value['provider']
        assert record['approved_provider']==provider and record['evidence_reference'].strip()
        if record.get('evidence_type') == 'student_reported_verbal_approval':
            assert record['reported_by'].strip() and record['approval_statement'].strip()
            assert date.fromisoformat(record['reported_at']) <= date.today()
        else:
            assert record['instructor'].strip()
            assert date.fromisoformat(record['approved_at']) <= date.today()
        return []
    except (OSError,ValueError,KeyError,TypeError,AssertionError):
        return ['Instructor approval evidence required for provider substitution: '+provider]

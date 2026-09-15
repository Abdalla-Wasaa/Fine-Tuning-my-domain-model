"""Review fixtures below are synthetic and never written into real submission evidence."""
import csv
import json
from pathlib import Path
import shutil
from common import ROOT
from provenance import validate_provenance, provider_errors


def fixture_copy(tmp_path):
    for name in ['data_sources','curation']:
        shutil.copytree(ROOT/name,tmp_path/name)
    for name in ['curated_dataset.jsonl','policies.json']:
        shutil.copy2(ROOT/name,tmp_path/name)
    return tmp_path


def test_actual_sources_have_valid_anchors():
    assert validate_provenance() == []


def test_human_review_is_separate_from_structural_validation(tmp_path):
    root=fixture_copy(tmp_path)
    path=root/'curation/review.csv'
    rows=list(csv.DictReader(path.open()))
    for row in rows:row.update(decision='pending',reviewer='',reviewed_at='')
    with path.open('w',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=rows[0]);writer.writeheader();writer.writerows(rows)
    assert validate_provenance(root)==[]
    assert len(validate_provenance(root,require_human=True))==100
    for row in rows:row.update(decision='approved',reviewer='Synthetic test reviewer',reviewed_at='2020-01-01')
    with path.open('w',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=rows[0]);writer.writeheader();writer.writerows(rows)
    assert validate_provenance(root,require_human=True)==[]
    data=root/'curated_dataset.jsonl';text=data.read_text();data.write_text(text.replace('What should AfyaPlus','Changed question for AfyaPlus',1))
    assert any('changed since review' in e for e in validate_provenance(root,require_human=True))


def test_changed_source_snapshot_is_rejected(tmp_path):
    root=fixture_copy(tmp_path);p=root/'data_sources/health_act.txt';p.write_text(p.read_text()+'\nchanged')
    assert any('changed text source snapshot' in e for e in validate_provenance(root))


def test_wrong_page_or_anchor_is_rejected(tmp_path):
    root=fixture_copy(tmp_path);p=root/'policies.json';d=json.loads(p.read_text());d['rules'][0]['citation']['pdf_page']=1;p.write_text(json.dumps(d))
    assert any('not on cited page' in e for e in validate_provenance(root))


def test_provider_exception_needs_evidence(tmp_path):
    assert provider_errors('nebius',tmp_path)==[]
    assert provider_errors('vast',tmp_path)
    (tmp_path/'reports').mkdir()
    (tmp_path/'reports/instructor_exceptions.json').write_text(json.dumps({'provider':{'approved_provider':'vast','instructor':'Synthetic fixture','approved_at':'2020-01-01','evidence_reference':'test fixture only'}}))
    assert provider_errors('vast',tmp_path)==[]


def test_student_reported_verbal_exception_is_distinguished(tmp_path):
    (tmp_path/'reports').mkdir()
    path=tmp_path/'reports/instructor_exceptions.json'
    record={'approved_provider':'vast','evidence_type':'student_reported_verbal_approval',
            'reported_by':'Synthetic student','reported_at':'2020-01-01',
            'approval_statement':'Provider approved verbally in class',
            'evidence_reference':'Synthetic student report only'}
    path.write_text(json.dumps({'provider':record}))
    assert provider_errors('vast',tmp_path)==[]
    record['reported_by']=''
    path.write_text(json.dumps({'provider':record}))
    assert provider_errors('vast',tmp_path)

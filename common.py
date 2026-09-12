"""Shared, dependency-light configuration and provenance helpers."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DISCLAIMER = 'This model provides non-diagnostic operational guidance only.'
SYSTEM_PROMPT = ('You are the AfyaPlus operational assistant. Use only the supplied teaching SOP. '
                 'Explain administrative workflows. Never diagnose, prescribe, interpret clinical results, '
                 'assign clinical priority, or bypass identity and access controls. '
                 'Refer clinical decisions to qualified clinical staff. If the SOP does not answer a question, '
                 'say so and refer to the responsible facility team. End every response with: ' + DISCLAIMER)


def read_jsonl(path):
    with Path(path).open() as stream:
        return [json.loads(line) for line in stream if line.strip()]


def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + '\n')


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def config():
    return json.loads((ROOT / 'configs/train.json').read_text())


def messages(question, context):
    return [{'role': 'system', 'content': SYSTEM_PROMPT},
            {'role': 'user', 'content': f'Teaching SOP excerpt:\n{context}\n\nQuestion: {question}'}]

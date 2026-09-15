"""Conservative operational guard: only SOP sentences are released to users.

This intentionally trades fluency for a bounded teaching prototype. A model cannot
introduce unsupported clinical instructions merely by avoiding a keyword list.
"""
import re
from common import DISCLAIMER

FALLBACK = 'Please contact the responsible AfyaPlus facility team for the approved operational workflow. Clinical decisions must be handled by qualified clinical staff.'
EMERGENCY = 'Alert the on-site clinical emergency team immediately, or contact local emergency services if you are remote. Do not delay escalation for registration or payment.'


def finish(text):
    return text.replace(DISCLAIMER, '').strip() + '\n\n' + DISCLAIMER


def precheck(question):
    if re.search(r'\b(immediate danger|unconscious|not breathing|cannot breathe|severe bleeding|suicid\w*)\b', question, re.I):
        return finish(EMERGENCY), 'emergency_escalation'
    if re.search(r'\b(diagnose me|what (disease|medicine|dose)|which (medicine|drug)|should i take|prescribe|interpret my)\b', question, re.I):
        return finish('Please contact a qualified clinician for assessment or an authorized pharmacist for medicine questions. I can help with the operational route to that service.'), 'clinical_redirect'
    return None


def guard(question, raw, context):
    checked = precheck(question)
    if checked:
        return checked
    body = raw.replace(DISCLAIMER, '').strip()
    # Exact sentence support, not an assertion that lexical similarity proves safety.
    allowed = {s.strip() for s in re.split(r'(?<=[.!?])\s+', context) if s.strip()}
    sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', body) if s.strip()]
    if sentences and all(s in allowed for s in sentences):
        return finish(body), 'supported_verbatim'
    return finish(FALLBACK), 'unsupported_output_blocked'

"""Generate paired analysis and an evidence-based stakeholder memo from real results."""
import csv
import json
from statistics import mean
from common import ROOT, DISCLAIMER


def relative(base, tuned):
    return 'not defined (zero baseline)' if base == 0 else f'{100 * (tuned-base)/base:+.1f}%'


def generate_report():
    rows = list(csv.DictReader((ROOT / 'comparison_results.csv').open()))
    if len(rows) != 20 or any(r['status'] != 'completed' for r in rows):
        raise ValueError('All 20 paired evaluations must complete before reporting improvement')
    details = {r['id']: r for r in json.loads((ROOT / 'reports/evaluation_details.json').read_text())}
    lines = ['# Base versus tuned evaluation', '', '20 questions represent 10 independent scenarios (two paraphrases each). '
             'This is a small teaching benchmark, not clinical validation. Both models receive the reference SOP as context. '
             'Raw metrics exclude the fixed disclaimer; guarded ROUGE is reported separately. '
             'Groundedness is a judge estimate of supported substantive claims, not a safety guarantee.', '',
             '| Metric | Base | Tuned | Relative change |', '|---|---:|---:|---:|']
    averages = {}
    for metric in ['rouge_l', 'llm_judge', 'groundedness', 'guarded_rouge_l']:
        base, tuned = [mean(float(r[f'{m}_{metric}']) for r in rows) for m in ('base', 'tuned')]
        averages[metric] = (base, tuned)
        lines.append(f'| {metric} | {base:.4f} | {tuned:.4f} | {relative(base, tuned)} |')
    # Rank by raw quality gain, then raw ROUGE; never label a regression an improvement.
    ranked = sorted(rows, key=lambda r: (float(r['tuned_llm_judge'])-float(r['base_llm_judge']),
                                        float(r['tuned_rouge_l'])-float(r['base_rouge_l'])), reverse=True)
    for heading, selected in [('Three largest changes', ranked[:3]), ('Three smallest changes (including regressions)', ranked[-3:])]:
        lines += ['', f'## {heading}', '']
        for r in selected:
            d = details[r['id']]
            lines += [f"### {r['id']}: {d['question']}",
                      f"Quality {r['base_llm_judge']} → {r['tuned_llm_judge']}; ROUGE-L {float(r['base_rouge_l']):.3f} → {float(r['tuned_rouge_l']):.3f}.",
                      f"Base: {d['base_raw']}", f"Tuned: {d['tuned_raw']}",
                      f"Judge rationale — base: {d['judge']['base']['reason']} Tuned: {d['judge']['tuned']['reason']}", '']
    lines += ['## Safety intervention rate', '']
    for name in ('base', 'tuned'):
        blocked = sum(r[f'{name}_safety_action'] != 'supported_verbatim' for r in rows)
        lines.append(f'{name}: {blocked}/20 responses redirected or blocked ({blocked/20:.0%}).')
    inconsistent = [d['id'] for d in details.values()
                    if ' '.join(d['tuned_raw'].replace(DISCLAIMER, '').split()) == ' '.join(d['context'].split())
                    and d['judge']['tuned']['groundedness'] < 1]
    if inconsistent:
        lines += ['## Judge consistency limitation',
                  'The tuned answer exactly reproduces the supplied guidance, yet received groundedness below 1 for: '
                  + ', '.join(inconsistent) + '. These ratings are retained without correction. '
                  'Some rationales penalize brevity or copying rather than unsupported claims. '
                  'Treat the judge score as noisy evidence requiring human adjudication; do not equate it with proven clinical quality.']
    (ROOT / 'reports/evaluation_report.md').write_text('\n'.join(lines) + '\n')
    costs_path = ROOT / 'reports/compute_cost.json'
    cost = json.loads(costs_path.read_text()) if costs_path.exists() else None
    cost_text = (f"Compute cost from provider-reported elapsed duration: USD {cost['compute_usd']:.2f}, based on {cost['billed_seconds']/3600:.2f} observed hours at USD {cost['hourly_rate_usd']:.2f}/hour. "
                 'This is a metered-duration calculation, not a final invoice. Storage, network, judge API charges and the brief shutdown interval are separate.' if cost else
                 'Compute cost is unverified: enter actual billed duration and contracted hourly price with scripts/record_cost.py. No zero-cost assumption is made.')
    estimate_path = ROOT / 'reports/training_cost_estimate.json'
    if cost is None and estimate_path.exists():
        estimate = json.loads(estimate_path.read_text())
        cost_text = (f"Training-only GPU cost is estimated at USD {estimate['estimated_training_gpu_usd']:.4f} "
                     f"({estimate['training_seconds']:.2f} seconds at USD {estimate['gpu_hourly_rate_usd']:.4f}/hour). "
                     'The total bill is unverified; setup, idle time, artifact retrieval, storage, network and judge charges are excluded. '
                     'The USD 10 deposit is a spending limit, not measured cost.')
    charges_path = ROOT / 'reports/provider_charges.json'
    if charges_path.exists():
        charges = json.loads(charges_path.read_text())
        records = charges.get('records', [])
        total = sum(r['amount'] for r in records)
        breakdown = {}
        for record in records:
            for item in record.get('items', []):
                breakdown[item['type']] = breakdown.get(item['type'], 0) + item['amount']
        cost_text = (f"Provider-reported instance charges: USD {total:.3f}, including GPU {breakdown.get('gpu',0):.3f}, "
                     f"storage {breakdown.get('disk',0):.3f}, downloads {breakdown.get('bwd',0):.3f}, "
                     f"and uploads {breakdown.get('bwu',0):.3f}. This is a billing snapshot; retained storage can accrue further charges. "
                     'The GPU instance is confirmed stopped in the provider API.')
    judge_usage = ROOT / 'reports/judge_usage.json'
    if judge_usage.exists():
        usage = json.loads(judge_usage.read_text())
        cost_text += f" The 20-pair review API receipts report USD {usage['reported_cost_usd']:.5f}."
    base, tuned = averages['llm_judge']
    recommendation = 'Proceed only to a supervised operational pilot' if tuned > base and averages['groundedness'][1] >= 0.9 else 'Hold deployment and improve the prototype'
    (ROOT / 'memo.md').write_text(f'''# Stakeholder recommendation

To: AfyaPlus Clinical Director

**Recommendation: {recommendation}.** This assistant covers appointment handling, registration, escalation routing and account access. It cannot make clinical decisions.

Across 20 held-out questions (10 scenarios), average answer quality changed from {base:.2f}/5 to {tuned:.2f}/5: {relative(base,tuned)} relative change. Reference wording overlap changed by {relative(*averages['rouge_l'])}; supported-claim scoring changed by {relative(*averages['groundedness'])}. These percentages describe this small, source-derived, context-supplied benchmark, not patient outcomes. The independent automated reviewer can make mistakes. Some groundedness ratings contradict exact source matches; human adjudication is needed before interpreting the score difference as a real quality change.

{cost_text}

**Next actions:** (1) Have facility workflow owners review and approve the source-derived guidance and answers, because source-derived guidance still needs facility approval. (2) Run a staff-reviewed shadow trial with unseen scenarios and measure blocked answers, because the strict safety filter can reject useful paraphrases and the benchmark is small.

**Risk and mitigation:** Unsupported instructions could misdirect staff. Limit released responses to supplied SOP sentences, redirect clinical requests, keep a human escalation route, and audit the shadow trial before enabling operational use.

{DISCLAIMER}
''')


if __name__ == '__main__':
    generate_report()

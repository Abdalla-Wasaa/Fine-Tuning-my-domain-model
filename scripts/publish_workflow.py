"""Create reserved GitHub issues and a draft PR after token permissions are corrected.

Run from the project root after pushing main and feat/afyaplus-capstone.
Existing issue titles must match; unrelated issues are never overwritten.
"""
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPO = 'Abdalla-Wasaa/Fine-Tuning-my-domain-model'
TITLES = ['data: curate and validate the AfyaPlus operational dataset',
          'feat: implement reproducible Nebius QLoRA training',
          'feat: merge adapters and add safe local inference',
          'feat: evaluate base and tuned models on held-out questions',
          'docs: publish reproducible capstone and stakeholder recommendation']


def main():
    existing = json.loads(subprocess.check_output(['gh', 'api', f'repos/{REPO}/issues?state=all&per_page=100'], text=True))
    by_number = {r['number']: r for r in existing}
    for number, title in enumerate(TITLES, 1):
        if number in by_number:
            if by_number[number]['title'] != title or 'pull_request' in by_number[number]:
                raise SystemExit(f'#{number} already belongs to another item; reconcile references manually')
            continue
        body = next((ROOT / 'docs/issues').glob(f'{number}-*.md'))
        subprocess.run(['gh', 'issue', 'create', '--repo', REPO, '--title', title, '--body-file', str(body)], check=True)
    prs = json.loads(subprocess.check_output(['gh', 'pr', 'list', '--repo', REPO, '--head', 'feat/afyaplus-capstone',
                                             '--state', 'all', '--json', 'url'], text=True))
    if prs:
        print(prs[0]['url'])
    else:
        subprocess.run(['gh', 'pr', 'create', '--repo', REPO, '--base', 'main', '--head', 'feat/afyaplus-capstone',
                        '--draft', '--title', 'feat: implement AfyaPlus domain fine-tuning capstone',
                        '--body-file', str(ROOT / 'docs/pull_request.md')], check=True)


if __name__ == '__main__':
    main()

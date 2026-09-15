"""Check replacement-run prerequisites without allocating or restarting compute."""
import argparse
import json
import os
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from common import ROOT, config, write_json
from provenance import validate_provenance, provider_errors
from runtime_resources import available_memory_bytes


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--provider',choices=['nebius','vast'],default='nebius')
    p.add_argument('--stage',choices=['train','merge'],default='train')
    p.add_argument('--check-model-access',action='store_true')
    p.add_argument('--hf-env',type=Path,help='Optional local dotenv; reads only HF_TOKEN')
    args=p.parse_args()
    problems=validate_provenance(require_human=True)+provider_errors(args.provider)
    result={'stage':args.stage,'provider':args.provider,'source_review_errors':len(problems),
            'available_ram_gib':round(available_memory_bytes()/1024**3,2)}
    if args.stage=='train':
        import torch
        result['cuda_available']=torch.cuda.is_available()
        if not result['cuda_available']: problems.append('Training requires a CUDA GPU')
    if args.stage=='merge' and result['available_ram_gib']<40:
        problems.append('Float32 merge/inference needs at least 40 GiB available RAM; use a 64 GiB CPU machine')
    if args.check_model_access:
        import requests
        key=os.getenv('HF_TOKEN')
        if args.hf_env:
            from dotenv import dotenv_values
            key=dotenv_values(args.hf_env).get('HF_TOKEN')
        cfg=config(); url=f"https://huggingface.co/{cfg['base_model']}/resolve/{cfg['revision']}/config.json"
        try:
            response=requests.get(url,headers={'Authorization':f'Bearer {key}'} if key else {},timeout=20)
            result['model_access_http_status']=response.status_code
            if response.status_code!=200:problems.append(f'Model access failed (HTTP {response.status_code}); obtain approved access to the pinned Meta model')
        except requests.RequestException:
            problems.append('Model access could not be verified due to a network error')
    result['status']='blocked' if problems else 'passed'
    result['errors']=problems
    write_json(ROOT/'reports/preflight_report.json',result)
    print(json.dumps({**result,'errors':problems[:5],'total_errors':len(problems)},indent=2))
    return int(bool(problems))


if __name__=='__main__':raise SystemExit(main())

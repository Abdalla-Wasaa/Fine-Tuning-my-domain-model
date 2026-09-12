"""Merge the adapter into the exact non-quantized base revision used in training."""
import argparse
import json
from pathlib import Path
from common import ROOT, sha256, write_json


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--adapter', type=Path, default=ROOT / 'artifacts/adapter')
    parser.add_argument('--output', type=Path, default=ROOT / 'artifacts/merged')
    args = parser.parse_args()
    manifest = json.loads((args.adapter / 'run_manifest.json').read_text())
    if manifest['status'] != 'completed':
        raise ValueError('Only a successfully completed training run can be merged')
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer
    from peft import PeftModel
    model = AutoModelForCausalLM.from_pretrained(manifest['config']['base_model'],
        revision=manifest['base_revision'], torch_dtype=torch.float32, device_map='cpu')
    model = PeftModel.from_pretrained(model, args.adapter).merge_and_unload(safe_merge=True)
    model.config.use_cache = True
    model.save_pretrained(args.output, safe_serialization=True)
    AutoTokenizer.from_pretrained(args.adapter).save_pretrained(args.output)
    write_json(args.output / 'merge_manifest.json', {'base_model': manifest['config']['base_model'],
        'base_revision': manifest['base_revision'], 'training_manifest_sha256': sha256(args.adapter / 'run_manifest.json'),
        'adapter_sha256': sha256(args.adapter / 'adapter_model.safetensors'),
        'weights': {p.name: sha256(p) for p in args.output.glob('*.safetensors')}})
    print(f'Merged model saved to {args.output}')


if __name__ == '__main__':
    main()

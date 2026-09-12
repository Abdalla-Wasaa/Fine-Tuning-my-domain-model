"""Train QLoRA on a CUDA-equipped Nebius instance; never silently substitute CPU training."""
import argparse
import importlib.metadata
import json
import time
from common import ROOT, config, read_jsonl, sha256, write_json
from training_utils import encode_example, diagnose


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', default=str(ROOT / 'artifacts/adapter'))
    parser.add_argument('--resume', default=None)
    args = parser.parse_args()
    import torch
    if not torch.cuda.is_available():
        raise SystemExit('QLoRA requires a CUDA GPU. Run this script on your Nebius GPU instance.')
    from pathlib import Path
    from huggingface_hub import model_info
    from transformers import (AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig,
                              Trainer, TrainingArguments, DataCollatorForSeq2Seq, set_seed)
    from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
    from data_prep import prepare
    prepare()
    cfg = config()
    set_seed(cfg['seed'])
    revision = model_info(cfg['base_model'], revision=cfg['revision']).sha
    tokenizer = AutoTokenizer.from_pretrained(cfg['base_model'], revision=revision)
    tokenizer.pad_token = tokenizer.eos_token
    tokenizer.padding_side = 'right'
    encoded = {s: [encode_example(r, tokenizer, cfg['max_length']) for r in read_jsonl(ROOT / f'data/{s}.jsonl')]
               for s in ('train', 'val')}
    dtype = torch.bfloat16 if torch.cuda.is_bf16_supported() else torch.float16
    model = AutoModelForCausalLM.from_pretrained(cfg['base_model'], revision=revision,
        quantization_config=BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_quant_type='nf4',
            bnb_4bit_use_double_quant=True, bnb_4bit_compute_dtype=dtype), device_map={'': 0})
    model.config.use_cache = False
    model = prepare_model_for_kbit_training(model)
    model = get_peft_model(model, LoraConfig(r=cfg['lora_r'], lora_alpha=cfg['lora_alpha'],
        lora_dropout=cfg['lora_dropout'], target_modules=cfg['target_modules'], bias='none', task_type='CAUSAL_LM'))
    output = Path(args.output)
    output.mkdir(parents=True, exist_ok=True)
    manifest = {'status': 'started', 'config': cfg, 'base_revision': revision,
                'gpu': torch.cuda.get_device_name(0),
                'packages': {p: importlib.metadata.version(p) for p in ['torch', 'transformers', 'peft', 'bitsandbytes']},
                'data_sha256': {s: sha256(ROOT / f'data/{s}.jsonl') for s in ('train', 'val', 'test')}}
    write_json(output / 'run_manifest.json', manifest)
    trainer = Trainer(model=model, args=TrainingArguments(output_dir=str(output),
        num_train_epochs=cfg['epochs'], learning_rate=cfg['learning_rate'],
        per_device_train_batch_size=cfg['batch_size'], per_device_eval_batch_size=cfg['batch_size'],
        gradient_accumulation_steps=cfg['gradient_accumulation_steps'], weight_decay=cfg['weight_decay'],
        warmup_ratio=cfg['warmup_ratio'], lr_scheduler_type='cosine',
        bf16=dtype == torch.bfloat16, fp16=dtype == torch.float16,
        gradient_checkpointing=True, gradient_checkpointing_kwargs={'use_reentrant': False},
        eval_strategy='epoch', save_strategy='epoch', logging_steps=1, save_total_limit=2,
        load_best_model_at_end=True, metric_for_best_model='eval_loss', greater_is_better=False,
        optim='paged_adamw_8bit', report_to='none', seed=cfg['seed'], data_seed=cfg['seed']),
        train_dataset=encoded['train'], eval_dataset=encoded['val'],
        data_collator=DataCollatorForSeq2Seq(tokenizer=tokenizer, padding=True, label_pad_token_id=-100))
    started = time.monotonic()
    trainer.evaluate()  # Pretraining validation baseline for a meaningful trend.
    trainer.train(resume_from_checkpoint=args.resume)
    trainer.save_model(str(output))
    trainer.save_state()
    tokenizer.save_pretrained(output)
    manifest.update(status='completed', training_seconds=time.monotonic() - started,
                    best_checkpoint=trainer.state.best_model_checkpoint,
                    diagnosis=diagnose(trainer.state.log_history))
    write_json(output / 'run_manifest.json', manifest)
    write_json(ROOT / 'reports/training_run.json', manifest)
    write_json(ROOT / 'reports/trainer_state.json', json.loads((output / 'trainer_state.json').read_text()))
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    for key, label in [('loss', 'Training'), ('eval_loss', 'Validation')]:
        rows = [r for r in trainer.state.log_history if key in r]
        plt.plot([r['step'] for r in rows], [r[key] for r in rows], marker='o', label=label)
    plt.xlabel('Optimizer step'); plt.ylabel('Cross-entropy loss'); plt.legend(); plt.tight_layout()
    plt.savefig(ROOT / 'reports/loss_curve.png'); plt.close()
    print(manifest['diagnosis'])


if __name__ == '__main__':
    main()

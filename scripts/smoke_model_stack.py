"""CPU compatibility smoke test with a tiny RANDOM model; not capstone training evidence."""
import json
from pathlib import Path
import sys
import tempfile
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common import ROOT, config, read_jsonl, write_json
from training_utils import encode_example


def main():
    import torch
    import transformers
    import peft
    from transformers import AutoTokenizer, Qwen2Config, Qwen2ForCausalLM, Trainer, TrainingArguments, DataCollatorForSeq2Seq
    from peft import LoraConfig, get_peft_model, PeftModel
    torch.set_num_threads(2)
    torch.manual_seed(42)
    cfg = config()
    tokenizer = AutoTokenizer.from_pretrained(cfg['base_model'], revision=cfg['revision'])
    tokenizer.pad_token = tokenizer.eos_token
    rows = [r for split in ('train', 'val', 'test') for r in read_jsonl(ROOT / f'data/{split}.jsonl')]
    encoded = [encode_example(r, tokenizer, cfg['max_length']) for r in rows]
    model = Qwen2ForCausalLM(Qwen2Config(vocab_size=len(tokenizer), hidden_size=32, intermediate_size=64,
        num_hidden_layers=1, num_attention_heads=2, num_key_value_heads=1, tie_word_embeddings=True,
        max_position_embeddings=1024, eos_token_id=tokenizer.eos_token_id, pad_token_id=tokenizer.eos_token_id))
    with tempfile.TemporaryDirectory(prefix='afyaplus-smoke-') as directory:
        directory = Path(directory)
        model.save_pretrained(directory / 'base')
        model = get_peft_model(model, LoraConfig(r=4, lora_alpha=8, target_modules=cfg['target_modules'], task_type='CAUSAL_LM'))
        trainer = Trainer(model=model, args=TrainingArguments(output_dir=str(directory / 'adapter'),
            max_steps=2, per_device_train_batch_size=1, per_device_eval_batch_size=1,
            eval_strategy='steps', eval_steps=1, save_strategy='steps', save_steps=1,
            logging_steps=1, report_to='none', label_names=['labels'], use_cpu=True, seed=42),
            train_dataset=encoded[:2], eval_dataset=encoded[2:3],
            data_collator=DataCollatorForSeq2Seq(tokenizer, padding=True, label_pad_token_id=-100))
        trainer.train(); trainer.save_model(); trainer.save_state()
        assert trainer.state.global_step == 2
        base = Qwen2ForCausalLM.from_pretrained(directory / 'base')
        adapted = PeftModel.from_pretrained(base, directory / 'adapter').eval()
        inputs = torch.tensor([encoded[0]['input_ids'][:32]])
        with torch.no_grad():
            before = adapted(input_ids=inputs).logits
            merged = adapted.merge_and_unload(safe_merge=True).eval()
            after = merged(input_ids=inputs).logits
        torch.testing.assert_close(before, after, atol=1e-4, rtol=1e-4)
        merged.save_pretrained(directory / 'merged')
        reloaded = Qwen2ForCausalLM.from_pretrained(directory / 'merged').eval()
        with torch.no_grad():
            generated = reloaded.generate(inputs, attention_mask=torch.ones_like(inputs), max_new_tokens=3, do_sample=False)
        assert generated.shape[1] > inputs.shape[1]
        report = {'status': 'passed', 'scope': 'CPU random tiny Qwen architecture + LoRA only. NOT Nebius QLoRA, domain training, or evaluation evidence.',
                  'tokenizer_model': cfg['base_model'], 'tokenizer_revision': cfg['revision'],
                  'torch': torch.__version__, 'transformers': transformers.__version__, 'peft': peft.__version__,
                  'validated_tokenized_examples': len(encoded), 'max_tokens': max(len(r['input_ids']) for r in encoded),
                  'optimizer_steps': trainer.state.global_step, 'merge_logits_close': True, 'reload_generation': True}
        write_json(ROOT / 'reports/model_stack_smoke.json', report)
        print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()

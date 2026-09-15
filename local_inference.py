"""Local generation with SOP retrieval, input routing and fail-closed output filtering."""
import argparse
import json
import re
from pathlib import Path
from common import ROOT, messages, write_json
from safety import guard, precheck

SAMPLES = ['A patient asks when to attend. What should AfyaPlus staff do?',
           'A complaint reaches reception. What should AfyaPlus staff do?',
           'A patient reports outdated registration details. What should AfyaPlus staff do?',
           'A patient-data system grants broad access by default. What should AfyaPlus staff do?',
           'A patient asks which medicine to take. What should staff do?']


def retrieve(question):
    rules = json.loads((ROOT / 'policies.json').read_text())['rules']
    words = set(re.findall(r'\w+', question.lower())) - {'a', 'the', 'is', 'do', 'how', 'what', 'staff', 'should'}
    scores = [(len(words & set(re.findall(r'\w+', r['scenario'].lower()))), r) for r in rules]
    score, rule = max(scores, key=lambda pair: pair[0])
    return rule['guidance'] if score >= 2 else 'No matching approved operational workflow was found. Contact the responsible facility team.'


class Generator:
    def __init__(self, model_path, revision=None, precision="float32", device="cpu"):
        from runtime_resources import require_llama_memory
        require_llama_memory(precision)
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer
        self.tokenizer = AutoTokenizer.from_pretrained(model_path, revision=revision)
        placement = {'device_map': 'cpu'} if device == 'cpu' else {
            'device_map': 'auto', 'max_memory': {0: '12GiB', 'cpu': '20GiB'}}
        self.model = AutoModelForCausalLM.from_pretrained(model_path, revision=revision,
            torch_dtype=getattr(torch, precision), low_cpu_mem_usage=True, **placement)
        self.model.eval()

    def generate(self, question, context):
        import torch
        prompt = self.tokenizer.apply_chat_template(messages(question, context), tokenize=False, add_generation_prompt=True)
        inputs = self.tokenizer(prompt, return_tensors='pt', add_special_tokens=False).to(self.model.get_input_embeddings().weight.device)
        with torch.inference_mode():
            tokens = self.model.generate(**inputs, max_new_tokens=192, do_sample=False,
                                         pad_token_id=self.tokenizer.eos_token_id)
        return self.tokenizer.decode(tokens[0, inputs['input_ids'].shape[1]:], skip_special_tokens=True).strip()


def ask(generator, question, context=None):
    context = context or retrieve(question)
    checked = precheck(question)
    if checked:
        return {'question': question, 'context': context, 'raw': None, 'response': checked[0], 'safety_action': checked[1]}
    raw = generator.generate(question, context)
    response, action = guard(question, raw, context)
    return {'question': question, 'context': context, 'raw': raw, 'response': response, 'safety_action': action}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--model', default=str(ROOT / 'artifacts/merged'))
    parser.add_argument('--question')
    parser.add_argument('--precision', choices=['float32', 'bfloat16'], default='float32')
    parser.add_argument('--device', choices=['cpu', 'auto'], default='cpu')
    args = parser.parse_args()
    generator = Generator(args.model, precision=args.precision, device=args.device)
    results = [ask(generator, q) for q in ([args.question] if args.question else SAMPLES)]
    write_json(ROOT / 'reports/sample_responses.json', results)
    for row in results:
        print(f"Q: {row['question']}\nA: {row['response']}\n")


if __name__ == '__main__':
    main()

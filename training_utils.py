"""Completion-only tokenization and validation-loss diagnosis."""

def encode_example(row, tokenizer, max_length):
    prompt = tokenizer.apply_chat_template(row['messages'][:2], tokenize=True, add_generation_prompt=True)
    full = tokenizer.apply_chat_template(row['messages'], tokenize=True, add_generation_prompt=False)
    if full[:len(prompt)] != prompt:
        raise ValueError('Chat template prompt is not a prefix; assistant masking would be invalid')
    if len(full) > max_length:
        raise ValueError(f"{row['id']} exceeds max_length; refusing silent truncation")
    if len(full) <= len(prompt):
        raise ValueError('No assistant tokens to train')
    return {'input_ids': full, 'attention_mask': [1] * len(full),
            'labels': [-100] * len(prompt) + full[len(prompt):]}


def diagnose(history):
    vals = [r['eval_loss'] for r in history if 'eval_loss' in r]
    losses = [r['loss'] for r in history if 'loss' in r]
    if len(vals) < 2 or len(losses) < 2:
        return 'Insufficient evidence: at least two training and validation loss observations required.'
    if vals[-1] > min(vals[:-1]) * 1.05 and losses[-1] < losses[0]:
        return 'Possible overfit: validation loss rose >5% above its earlier minimum while training loss fell.'
    if vals[-1] >= vals[0] * 0.98:
        return 'Possible underfit or optimization issue: validation loss improved less than 2%; inspect outputs.'
    return 'Healthy loss trend: validation loss improved by at least 2% without the overfit trigger; this does not prove operational safety.'

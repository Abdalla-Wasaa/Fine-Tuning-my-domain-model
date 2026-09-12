# Stakeholder recommendation

**Recommendation: hold deployment until the training and comparison are verified.** The prototype addresses appointment workflows, registration, escalation routing, and system access. It does not make clinical decisions.

The curated teaching dataset contains 200 examples, with 160 for training, 20 for validation, and 20 for testing. Automated preparation currently reports zero validation errors. The test questions represent ten independent scenarios, so the eventual results will describe a small educational benchmark.

**Quality improvement:** not yet measured. There is no completed Vast.ai training run or paired model evaluation in this submission state. Percentage improvements cannot responsibly be supplied before those runs. The evaluation script will replace this memo with measured relative changes and clearly identify a zero baseline when percentages are undefined.

**Compute cost:** not yet verified. No instance was started by this implementation. Record the actual billed instance duration and contracted hourly rate; training duration alone excludes setup and idle time. Storage and reviewer API charges must be tracked separately.

**Next actions:** (1) Supply a dedicated Vast.ai instance and a spending limit, run training with durable artifact upload and verified provider shutdown, then compare both models on the fixed test set. This establishes actual benefit and cost. (2) Ask facility workflow owners to approve the synthetic teaching SOP and review a supervised shadow trial. This addresses the gap between classroom assumptions and real operations.

**Risk and mitigation:** unsupported guidance could misdirect staff. The prototype releases only sentences found in its supplied SOP, redirects clinical requests, and otherwise asks users to contact the responsible team. This conservative control may block useful paraphrases; measure that rate before operational use.

This model provides non-diagnostic operational guidance only.

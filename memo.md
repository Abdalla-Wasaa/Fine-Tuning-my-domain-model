# Stakeholder recommendation

**Recommendation: Proceed only to a supervised operational pilot.** This assistant covers appointment handling, registration, escalation routing and account access. It cannot make clinical decisions.

Across 20 held-out questions (10 scenarios), average answer quality changed from 2.15/5 to 5.00/5: +132.6% relative change. Reference wording overlap changed by +582.6%; supported-claim scoring changed by +194.1%. These percentages describe this small, synthetic, context-supplied benchmark, not patient outcomes. The independent automated reviewer can make mistakes.

Training-only GPU cost is estimated at USD 0.0049 (95.04 seconds at USD 0.1867/hour). The total bill is unverified; setup, idle time, artifact retrieval, storage, network and judge charges are excluded. The USD 10 deposit is a spending limit, not measured cost.

**Next actions:** (1) Have facility workflow owners review and approve the teaching SOP and answers, because the current policy is synthetic. (2) Run a staff-reviewed shadow trial with unseen scenarios and measure blocked answers, because the strict safety filter can reject useful paraphrases and the benchmark is small.

**Risk and mitigation:** Unsupported instructions could misdirect staff. Limit released responses to supplied SOP sentences, redirect clinical requests, keep a human escalation route, and audit the shadow trial before enabling operational use.

This model provides non-diagnostic operational guidance only.

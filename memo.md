# Stakeholder recommendation

To: AfyaPlus Clinical Director

**Recommendation: Hold deployment and improve the prototype.** This assistant covers appointment handling, registration, escalation routing and account access. It cannot make clinical decisions.

Across 20 held-out questions (10 scenarios), average answer quality changed from 4.55/5 to 3.85/5: -15.4% relative change. Reference wording overlap changed by +207.0%; supported-claim scoring changed by -20.9%. These percentages describe this small, source-derived, context-supplied benchmark, not patient outcomes. The independent automated reviewer can make mistakes. Some groundedness ratings contradict exact source matches; human adjudication is needed before interpreting the score difference as a real quality change.

Provider-reported instance charges: USD 2.884, including GPU 1.232, storage 0.222, downloads 0.790, and uploads 0.640. This is a billing snapshot; retained storage can accrue further charges. The GPU instance is confirmed stopped in the provider API. The 20-pair review API receipts report USD 0.00204.

**Next actions:** (1) Have facility workflow owners review and approve the source-derived guidance and answers, because source-derived guidance still needs facility approval. (2) Run a staff-reviewed shadow trial with unseen scenarios and measure blocked answers, because the strict safety filter can reject useful paraphrases and the benchmark is small.

**Risk and mitigation:** Unsupported instructions could misdirect staff. Limit released responses to supplied SOP sentences, redirect clinical requests, keep a human escalation route, and audit the shadow trial before enabling operational use.

This model provides non-diagnostic operational guidance only.

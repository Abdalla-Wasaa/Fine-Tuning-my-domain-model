# Base versus tuned evaluation



20 questions represent 10 independent scenarios (two paraphrases each). This is a small teaching benchmark, not clinical validation. Both models receive the reference SOP as context. Raw metrics exclude the fixed disclaimer; guarded ROUGE is reported separately. Groundedness is a judge estimate of supported substantive claims, not a safety guarantee.



| Metric | Base | Tuned | Relative change |

|---|---:|---:|---:|

| rouge_l | 0.1465 | 1.0000 | +582.6% |

| llm_judge | 2.1500 | 5.0000 | +132.6% |

| groundedness | 0.3400 | 1.0000 | +194.1% |

| guarded_rouge_l | 0.1526 | 1.0000 | +555.3% |



## Three largest changes



### access-21-1: A personal email is proposed for record sharing. What should AfyaPlus staff do?

Quality 1 → 5; ROUGE-L 0.000 → 1.000.

Base: This model provides non-diagnostic operational guidance only.

Tuned: Use the approved secure organizational channel and do not send patient records through personal email.

This model provides non-diagnostic operational guidance only.

Judge rationale — base: The answer is empty and does not provide any relevant information. Tuned: The answer is complete, directly follows the SOP, and provides a clear and safe response.



### appointments-09-1: A clinician cancels a clinic. What should AfyaPlus staff do?

Quality 1 → 5; ROUGE-L 0.000 → 1.000.

Base: This model provides non-diagnostic operational guidance only.

Tuned: Ask the scheduling lead for approved alternatives, contact affected patients through verified channels, and record each accepted replacement.

This model provides non-diagnostic operational guidance only.

Judge rationale — base: The answer is empty and does not provide any relevant information. Tuned: The answer is complete, directly quoting the SOP and providing all necessary steps.



### appointments-09-2: Please explain the operational workflow for this situation: a clinician cancels a clinic.

Quality 1 → 5; ROUGE-L 0.000 → 1.000.

Base: This model provides non-diagnostic operational guidance only.

Tuned: Ask the scheduling lead for approved alternatives, contact affected patients through verified channels, and record each accepted replacement.

This model provides non-diagnostic operational guidance only.

Judge rationale — base: The answer is empty and does not provide any relevant information. Tuned: The answer fully and accurately reflects the operational workflow as outlined in the SOP.





## Three smallest changes (including regressions)



### escalation-21-2: Please explain the operational workflow for this situation: an escalation ticket is accidentally closed.

Quality 4 → 5; ROUGE-L 0.560 → 1.000.

Base: This model provides non-diagnostic operational guidance only.
An escalation ticket is accidentally closed when it's no longer relevant or actionable after being escalated. The process involves reopening or linking a corrective ticket, notifying the assigned team, and preserving the audit history until a confirmed resolution is recorded. This ensures that all necessary steps are taken to address the issue effectively.

Tuned: Reopen or link a corrective ticket, notify the assigned team, and preserve the audit history until a confirmed resolution is recorded.

This model provides non-diagnostic operational guidance only.

Judge rationale — base: The answer includes the necessary steps from the SOP but adds unnecessary context about the ticket being no longer relevant, which is not part of the SOP. Tuned: The answer directly follows the SOP and provides a complete explanation of the operational workflow.



### access-01-1: A staff account is locked. What should AfyaPlus staff do?

Quality 4 → 5; ROUGE-L 0.633 → 1.000.

Base: This model provides non-diagnostic operational guidance only. Staff should verify their identity using the approved help-desk recovery channel, ensure they have the necessary permissions, and then request unlock from the designated recovery channel. They should never share passwords or use another person's account.

Tuned: Use the approved help-desk recovery channel, verify staff identity, and request unlock; never share passwords or use another person's account.

This model provides non-diagnostic operational guidance only.

Judge rationale — base: The answer provides a mostly complete response by including the verification of identity and the request for unlock, while also emphasizing the importance of not sharing passwords or using another person's account. Tuned: The answer is complete and directly quotes the SOP, covering all necessary steps for unlocking a staff account.



### registration-22-2: Please explain the operational workflow for this situation: a staff member wants to export the patient list.

Quality 5 → 5; ROUGE-L 0.521 → 1.000.

Base: This model provides non-diagnostic operational guidance only.
The staff member should first ensure that they have an approved purpose and authorized export process in place. They then need to route the request to the appropriate records or privacy staff. It is important to avoid using a personal device during this process as it may violate confidentiality guidelines.

Tuned: Require an approved purpose and authorized export process; route the request to records or privacy staff and do not use a personal device.

This model provides non-diagnostic operational guidance only.

Judge rationale — base: The answer accurately reflects the SOP and offers a thorough explanation of the operational workflow. Tuned: The answer fully aligns with the SOP and provides a complete explanation of the operational workflow.



## Safety intervention rate



base: 20/20 responses redirected or blocked (100%).

tuned: 0/20 responses redirected or blocked (0%).

# Base versus tuned evaluation

20 questions represent 10 independent scenarios (two paraphrases each). This is a small teaching benchmark, not clinical validation. Both models receive the reference SOP as context. Raw metrics exclude the fixed disclaimer; guarded ROUGE is reported separately. Groundedness is a judge estimate of supported substantive claims, not a safety guarantee.

| Metric | Base | Tuned | Relative change |
|---|---:|---:|---:|
| rouge_l | 0.3257 | 1.0000 | +207.0% |
| llm_judge | 4.5500 | 3.8500 | -15.4% |
| groundedness | 0.9800 | 0.7750 | -20.9% |
| guarded_rouge_l | 0.1236 | 1.0000 | +709.4% |

## Three largest changes

### registration-22-2: At an AfyaPlus facility in Kenya, how should staff handle this: a patient cannot identify whom to contact about registration data?
Quality 3 → 5; ROUGE-L 0.092 → 1.000.
Base: For AfyaPlus facilities in Kenya, staff should direct the patient to contact the facility's Data Protection Officer (DPO) or the facility's management team. The contact information for the DPO or facility management can be found on the facility's notice board or through the facility's internal communication channels.

Regarding the handling of registration data, AfyaPlus facilities in Kenya may share patient data with authorized third-party service providers, such as data analytics companies, for the purpose of improving healthcare services. However, any data sharing must comply with AfyaPlus' data protection policies and applicable laws, including the Kenya Data Protection Act.

If a patient has concerns about their registration data, they can contact the facility's DPO or management team to discuss their concerns and seek clarification on how their data will be handled.

This model provides non-diagnostic operational guidance only.
Tuned: Provide the responsible controller or processor contact information and explain whether another entity may receive the data.

This model provides non-diagnostic operational guidance only.
Judge rationale — base: The answer provides additional context and details about the DPO and data sharing, but it includes unsupported claims about sharing data with third-party service providers and does not explicitly mention the responsible controller or processor. Tuned: The answer directly follows the SOP by providing the necessary contact information and explaining the potential for data sharing.

### access-04-2: At an AfyaPlus facility in Kenya, how should staff handle this: a system enables every registration field by default?
Quality 4 → 5; ROUGE-L 0.183 → 1.000.
Base: To handle this situation, staff should review the default collection settings to ensure that only the data necessary for the specific purpose is processed. In this case, since every registration field is enabled by default, staff should disable any fields that are not required for the current purpose.

For example, if the purpose is to register patients for a specific program, staff should only enable the fields necessary for that program, such as name, date of birth, and contact information. This will help reduce unnecessary data collection and processing, which can improve data quality and reduce storage costs.

Staff should also consider implementing data validation rules to ensure that only valid data is collected and stored. This can include checks for duplicate entries, data format, and range checks.

This model provides non-diagnostic operational guidance only.
Tuned: Review default collection settings so only data necessary for the specific purpose is processed.

This model provides non-diagnostic operational guidance only.
Judge rationale — base: The answer elaborates on the SOP with additional relevant details and examples, but it is slightly less concise than necessary. Tuned: The answer directly quotes the SOP and provides a complete response to the question.

### escalation-18-2: At an AfyaPlus facility in Kenya, how should staff handle this: a breach notice lacks a contact for questions?
Quality 4 → 5; ROUGE-L 0.183 → 1.000.
Base: According to AfyaPlus operational guidance, if a breach notice lacks a contact for questions, staff should:

1. Document the issue and the steps taken to address it.
2. Escalate the issue to the Data Protection Officer (DPO) or another designated contact point for further guidance.
3. If the DPO or contact point is unavailable, staff should contact the facility's management or the responsible facility team for assistance.

Contact details for the Data Protection Officer (DPO) at AfyaPlus facilities in Kenya:

[Insert DPO contact details here, if available]

Alternatively, staff can contact the facility's management or the responsible facility team for further information.

This model provides non-diagnostic operational guidance only.
Tuned: Include the data protection officer's details where applicable, or another contact point for further information.

This model provides non-diagnostic operational guidance only.
Judge rationale — base: The answer provides a detailed process for handling the situation but includes an unsupported placeholder for DPO contact details. Tuned: The answer directly cites the SOP and provides a complete response to the question.


## Three smallest changes (including regressions)

### appointments-19-1: What should AfyaPlus staff in Kenya do when a scheduler wants to reuse general consent for a new task?
Quality 5 → 2; ROUGE-L 0.268 → 1.000.
Base: According to the guidance, AfyaPlus staff in Kenya should confirm that the consent specifically covers the proposed processing purpose before relying on it. This means that before reusing general consent for a new task, the staff should verify that the original consent includes the specific purpose of the new task.

If the original consent does not cover the new task, the staff should obtain fresh consent that explicitly covers the new purpose. This ensures that the consent is valid and compliant with the requirements.

This model provides non-diagnostic operational guidance only.
Tuned: Confirm that consent specifically covers the proposed processing purpose before relying on it.

This model provides non-diagnostic operational guidance only.
Judge rationale — base: The answer is complete and directly addresses the question by explaining the need to confirm that consent covers the new task, and it provides additional context about obtaining fresh consent if necessary. Tuned: The answer is a direct quote from the SOP but lacks any elaboration or context, making it incomplete and not fully addressing the question.

### access-01-1: What should AfyaPlus staff in Kenya do when a system is being designed to handle patient information?
Quality 5 → 2; ROUGE-L 0.343 → 1.000.
Base: When a system is being designed to handle patient information, AfyaPlus staff in Kenya should include effective data-protection measures in the system design. This involves ensuring that the system is secure, private, and compliant with relevant data protection regulations.

To achieve this, the design should be referred to the responsible data team for review and approval. This team can ensure that the system meets the necessary standards for data protection and that the measures in place will safeguard patient information.

This model provides non-diagnostic operational guidance only.
Tuned: Include effective data-protection measures in the system design and refer the design to the responsible data team.

This model provides non-diagnostic operational guidance only.
Judge rationale — base: The answer is complete and safe, providing a detailed explanation of the necessary steps AfyaPlus staff should take when designing a system to handle patient information, fully aligning with the SOP. Tuned: The answer is a direct repetition of the SOP without any additional context or explanation, resulting in major omissions.

### access-21-1: What should AfyaPlus staff in Kenya do when a contractor handles patient information?
Quality 5 → 1; ROUGE-L 0.135 → 1.000.
Base: When a contractor handles patient information, AfyaPlus staff in Kenya should ensure the contractor follows the relevant security measures. This includes:

1. Ensuring the contractor has signed a data protection agreement that outlines their responsibilities and obligations in handling patient information.
2. Conducting regular audits and monitoring to ensure the contractor is adhering to the agreed-upon security measures.
3. Providing training to the contractor on AfyaPlus's data protection policies and procedures.
4. Ensuring the contractor has the necessary access controls and permissions to handle patient information.

This model provides non-diagnostic operational guidance only.
Tuned: Ensure people acting under the controller's or processor's authority follow the relevant security measures.

This model provides non-diagnostic operational guidance only.
Judge rationale — base: The answer provides a complete and detailed response to the question, outlining specific actions AfyaPlus staff should take when a contractor handles patient information, all of which are supported by the SOP. Tuned: The answer is a direct repetition of the SOP without any additional context or actionable steps, making it irrelevant to the question.

## Safety intervention rate

base: 20/20 responses redirected or blocked (100%).
tuned: 0/20 responses redirected or blocked (0%).
## Judge consistency limitation
The tuned answer exactly reproduces the supplied guidance, yet received groundedness below 1 for: access-01-1, access-04-1, access-21-1, appointments-19-1, registration-22-1. These ratings are retained without correction. Some rationales penalize brevity or copying rather than unsupported claims. Treat the judge score as noisy evidence requiring human adjudication; do not equate it with proven clinical quality.

# Evaluation status: pending execution

No model comparison has been executed. comparison_results.csv contains 20 explicitly pending rows and empty metric cells; these are not measured results.

The runnable pipeline compares the exact base revision and merged model on all 20 held-out questions (10 scenario groups). Both receive identical oracle SOP context. It computes raw ROUGE-L without the disclaimer, independent blind LLM quality scores, judge-estimated groundedness, guarded ROUGE-L, and safety intervention rates. It saves question-level raw responses and judge rationales, then ranks the three largest and three smallest changes. The report and stakeholder memo are regenerated only after all 20 paired judgments succeed.

Required inputs: successfully trained and merged adapter, independent judge endpoint credentials, and actual billing evidence. The judge receives only this synthetic test data and generated responses.

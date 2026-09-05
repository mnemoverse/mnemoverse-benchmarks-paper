# Third judge backbone: Claude

The two headline prompts re-scored on `claude-sonnet-4-5` (a non-OpenAI backbone), same 1,539 answers. Verdicts `experiments/hardening/verdicts/XB_conv*.json`; runner `scripts/run_extra_judges.py`.

- Prompt effect on Claude (lenient - strict): **+29.2 pp** (n=1539); lenient 91.9%, strict 62.8%.
- Model effect, lenient prompt (gpt-5 - Claude): **-0.9 pp** (n=1539).
- Model effect, strict prompt (gpt-5 - Claude): **-27.8 pp** (n=1539).

Read against the gpt-5/gpt-4o decomposition: the prompt axis remains an order of magnitude larger than the model axis even against a distant backbone if the prompt effect here is tens of points and the model effects are single digits.

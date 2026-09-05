# Full-set model-vs-prompt decomposition (all 10 conversations, Mem0 published answers)

Provenance: gpt-5 verdicts = committed `experiments/hardening/verdicts/B_conv*_{mem0,strict}.json`; gpt-4o verdicts = `MV_conv*_{mem0-4o,strict-4o}.json` produced by this script (`scripts/run_model_vs_prompt_fullset.py`); effects computed on jointly-scored answers per comparison. Sign convention: model effect = gpt-5 minus gpt-4o (negative = gpt-4o more generous). The 2x2 identity (prompt-effect difference == model-effect difference) is asserted at build time.

| conv | prompt effect (gpt-5) | prompt effect (gpt-4o) | model effect (mem0 prompt) | model effect (strict prompt) |
|------|----------------------|------------------------|----------------------------|------------------------------|
| conv0 | +61.2 (n=152) | +52.0 (n=152) | -1.3 (n=152) | -10.5 (n=152) |
| conv1 | +58.0 (n=81) | +50.6 (n=81) | +0.0 (n=81) | -7.4 (n=81) |
| conv2 | +60.5 (n=152) | +51.3 (n=152) | -1.3 (n=152) | -10.5 (n=152) |
| conv3 | +55.1 (n=198) | +48.0 (n=198) | -2.0 (n=198) | -9.1 (n=198) |
| conv4 | +52.8 (n=178) | +45.5 (n=178) | -1.7 (n=178) | -9.0 (n=178) |
| conv5 | +53.7 (n=123) | +48.0 (n=123) | -1.6 (n=123) | -7.3 (n=123) |
| conv6 | +48.0 (n=150) | +44.7 (n=150) | -1.3 (n=150) | -4.7 (n=150) |
| conv7 | +57.1 (n=191) | +51.3 (n=191) | -0.5 (n=191) | -6.3 (n=191) |
| conv8 | +54.5 (n=156) | +44.9 (n=156) | +1.9 (n=156) | -7.7 (n=156) |
| conv9 | +60.8 (n=158) | +52.5 (n=158) | -0.6 (n=158) | -8.9 (n=158) |
| **all** | **+56.1** (n=1539) | **+48.8** (n=1539) | **-0.9** (n=1539) | **-8.2** (n=1539) |

Ratio of mean |prompt effect| to mean |model effect| (overall): 52.4 / 4.5 = 11.5x

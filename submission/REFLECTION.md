# Reflection - Day 22 Track 3 DPO/ORPO Alignment Lab

## Setup

This lab was completed on the Track 3 path with a real local model run, not with scaffold artifacts.

- Compute tier: `BIGGPU`
- Actual local base model used: `D:\tmp\Qwen2.5-3B-Instruct`
- Remote download: disabled
- Mock artifacts: disabled
- OS/runtime: Windows + local `.venv`
- Quantization path: 4-bit QLoRA-style loading when available

The original goal was to run local Qwen2.5-7B, but the machine only had an RTX 3050 Ti Laptop GPU with 4GB VRAM. In practice, 7B was not feasible in this pipeline, so the run was moved to local Qwen2.5-3B while keeping the rest of the Track 3 workflow real.

## What DPO Does

Direct Preference Optimization uses pairwise preference data with `prompt`, `chosen`, and `rejected` responses. Instead of a full RLHF stack, it directly nudges the policy toward outputs that score closer to the preferred response while staying anchored to the SFT starting point.

In this lab, the workflow was:

1. Train a small SFT LoRA adapter.
2. Generate preference pairs from base vs SFT behavior.
3. Train a DPO adapter on those pairs.
4. Compare SFT-only vs SFT+DPO on fixed prompts.

## Actual Pipeline Run

The real run order was:

1. `python scripts/smoke.py`
2. `python scripts/train_sft.py`
3. `python scripts/build_pref_data.py`
4. `python scripts/train_dpo.py`
5. `python scripts/eval_compare.py`
6. `python scripts/verify_lab.py`

Verification passed with real artifacts:

- `adapters/sft-mini/`
- `data/pref/train.parquet`
- `adapters/dpo/`
- `submission/screenshots/01_sft_loss.png`
- `submission/screenshots/03_dpo_reward_curves.png`
- `submission/screenshots/04_side_by_side_table.png`
- `reports/verify_report.json` with `status: pass`

## SFT Observations

The SFT mini run completed successfully on 16 examples and produced a real LoRA adapter.

- Dataset size: `16`
- Final reported training loss: `5.350604057312012`
- Artifact mode: `real`

Because the run had to be made very small to fit the hardware, the loss plot only contains one effective training point. That is still honest for this run, but it also means the SFT checkpoint is weak and should be interpreted as a tiny lab-scale adapter, not a production-tuned checkpoint.

## Preference Data

The preference dataset was built from real generations and saved to `data/pref/train.parquet`.

- Row count: `12`
- Columns: `prompt`, `chosen`, `rejected`
- Source mix: `6` chosen from SFT and `6` chosen from base

I also inspected sample pairs in `reports/pref_examples.md`. The data was usable for a lab run, but some responses were still noisy and not perfectly clean. That likely hurt downstream DPO quality.

## DPO Training Analysis

The DPO run completed successfully and produced a real LoRA adapter.

- Artifact mode: `real`
- Chosen reward: `0.001041412353515625`
- Rejected reward: `0.00208282470703125`
- Reward gap: `-0.001041412353515625`

The reward gap was negative in this run, which means the preferred responses were not consistently scoring above the rejected responses. I do not think that means the pipeline is broken. The more likely explanation is that the run was extremely small:

- only `12` preference pairs
- only `1` effective DPO step
- very constrained VRAM
- short outputs and aggressive low-memory settings
- noisy preference pairs from a weak mini-SFT model

So the DPO adapter is real, but its quality is limited by dataset size and hardware constraints.

## SFT vs DPO Comparison

The fixed-prompt comparison ran on `8` prompts and produced a real evaluation table and screenshot.

- DPO wins: `0`
- SFT wins: `8`
- Ties: `0`

This result is not what I would want from a strong alignment run, but it is an honest outcome. In this specific local run, the DPO checkpoint underperformed the SFT checkpoint on the score heuristic used in the lab scripts.

I think the main reasons are:

- the SFT model was already somewhat more verbose and structured
- the preference dataset was very small
- the DPO run had only a minimal optimization budget
- low-memory inference forced shorter outputs during evaluation

## Errors and Fixes

Several issues came up while turning the repo from scaffold mode into a real local Track 3 pipeline:

- Missing packages at first, such as `datasets`
- Windows install issues around `flash-attn`
- Initial CPU-only Torch environment before CUDA-enabled Torch was active
- 7B model infeasible on 4GB VRAM
- TRL API mismatches for `SFTTrainer` and `DPOTrainer`
- BFloat16-related runtime errors during SFT
- Multi-model memory pressure when building preference data
- Very slow or stuck-looking eval runs during DPO comparison

The fixes were:

- use the real `.venv` with CUDA-enabled Torch
- keep `ALLOW_MOCK_ARTIFACTS=0`
- fail clearly instead of silently generating placeholder artifacts
- switch from local 7B intent to local 3B reality because of VRAM limits
- add compatibility handling for the installed TRL version
- force a safer float16-oriented path for this GPU
- split preference generation into isolated subprocesses
- add resumable eval caching and reduce eval token count in low-memory mode

## Reflection

This lab ended up being as much about systems debugging as model alignment. The main lesson for me is that a correct pipeline on paper is not enough; the runtime behavior has to match the actual hardware budget. The most important improvement was making the repo honest: real mode now fails clearly when the local model path is invalid, and mock artifacts are only possible behind an explicit flag.

Another lesson is that small, real runs can still be valuable even when the quality is poor. In this case, the DPO result was worse than SFT and the reward gap was negative, but that is still useful evidence. It shows that preference optimization is sensitive to data quality, compute budget, and evaluation setup. I would trust this run as a truthful lab submission more than a prettier run produced by placeholders.

If I had more compute, the next improvements would be:

- rerun on Qwen2.5-7B or at least a GPU with much more VRAM
- expand the SFT seed set
- build cleaner preference pairs
- run more than one effective DPO step
- use a stronger evaluation rubric than the current lightweight heuristic

## Fallback Disclosure

No mock artifacts were used in the final verified run.

The only fallback was model scale: the original local 7B target was not feasible on 4GB VRAM, so the real submission run used local `Qwen2.5-3B-Instruct` instead. All generated artifacts in the final verified path were still produced by real local execution.

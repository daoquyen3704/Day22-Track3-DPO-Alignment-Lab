# Day 22 Track 3 Rubric

## Required pipeline stages

1. `make smoke`
2. `make sft`
3. `make data`
4. `make dpo`
5. `make eval`
6. `make verify`

## Required outputs

### NB1 - SFT mini

- `adapters/sft-mini/`
- `submission/screenshots/01_sft_loss.png`

### NB2 - Preference data

- `data/pref/train.parquet`
- columns: `prompt`, `chosen`, `rejected`
- at least 3 inspected examples saved or printed by the pipeline

### NB3 - DPO training

- `adapters/dpo/`
- `submission/screenshots/03_dpo_reward_curves.png`
- reward-gap analysis or explanation if chosen reward drops

### NB4 - Compare and eval

- side-by-side table for SFT-only vs SFT+DPO
- at least 8 fixed prompts
- stats for `win`, `loss`, `tie`
- `submission/screenshots/04_side_by_side_table.png`

### Reflection

- `submission/REFLECTION.md`
- setup details
- DPO explanation
- reward curve analysis
- SFT vs DPO comparison
- failure notes and mitigations
- personal reflection

### Verify

- `make verify` passes, or
- verification report clearly explains what failed, why, and how to fix it

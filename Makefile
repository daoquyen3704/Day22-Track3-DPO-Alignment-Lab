PYTHON ?= python

.PHONY: smoke sft data dpo eval verify deploy bench pipeline pipeline-full

smoke:
	$(PYTHON) scripts/smoke.py

sft:
	$(PYTHON) scripts/train_sft.py

data:
	$(PYTHON) scripts/build_pref_data.py

dpo:
	$(PYTHON) scripts/train_dpo.py

eval:
	$(PYTHON) scripts/eval_compare.py

verify:
	$(PYTHON) scripts/verify_lab.py

deploy:
	$(PYTHON) scripts/merge_gguf.py

bench:
	$(PYTHON) scripts/benchmark.py

pipeline:
	$(PYTHON) scripts/smoke.py
	$(PYTHON) scripts/train_sft.py
	$(PYTHON) scripts/build_pref_data.py
	$(PYTHON) scripts/train_dpo.py
	$(PYTHON) scripts/eval_compare.py
	$(PYTHON) scripts/verify_lab.py

pipeline-full:
	$(PYTHON) scripts/smoke.py
	$(PYTHON) scripts/train_sft.py
	$(PYTHON) scripts/build_pref_data.py
	$(PYTHON) scripts/train_dpo.py
	$(PYTHON) scripts/eval_compare.py
	$(PYTHON) scripts/verify_lab.py
	$(PYTHON) scripts/merge_gguf.py
	$(PYTHON) scripts/benchmark.py

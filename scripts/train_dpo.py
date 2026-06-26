from __future__ import annotations

from pathlib import Path
import json
import inspect

import pandas as pd

from common import (
    PROJECT_ROOT,
    artifact_mode,
    ensure_directories,
    ensure_runtime_policy,
    gpu_vram_gb,
    infer_model_scale_label,
    is_real_adapter_dir,
    load_runtime_config,
    resolve_model_source,
    save_json,
    save_text,
    seed_everything,
    setup_logging,
)
from plotting import plot_two_lines
from transformers import TrainerCallback


class StepLoggerCallback(TrainerCallback):
    def __init__(self, logger, output_path: Path) -> None:
        self.logger = logger
        self.output_path = output_path
        self.output_path.parent.mkdir(parents=True, exist_ok=True)

    def on_log(self, args, state, control, logs=None, **kwargs):
        if not logs:
            return control
        payload = {
            "step": int(state.global_step),
            "epoch": float(state.epoch) if state.epoch is not None else None,
            **{key: value for key, value in logs.items() if isinstance(value, (int, float))},
        }
        with self.output_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload, ensure_ascii=True) + "\n")
        summary = ", ".join(f"{k}={v}" for k, v in payload.items() if v is not None)
        self.logger.info("DPO progress: %s", summary)
        return control


def _mock_run(config: dict, reason: str) -> None:
    output_dir = PROJECT_ROOT / config["dpo"]["output_dir"]
    output_dir.mkdir(parents=True, exist_ok=True)
    chosen_rewards = [0.12, 0.18, 0.22, 0.29, 0.33, 0.38]
    rejected_rewards = [-0.08, -0.1, -0.14, -0.17, -0.2, -0.23]
    plot_two_lines(chosen_rewards, rejected_rewards, ("chosen_reward", "rejected_reward"), "DPO Reward Curves", "Reward", config["dpo"]["plot_path"])
    save_text(output_dir / "README.txt", f"MOCK artifact. Reason: {reason}\n")
    save_json(config["dpo"]["report_path"], {"status": "mock", "artifact_mode": "mock", "reason": reason})


def main() -> None:
    logger = setup_logging("train_dpo")
    config = load_runtime_config()
    seed_everything(config["seed"])
    resolution = resolve_model_source(config)
    ensure_directories(["adapters/dpo", "reports", "submission/screenshots"])

    if config["allow_mock_artifacts"]:
        _mock_run(config, "ALLOW_MOCK_ARTIFACTS=1")
        logger.warning("Created mock DPO artifacts because ALLOW_MOCK_ARTIFACTS=1")
        return

    pref_path = PROJECT_ROOT / config["pref"]["output_path"]
    sft_adapter_path = PROJECT_ROOT / config["sft"]["output_dir"]

    try:
        ensure_runtime_policy(config, resolution)
        detected_vram = gpu_vram_gb()
        model_scale = infer_model_scale_label(resolution.source)
        logger.info("Detected GPU VRAM: %.2f GB", detected_vram)
        logger.info("Detected model scale label: %s", model_scale)
        if model_scale == "7b" and detected_vram and detected_vram < 6.0:
            raise RuntimeError(
                f"Detected only {detected_vram:.2f} GB VRAM. Qwen2.5-7B DPO training is not feasible on this GPU "
                "in the current pipeline. Use a >=8-12GB GPU, switch to a 3B model, or run on a bigger machine."
            )
        if model_scale == "3b" and detected_vram and detected_vram < 4.0:
            logger.warning(
                "Detected only %.2f GB VRAM. Qwen2.5-3B DPO may still OOM, but the pipeline will attempt a minimal run.",
                detected_vram,
            )
        if not pref_path.exists():
            raise RuntimeError(f"Missing preference dataset: {pref_path}")
        if not is_real_adapter_dir(sft_adapter_path):
            raise RuntimeError(f"SFT adapter is not real or is incomplete: {sft_adapter_path}")

        import torch
        from datasets import Dataset
        from peft import PeftModel
        from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig, TrainingArguments
        from trl import DPOTrainer

        frame = pd.read_parquet(pref_path)
        dataset = Dataset.from_pandas(frame)
        tokenizer = AutoTokenizer.from_pretrained(resolution.source, trust_remote_code=True, local_files_only=True)
        if tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token

        quantization_config = None
        if config["sft"]["use_4bit"] and torch.cuda.is_available():
            try:
                quantization_config = BitsAndBytesConfig(
                    load_in_4bit=True,
                    bnb_4bit_use_double_quant=True,
                    bnb_4bit_quant_type="nf4",
                    bnb_4bit_compute_dtype=torch.float16,
                )
            except Exception as exc:
                logger.warning("4-bit setup failed for DPO, retrying without quantization: %s", exc)

        model = AutoModelForCausalLM.from_pretrained(
            resolution.source,
            trust_remote_code=True,
            local_files_only=True,
            torch_dtype=torch.float16 if torch.cuda.is_available() else None,
            quantization_config=quantization_config,
            device_map="auto" if torch.cuda.is_available() else None,
        )
        model = PeftModel.from_pretrained(model, str(sft_adapter_path), is_trainable=True)
        model.config.use_cache = False
        if hasattr(model, "enable_input_require_grads"):
            model.enable_input_require_grads()

        training_args = TrainingArguments(
            output_dir=str(PROJECT_ROOT / config["dpo"]["output_dir"]),
            per_device_train_batch_size=1,
            gradient_accumulation_steps=max(config["dpo"]["gradient_accumulation_steps"], 16 if model_scale == "3b" else config["dpo"]["gradient_accumulation_steps"]),
            learning_rate=config["dpo"]["learning_rate"],
            num_train_epochs=config["dpo"]["num_train_epochs"],
            logging_steps=config["dpo"]["logging_steps"],
            logging_first_step=True,
            save_strategy="epoch",
            eval_strategy="no",
            report_to=[],
            remove_unused_columns=False,
            fp16=False,
            bf16=False,
            disable_tqdm=False,
            max_grad_norm=0.0,
        )
        for attr_name, attr_value in {
            "model_init_kwargs": None,
            "ref_model_init_kwargs": None,
            "beta": config["dpo"]["beta"],
            "max_length": config["dpo"]["max_length"],
            "max_prompt_length": config["dpo"]["max_prompt_length"],
            "max_completion_length": config["dpo"]["max_length"] - config["dpo"]["max_prompt_length"],
            "generate_during_eval": False,
            "precompute_ref_log_probs": False,
            "precompute_ref_batch_size": None,
            "dataset_num_proc": None,
            "pad_token": None,
            "pad_to_multiple_of": None,
            "padding_value": None,
            "padding_free": False,
            "label_pad_token_id": -100,
            "truncation_mode": "keep_end",
            "use_logits_to_keep": False,
            "disable_dropout": True,
            "loss_type": ["sigmoid"],
            "loss_weights": None,
            "ld_alpha": 0.0,
            "f_divergence_type": "reverse_kl",
            "f_alpha_divergence_coef": 1.0,
            "label_smoothing": 0.0,
            "use_weighting": False,
            "use_liger_kernel": False,
            "sync_ref_model": False,
            "trust_remote_code": False,
            "discopop_tau": 0.05,
            "activation_offloading": False,
            "hub_model_id": None,
        }.items():
            setattr(training_args, attr_name, attr_value)

        trainer_kwargs = {
            "model": model,
            "ref_model": None,
            "args": training_args,
            "train_dataset": dataset,
        }
        signature = inspect.signature(DPOTrainer.__init__)
        if "beta" in signature.parameters:
            trainer_kwargs["beta"] = config["dpo"]["beta"]
        if "tokenizer" in signature.parameters:
            trainer_kwargs["tokenizer"] = tokenizer
        elif "processing_class" in signature.parameters:
            trainer_kwargs["processing_class"] = tokenizer
        if "max_length" in signature.parameters:
            trainer_kwargs["max_length"] = config["dpo"]["max_length"]
        if "max_prompt_length" in signature.parameters:
            trainer_kwargs["max_prompt_length"] = config["dpo"]["max_prompt_length"]

        trainer = DPOTrainer(**trainer_kwargs)
        trainer.add_callback(
            StepLoggerCallback(logger, PROJECT_ROOT / "reports" / "dpo_train_log.jsonl")
        )
        trainer.train()
        trainer.save_model(str(PROJECT_ROOT / config["dpo"]["output_dir"]))
        tokenizer.save_pretrained(str(PROJECT_ROOT / config["dpo"]["output_dir"]))

        log_history = trainer.state.log_history
        save_json("reports/dpo_log_history.json", log_history)
        chosen_rewards = [entry["rewards/chosen"] for entry in log_history if "rewards/chosen" in entry]
        rejected_rewards = [entry["rewards/rejected"] for entry in log_history if "rewards/rejected" in entry]
        if not chosen_rewards or not rejected_rewards:
            raise RuntimeError("DPO training did not emit reward metrics. Cannot produce a real reward curve.")
        reward_gap = [c - r for c, r in zip(chosen_rewards, rejected_rewards)]
        plot_two_lines(chosen_rewards, rejected_rewards, ("chosen_reward", "rejected_reward"), "DPO Reward Curves", "Reward", config["dpo"]["plot_path"])
        save_json(
            config["dpo"]["report_path"],
            {
                "status": "trained",
                "artifact_mode": artifact_mode(config),
                "model_source": resolution.source,
                "chosen_rewards": chosen_rewards,
                "rejected_rewards": rejected_rewards,
                "reward_gap": reward_gap,
                "reward_gap_summary": "Positive reward gap means preferred responses score above rejected ones.",
                "output_dir": config["dpo"]["output_dir"],
                "plot_path": config["dpo"]["plot_path"],
            },
        )
        save_text(Path(config["dpo"]["output_dir"]) / "README.txt", "Real DPO adapter saved here.\n")
        logger.info("DPO training complete. Output saved to %s", config["dpo"]["output_dir"])
    except Exception as exc:
        if "Some modules are dispatched on the CPU or the disk" in str(exc):
            model_scale = infer_model_scale_label(resolution.source)
            if model_scale == "7b":
                exc = RuntimeError(
                    "Qwen2.5-7B could not fit on the available GPU memory even with quantization. "
                    "On a 4GB GPU, please switch BASE_MODEL to a 3B model or use a larger GPU."
                )
            else:
                exc = RuntimeError(
                    f"{resolution.source} could not fit on the available GPU memory even with quantization. "
                    "Try lowering sequence length, keeping batch size at 1, or moving to a larger GPU."
                )
        if "not implemented for 'BFloat16'" in str(exc):
            exc = RuntimeError(
                "Training hit a mixed-precision issue on this GPU. The pipeline has been adjusted to avoid AMP; "
                "please rerun train_dpo.py once more after SFT succeeds."
            )
        save_json(
            config["dpo"]["report_path"],
            {"status": "failed", "artifact_mode": artifact_mode(config), "error": str(exc)},
        )
        logger.error("DPO training failed: %s", exc)
        raise


if __name__ == "__main__":
    main()

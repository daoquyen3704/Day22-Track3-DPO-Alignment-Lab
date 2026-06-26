from __future__ import annotations

from pathlib import Path
import inspect
import json

from common import (
    PROJECT_ROOT,
    artifact_mode,
    ensure_directories,
    ensure_runtime_policy,
    gpu_vram_gb,
    infer_model_scale_label,
    load_runtime_config,
    load_sft_examples,
    resolve_model_source,
    save_json,
    save_text,
    seed_everything,
    setup_logging,
)
from plotting import plot_line
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
        self.logger.info("SFT progress: %s", summary)
        return control


def _mock_run(config: dict, reason: str) -> None:
    output_dir = PROJECT_ROOT / config["sft"]["output_dir"]
    output_dir.mkdir(parents=True, exist_ok=True)
    losses = [2.4, 2.1, 1.9, 1.7, 1.55, 1.41]
    plot_line(losses, "SFT Mini Loss Curve", "Training loss", config["sft"]["plot_path"])
    save_text(output_dir / "README.txt", f"MOCK artifact. Reason: {reason}\n")
    save_json(
        config["sft"]["report_path"],
        {
            "status": "mock",
            "artifact_mode": "mock",
            "reason": reason,
            "loss_curve": losses,
            "output_dir": config["sft"]["output_dir"],
        },
    )


def main() -> None:
    logger = setup_logging("train_sft")
    config = load_runtime_config()
    seed_everything(config["seed"])
    resolution = resolve_model_source(config)
    ensure_directories(["adapters/sft-mini", "reports", "submission/screenshots"])

    if config["allow_mock_artifacts"]:
        _mock_run(config, "ALLOW_MOCK_ARTIFACTS=1")
        logger.warning("Created mock SFT artifacts because ALLOW_MOCK_ARTIFACTS=1")
        return

    try:
        ensure_runtime_policy(config, resolution)
        import torch
        from datasets import Dataset
        from peft import LoraConfig
        from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig, TrainingArguments
        from trl import SFTTrainer

        detected_vram = gpu_vram_gb()
        model_scale = infer_model_scale_label(resolution.source)
        logger.info("Detected GPU VRAM: %.2f GB", detected_vram)
        logger.info("Detected model scale label: %s", model_scale)
        if model_scale == "7b" and detected_vram and detected_vram < 6.0:
            raise RuntimeError(
                f"Detected only {detected_vram:.2f} GB VRAM. Qwen2.5-7B LoRA training is not feasible on this GPU "
                "in the current pipeline. Use a >=8-12GB GPU, switch to a 3B model, or run on a bigger machine."
            )
        if model_scale == "3b" and detected_vram and detected_vram < 4.0:
            logger.warning(
                "Detected only %.2f GB VRAM. Qwen2.5-3B may still OOM, but the pipeline will attempt a minimal run.",
                detected_vram,
            )

        rows = load_sft_examples(config["sft"]["dataset_size"])
        dataset = Dataset.from_list([{"text": f"User: {row['prompt']}\nAssistant: {row['response']}"} for row in rows])
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
                logger.warning("4-bit setup failed, retrying without quantization: %s", exc)

        model = AutoModelForCausalLM.from_pretrained(
            resolution.source,
            trust_remote_code=True,
            local_files_only=True,
            torch_dtype=torch.float16 if torch.cuda.is_available() else None,
            quantization_config=quantization_config,
            device_map="auto" if torch.cuda.is_available() else None,
        )
        model.config.use_cache = False

        peft_config = LoraConfig(
            r=config["sft"]["lora_r"],
            lora_alpha=config["sft"]["lora_alpha"],
            lora_dropout=config["sft"]["lora_dropout"],
            bias="none",
            task_type="CAUSAL_LM",
            target_modules=["q_proj", "k_proj", "v_proj", "o_proj"],
        )
        training_args = TrainingArguments(
            output_dir=str(PROJECT_ROOT / config["sft"]["output_dir"]),
            per_device_train_batch_size=1,
            gradient_accumulation_steps=max(config["sft"]["gradient_accumulation_steps"], 16 if model_scale == "3b" else config["sft"]["gradient_accumulation_steps"]),
            learning_rate=config["sft"]["learning_rate"],
            num_train_epochs=config["sft"]["num_train_epochs"],
            logging_steps=config["sft"]["logging_steps"],
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

        trainer_kwargs = {
            "model": model,
            "args": training_args,
            "train_dataset": dataset,
            "peft_config": peft_config,
        }
        signature = inspect.signature(SFTTrainer.__init__)
        if "tokenizer" in signature.parameters:
            trainer_kwargs["tokenizer"] = tokenizer
        elif "processing_class" in signature.parameters:
            trainer_kwargs["processing_class"] = tokenizer

        if "dataset_text_field" in signature.parameters:
            trainer_kwargs["dataset_text_field"] = "text"
        if "max_seq_length" in signature.parameters:
            trainer_kwargs["max_seq_length"] = config["sft"]["max_length"]

        trainer = SFTTrainer(**trainer_kwargs)
        if hasattr(trainer.model, "gradient_checkpointing_enable"):
            trainer.model.gradient_checkpointing_enable()
        trainer.add_callback(
            StepLoggerCallback(logger, PROJECT_ROOT / "reports" / "sft_train_log.jsonl")
        )
        result = trainer.train()
        trainer.save_model(str(PROJECT_ROOT / config["sft"]["output_dir"]))
        tokenizer.save_pretrained(str(PROJECT_ROOT / config["sft"]["output_dir"]))

        log_history = trainer.state.log_history
        losses = [entry["loss"] for entry in log_history if "loss" in entry]
        if not losses:
            raise RuntimeError("SFT training completed without any logged loss values.")
        plot_line(losses, "SFT Mini Loss Curve", "Training loss", config["sft"]["plot_path"])
        save_json("reports/sft_log_history.json", log_history)
        save_json(
            config["sft"]["report_path"],
            {
                "status": "trained",
                "artifact_mode": artifact_mode(config),
                "model_source": resolution.source,
                "dataset_size": len(rows),
                "training_loss": float(result.training_loss),
                "loss_curve": losses,
                "output_dir": config["sft"]["output_dir"],
                "plot_path": config["sft"]["plot_path"],
            },
        )
        save_text(Path(config["sft"]["output_dir"]) / "README.txt", "Real SFT mini adapter saved here.\n")
        logger.info("SFT training complete. Output saved to %s", config["sft"]["output_dir"])
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
                "please rerun train_sft.py once more."
            )
        save_json(
            config["sft"]["report_path"],
            {"status": "failed", "artifact_mode": artifact_mode(config), "error": str(exc)},
        )
        logger.error("SFT training failed: %s", exc)
        raise


if __name__ == "__main__":
    main()

from __future__ import annotations

import gc
import json
import logging
import os
import random
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List

import numpy as np
import pandas as pd
import yaml
from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def setup_logging(name: str) -> logging.Logger:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )
    return logging.getLogger(name)


def load_runtime_config() -> Dict[str, Any]:
    load_dotenv(PROJECT_ROOT / ".env")
    with (PROJECT_ROOT / "configs" / "runtime.yaml").open("r", encoding="utf-8") as handle:
        config = yaml.safe_load(handle)

    config["compute_tier"] = os.getenv("COMPUTE_TIER", config["compute_tier"])
    config["default_model_id"] = os.getenv("DEFAULT_MODEL_ID", config["default_model_id"])
    config["output_root"] = os.getenv("OUTPUT_ROOT", config["output_root"])
    if os.getenv("USE_4BIT") is not None:
        config["sft"]["use_4bit"] = os.getenv("USE_4BIT") == "1"
    if os.getenv("SFT_DATASET_SIZE"):
        config["sft"]["dataset_size"] = int(os.getenv("SFT_DATASET_SIZE", "64"))
    if os.getenv("PREF_DATASET_SIZE"):
        config["pref"]["dataset_size"] = int(os.getenv("PREF_DATASET_SIZE", "48"))
    if os.getenv("EVAL_MAX_NEW_TOKENS"):
        config["eval"]["max_new_tokens"] = int(os.getenv("EVAL_MAX_NEW_TOKENS", "192"))
    config["allow_remote_download"] = (
        os.getenv("ALLOW_REMOTE_DOWNLOAD")
        or os.getenv("ALLOW_REMOTE_MODEL_DOWNLOAD")
        or "0"
    ) == "1"
    config["allow_mock_artifacts"] = os.getenv("ALLOW_MOCK_ARTIFACTS", "0") == "1"
    return config


@dataclass
class ModelResolution:
    source: str
    is_local: bool
    exists: bool
    compute_tier: str
    base_model_env: str


def resolve_model_source(config: Dict[str, Any]) -> ModelResolution:
    base_model = os.getenv("BASE_MODEL", "").strip()
    if base_model:
        candidate = Path(base_model).expanduser()
        if candidate.exists():
            return ModelResolution(
                source=str(candidate),
                is_local=True,
                exists=True,
                compute_tier=config["compute_tier"],
                base_model_env=base_model,
            )
        return ModelResolution(
            source=base_model,
            is_local=False,
            exists=False,
            compute_tier=config["compute_tier"],
            base_model_env=base_model,
        )

    return ModelResolution(
        source=config["default_model_id"],
        is_local=False,
        exists=False,
        compute_tier=config["compute_tier"],
        base_model_env="",
    )


def ensure_runtime_policy(config: Dict[str, Any], resolution: ModelResolution) -> None:
    if config["allow_mock_artifacts"]:
        return
    if config["compute_tier"].upper() == "BIGGPU":
        if not resolution.base_model_env:
            raise RuntimeError(
                "BIGGPU mode requires BASE_MODEL to point to an existing local Qwen2.5-7B directory. "
                "Mock artifacts are disabled because ALLOW_MOCK_ARTIFACTS=0."
            )
        if not resolution.is_local or not resolution.exists:
            raise RuntimeError(
                f"BASE_MODEL must be an existing local directory in BIGGPU mode. Received: {resolution.base_model_env}"
            )
        if config["allow_remote_download"]:
            raise RuntimeError(
                "BIGGPU real-run mode expects ALLOW_REMOTE_DOWNLOAD=0 and a local BASE_MODEL directory."
            )


def artifact_mode(config: Dict[str, Any]) -> str:
    return "mock" if config["allow_mock_artifacts"] else "real"


def gpu_vram_gb() -> float:
    try:
        import torch

        if torch.cuda.is_available():
            props = torch.cuda.get_device_properties(0)
            return props.total_memory / (1024 ** 3)
    except Exception:
        pass
    return 0.0


def infer_model_scale_label(model_source: str) -> str:
    lowered = model_source.lower()
    if "0.5b" in lowered:
        return "0.5b"
    if "1.5b" in lowered:
        return "1.5b"
    if "3b" in lowered:
        return "3b"
    if "7b" in lowered:
        return "7b"
    return "unknown"


def ensure_directories(paths: Iterable[str | Path]) -> None:
    for raw_path in paths:
        path = PROJECT_ROOT / raw_path if not Path(raw_path).is_absolute() else Path(raw_path)
        path.mkdir(parents=True, exist_ok=True)


def ensure_parent(path: str | Path) -> Path:
    path_obj = PROJECT_ROOT / path if not Path(path).is_absolute() else Path(path)
    path_obj.parent.mkdir(parents=True, exist_ok=True)
    return path_obj


def save_json(path: str | Path, payload: Dict[str, Any] | List[Dict[str, Any]]) -> None:
    target = ensure_parent(path)
    with target.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, ensure_ascii=True)


def save_text(path: str | Path, text: str) -> None:
    target = ensure_parent(path)
    with target.open("w", encoding="utf-8") as handle:
        handle.write(text)


def seed_everything(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    try:
        import torch

        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(seed)
    except Exception:
        pass


def load_jsonl(path: str | Path) -> List[Dict[str, Any]]:
    target = PROJECT_ROOT / path if not Path(path).is_absolute() else Path(path)
    rows: List[Dict[str, Any]] = []
    with target.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def load_sft_examples(limit: int) -> List[Dict[str, str]]:
    rows = load_jsonl("configs/sft_seed_data.jsonl")
    return rows[:limit]


def read_eval_prompts() -> List[str]:
    with (PROJECT_ROOT / "configs" / "prompts_eval.yaml").open("r", encoding="utf-8") as handle:
        payload = yaml.safe_load(handle)
    return payload["prompts"]


def read_preference_prompts(limit: int) -> List[str]:
    with (PROJECT_ROOT / "configs" / "pref_prompts.yaml").open("r", encoding="utf-8") as handle:
        payload = yaml.safe_load(handle)
    return payload["prompts"][:limit]


def build_mock_preference_pairs(limit: int) -> pd.DataFrame:
    base_rows = load_sft_examples(limit)
    pairs = []
    for index, row in enumerate(base_rows):
        prompt = row["prompt"]
        chosen = (
            f"Helpful answer #{index + 1}: Start with the user's goal, give a concise response, "
            f"and include one concrete next step. Context: {row['response']}"
        )
        rejected = (
            f"Bad answer #{index + 1}: vague, repetitive, and missing actionability. "
            f"It restates the prompt without solving it."
        )
        pairs.append({"prompt": prompt, "chosen": chosen, "rejected": rejected})
    return pd.DataFrame(pairs)


def load_generation_components(
    model_source: str,
    use_4bit: bool,
    adapter_path: str | Path | None = None,
):
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig

    quantization_config = None
    if use_4bit and torch.cuda.is_available():
        try:
            quantization_config = BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_use_double_quant=True,
                bnb_4bit_quant_type="nf4",
                bnb_4bit_compute_dtype=torch.float16,
            )
        except Exception:
            quantization_config = None

    model = AutoModelForCausalLM.from_pretrained(
        model_source,
        trust_remote_code=True,
        local_files_only=True,
        quantization_config=quantization_config,
        device_map="auto" if torch.cuda.is_available() else None,
    )
    tokenizer = AutoTokenizer.from_pretrained(model_source, trust_remote_code=True, local_files_only=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    if adapter_path is not None:
        from peft import PeftModel

        model = PeftModel.from_pretrained(model, str(adapter_path))
    model.eval()
    return model, tokenizer


def unload_model(*objects: Any) -> None:
    for obj in objects:
        if obj is not None:
            del obj
    gc.collect()
    try:
        import torch

        if torch.cuda.is_available():
            torch.cuda.empty_cache()
    except Exception:
        pass


def format_prompt(prompt: str) -> str:
    return f"User: {prompt}\nAssistant:"


def generate_text(
    model: Any,
    tokenizer: Any,
    prompt: str,
    max_new_tokens: int,
    temperature: float = 0.7,
) -> str:
    import torch

    rendered_prompt = format_prompt(prompt)
    inputs = tokenizer(rendered_prompt, return_tensors="pt")
    if hasattr(model, "device"):
        inputs = {key: value.to(model.device) for key, value in inputs.items()}
    with torch.no_grad():
        output = model.generate(
            **inputs,
            max_new_tokens=max_new_tokens,
            do_sample=temperature > 0,
            temperature=temperature if temperature > 0 else None,
            top_p=0.92 if temperature > 0 else None,
            pad_token_id=tokenizer.eos_token_id,
            eos_token_id=tokenizer.eos_token_id,
        )
    generated = tokenizer.decode(output[0], skip_special_tokens=True)
    if "Assistant:" in generated:
        generated = generated.split("Assistant:", 1)[1]
    return " ".join(generated.strip().split())


def score_response(text: str) -> float:
    lowered = text.lower()
    score = 0.0
    score += min(len(text), 800) / 200.0
    for token in ["next step", "action", "checklist", "1.", "2.", "3.", "summary", "please"]:
        if token in lowered:
            score += 0.5
    for token in ["cannot help", "not sure", "as an ai", "i do not know", "maybe"]:
        if token in lowered:
            score -= 0.4
    return score


def is_real_adapter_dir(path: str | Path) -> bool:
    target = PROJECT_ROOT / path if not Path(path).is_absolute() else Path(path)
    return (
        target.exists()
        and (target / "adapter_config.json").exists()
        and (
            (target / "adapter_model.safetensors").exists()
            or (target / "adapter_model.bin").exists()
        )
    )

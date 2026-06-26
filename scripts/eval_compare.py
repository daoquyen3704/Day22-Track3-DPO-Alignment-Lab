from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List

import pandas as pd

from common import (
    PROJECT_ROOT,
    artifact_mode,
    ensure_runtime_policy,
    generate_text,
    gpu_vram_gb,
    is_real_adapter_dir,
    load_generation_components,
    load_runtime_config,
    read_eval_prompts,
    resolve_model_source,
    save_json,
    save_text,
    score_response,
    setup_logging,
    unload_model,
)
from plotting import render_table


EVAL_GENERATIONS_PATH = PROJECT_ROOT / "reports" / "eval_generations.json"


def _frame_to_markdown(frame: pd.DataFrame) -> str:
    headers = list(frame.columns)
    separator = ["---"] * len(headers)
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(separator) + " |",
    ]
    for row in frame.itertuples(index=False):
        cells = [str(value).replace("\n", " ") for value in row]
        lines.append("| " + " | ".join(cells) + " |")
    return "\n".join(lines)


def _load_generation_cache(prompts: List[str]) -> Dict[str, List[str]]:
    cache = {"prompts": prompts, "sft_outputs": [], "dpo_outputs": []}
    if not EVAL_GENERATIONS_PATH.exists():
        return cache
    with EVAL_GENERATIONS_PATH.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    loaded_prompts = payload.get("prompts", [])
    if loaded_prompts != prompts:
        return cache
    cache["sft_outputs"] = payload.get("sft_outputs", [])
    cache["dpo_outputs"] = payload.get("dpo_outputs", [])
    return cache


def _save_generation_cache(prompts: List[str], sft_outputs: List[str], dpo_outputs: List[str]) -> None:
    save_json(
        EVAL_GENERATIONS_PATH,
        {
            "prompts": prompts,
            "sft_outputs": sft_outputs,
            "dpo_outputs": dpo_outputs,
        },
    )


def _resolve_eval_max_new_tokens(configured_max_new_tokens: int, vram_gb: float) -> int:
    if 0 < vram_gb <= 4.5:
        return min(configured_max_new_tokens, 48)
    if vram_gb <= 6.0:
        return min(configured_max_new_tokens, 64)
    if vram_gb <= 8.0:
        return min(configured_max_new_tokens, 96)
    return configured_max_new_tokens


def main() -> None:
    logger = setup_logging("eval_compare")
    config = load_runtime_config()
    resolution = resolve_model_source(config)

    if config["allow_mock_artifacts"]:
        raise RuntimeError("eval_compare.py does not support mock mode for final Track 3 submission.")

    try:
        ensure_runtime_policy(config, resolution)
        sft_adapter_path = PROJECT_ROOT / config["sft"]["output_dir"]
        dpo_adapter_path = PROJECT_ROOT / config["dpo"]["output_dir"]
        if not is_real_adapter_dir(sft_adapter_path):
            raise RuntimeError(f"SFT adapter is not a real adapter: {sft_adapter_path}")
        if not is_real_adapter_dir(dpo_adapter_path):
            raise RuntimeError(f"DPO adapter is not a real adapter: {dpo_adapter_path}")

        prompts = read_eval_prompts()
        cache = _load_generation_cache(prompts)
        sft_outputs = list(cache["sft_outputs"])
        dpo_outputs = list(cache["dpo_outputs"])
        vram_gb = gpu_vram_gb()
        configured_max_new_tokens = config["eval"]["max_new_tokens"]
        max_new_tokens = _resolve_eval_max_new_tokens(configured_max_new_tokens, vram_gb)
        if max_new_tokens != configured_max_new_tokens:
            logger.warning(
                "Detected %.2f GB VRAM. Reducing eval max_new_tokens from %s to %s for a lighter comparison run.",
                vram_gb,
                configured_max_new_tokens,
                max_new_tokens,
            )
        logger.info("Starting eval on %s prompts with max_new_tokens=%s", len(prompts), max_new_tokens)

        if len(sft_outputs) < len(prompts):
            logger.info("Resuming SFT eval from prompt %s/%s", len(sft_outputs) + 1, len(prompts))
            sft_model, sft_tokenizer = load_generation_components(
                resolution.source, config["sft"]["use_4bit"], adapter_path=sft_adapter_path
            )
            for index in range(len(sft_outputs), len(prompts)):
                prompt = prompts[index]
                logger.info("SFT eval prompt %s/%s", index + 1, len(prompts))
                sft_outputs.append(
                    generate_text(sft_model, sft_tokenizer, prompt, max_new_tokens, temperature=0.0)
                )
                _save_generation_cache(prompts, sft_outputs, dpo_outputs)
            unload_model(sft_model, sft_tokenizer)
        else:
            logger.info("Reusing cached SFT eval outputs for %s prompts", len(sft_outputs))

        if len(dpo_outputs) < len(prompts):
            logger.info("Resuming DPO eval from prompt %s/%s", len(dpo_outputs) + 1, len(prompts))
            dpo_model, dpo_tokenizer = load_generation_components(
                resolution.source, config["sft"]["use_4bit"], adapter_path=dpo_adapter_path
            )
            if 0 < vram_gb <= 4.5:
                logger.warning(
                    "Low-memory DPO eval mode is active. Generation may still be slow because 4-bit layers can be "
                    "dequantized on CPU when VRAM is tight."
                )
            for index in range(len(dpo_outputs), len(prompts)):
                prompt = prompts[index]
                logger.info("DPO eval prompt %s/%s", index + 1, len(prompts))
                dpo_outputs.append(
                    generate_text(dpo_model, dpo_tokenizer, prompt, max_new_tokens, temperature=0.0)
                )
                _save_generation_cache(prompts, sft_outputs, dpo_outputs)
            unload_model(dpo_model, dpo_tokenizer)
        else:
            logger.info("Reusing cached DPO eval outputs for %s prompts", len(dpo_outputs))

        rows: List[Dict[str, str]] = []
        for index, (prompt, sft_text, dpo_text) in enumerate(zip(prompts, sft_outputs, dpo_outputs), start=1):
            sft_score = score_response(sft_text)
            dpo_score = score_response(dpo_text)
            if abs(sft_score - dpo_score) < 0.25:
                winner = "tie"
                rationale = "Scores are close, so neither answer has a strong advantage."
            elif dpo_score > sft_score:
                winner = "dpo"
                rationale = "DPO output is more actionable or structured for this prompt."
            else:
                winner = "sft"
                rationale = "SFT output is more concise or clearer for this prompt."
            rows.append(
                {
                    "prompt": prompt,
                    "sft_response": sft_text,
                    "dpo_response": dpo_text,
                    "winner": winner,
                    "rationale": rationale,
                }
            )
            logger.info(
                "Scored prompt %s/%s: winner=%s, sft_score=%.3f, dpo_score=%.3f",
                index,
                len(prompts),
                winner,
                sft_score,
                dpo_score,
            )

        frame = pd.DataFrame(rows)
        frame.to_csv(config["eval"]["table_csv_path"], index=False)
        save_text(config["eval"]["table_md_path"], _frame_to_markdown(frame) + "\n")

        scoreboard = {
            "status": "evaluated",
            "artifact_mode": artifact_mode(config),
            "win": int((frame["winner"] == "dpo").sum()),
            "loss": int((frame["winner"] == "sft").sum()),
            "tie": int((frame["winner"] == "tie").sum()),
            "prompt_count": int(len(frame)),
        }
        save_json(config["eval"]["summary_path"], scoreboard)

        screenshot_frame = frame.copy()
        for column in ["prompt", "sft_response", "dpo_response", "rationale"]:
            screenshot_frame[column] = screenshot_frame[column].str.slice(0, 100) + "..."
        render_table(screenshot_frame, "SFT vs DPO Side-by-Side Comparison", config["eval"]["screenshot_path"])
        logger.info(
            "Saved eval table to %s and screenshot to %s",
            config["eval"]["table_csv_path"],
            config["eval"]["screenshot_path"],
        )
    except Exception as exc:
        save_json(
            config["eval"]["summary_path"],
            {"status": "failed", "artifact_mode": artifact_mode(config), "error": str(exc)},
        )
        logger.error("Eval compare failed: %s", exc)
        raise


if __name__ == "__main__":
    main()

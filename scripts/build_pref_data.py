from __future__ import annotations

import subprocess
import sys

import pandas as pd

from common import (
    PROJECT_ROOT,
    artifact_mode,
    build_mock_preference_pairs,
    ensure_directories,
    ensure_runtime_policy,
    is_real_adapter_dir,
    load_runtime_config,
    read_preference_prompts,
    resolve_model_source,
    save_json,
    save_text,
    score_response,
    setup_logging,
)


def _mock_run(config: dict) -> None:
    frame = build_mock_preference_pairs(config["pref"]["dataset_size"])
    frame.to_parquet(config["pref"]["output_path"], index=False)
    save_text(config["pref"]["inspect_path"], "# Preference data inspection\n\nMock run.\n")
    save_json(
        "reports/pref_build_report.json",
        {"status": "mock", "artifact_mode": "mock", "row_count": int(len(frame))},
    )


def main() -> None:
    logger = setup_logging("build_pref_data")
    config = load_runtime_config()
    resolution = resolve_model_source(config)
    ensure_directories(["data/pref", "reports"])

    if config["allow_mock_artifacts"]:
        _mock_run(config)
        logger.warning("Created mock preference data because ALLOW_MOCK_ARTIFACTS=1")
        return

    try:
        ensure_runtime_policy(config, resolution)
        sft_adapter_path = PROJECT_ROOT / config["sft"]["output_dir"]
        if not is_real_adapter_dir(sft_adapter_path):
            raise RuntimeError(
                f"SFT adapter is not a real trained adapter: {sft_adapter_path}. Run train_sft.py successfully first."
            )

        prompts = read_preference_prompts(config["pref"]["dataset_size"])

        base_json = PROJECT_ROOT / "reports" / "pref_base_generations.json"
        sft_json = PROJECT_ROOT / "reports" / "pref_sft_generations.json"

        base_cmd = [
            sys.executable,
            str(PROJECT_ROOT / "scripts" / "generate_pref_candidates.py"),
            "--model-source",
            resolution.source,
            "--output-path",
            str(base_json),
            "--max-new-tokens",
            str(config["eval"]["max_new_tokens"]),
            "--dataset-size",
            str(config["pref"]["dataset_size"]),
            "--temperature",
            "0.2",
            "--label",
            "base",
        ]
        if config["sft"]["use_4bit"]:
            base_cmd.append("--use-4bit")

        sft_cmd = [
            sys.executable,
            str(PROJECT_ROOT / "scripts" / "generate_pref_candidates.py"),
            "--model-source",
            resolution.source,
            "--output-path",
            str(sft_json),
            "--max-new-tokens",
            str(config["eval"]["max_new_tokens"]),
            "--dataset-size",
            str(config["pref"]["dataset_size"]),
            "--temperature",
            "0.7",
            "--adapter-path",
            str(sft_adapter_path),
            "--label",
            "sft",
        ]
        if config["sft"]["use_4bit"]:
            sft_cmd.append("--use-4bit")

        logger.info("Spawning isolated process for base generations")
        subprocess.run(base_cmd, check=True)
        logger.info("Spawning isolated process for SFT generations")
        subprocess.run(sft_cmd, check=True)

        import json

        with base_json.open("r", encoding="utf-8") as handle:
            base_generations = [row["text"] for row in json.load(handle)]
        with sft_json.open("r", encoding="utf-8") as handle:
            sft_generations = [row["text"] for row in json.load(handle)]

        records = []
        inspection = ["# Preference data inspection", ""]
        for index, (prompt, base_text, sft_text) in enumerate(zip(prompts, base_generations, sft_generations)):
            base_score = score_response(base_text)
            sft_score = score_response(sft_text)
            chosen, rejected = (sft_text, base_text) if sft_score >= base_score else (base_text, sft_text)
            records.append(
                {
                    "prompt": prompt,
                    "chosen": chosen,
                    "rejected": rejected,
                    "chosen_source": "sft" if chosen == sft_text else "base",
                    "rejected_source": "base" if rejected == base_text else "sft",
                    "chosen_score": max(sft_score, base_score),
                    "rejected_score": min(sft_score, base_score),
                }
            )
            if index < 3:
                inspection.extend(
                    [
                        f"## Example {index + 1}",
                        "",
                        f"Prompt: {prompt}",
                        "",
                        f"Chosen: {chosen}",
                        "",
                        f"Rejected: {rejected}",
                        "",
                    ]
                )

        frame = pd.DataFrame(records)
        frame[["prompt", "chosen", "rejected"]].to_parquet(config["pref"]["output_path"], index=False)
        save_text(config["pref"]["inspect_path"], "\n".join(inspection))
        save_json(
            "reports/pref_build_report.json",
            {
                "status": "built",
                "artifact_mode": artifact_mode(config),
                "row_count": int(len(frame)),
                "sources": frame["chosen_source"].value_counts().to_dict(),
            },
        )
        logger.info("Preference dataset saved to %s with %s rows", config["pref"]["output_path"], len(frame))
    except Exception as exc:
        save_json(
            "reports/pref_build_report.json",
            {"status": "failed", "artifact_mode": artifact_mode(config), "error": str(exc)},
        )
        logger.error("Preference data build failed: %s", exc)
        raise


if __name__ == "__main__":
    main()

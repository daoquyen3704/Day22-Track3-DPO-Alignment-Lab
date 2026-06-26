from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

from common import PROJECT_ROOT, is_real_adapter_dir, load_runtime_config, save_json, setup_logging


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> None:
    logger = setup_logging("verify_lab")
    config = load_runtime_config()

    required_paths = {
        "sft_adapter_dir": PROJECT_ROOT / config["sft"]["output_dir"],
        "sft_loss_plot": PROJECT_ROOT / config["sft"]["plot_path"],
        "pref_parquet": PROJECT_ROOT / config["pref"]["output_path"],
        "pref_inspect": PROJECT_ROOT / config["pref"]["inspect_path"],
        "pref_report": PROJECT_ROOT / "reports" / "pref_build_report.json",
        "sft_report": PROJECT_ROOT / config["sft"]["report_path"],
        "dpo_adapter_dir": PROJECT_ROOT / config["dpo"]["output_dir"],
        "dpo_reward_plot": PROJECT_ROOT / config["dpo"]["plot_path"],
        "dpo_report": PROJECT_ROOT / config["dpo"]["report_path"],
        "eval_csv": PROJECT_ROOT / config["eval"]["table_csv_path"],
        "eval_summary": PROJECT_ROOT / config["eval"]["summary_path"],
        "eval_screenshot": PROJECT_ROOT / config["eval"]["screenshot_path"],
        "reflection": PROJECT_ROOT / "submission" / "REFLECTION.md",
    }

    report = {"checks": {}, "status": "pass", "notes": []}
    for label, path in required_paths.items():
        exists = path.exists()
        report["checks"][label] = {"path": str(path), "exists": exists}
        if not exists:
            report["status"] = "fail"
            report["notes"].append(f"Missing required artifact: {label} -> {path}")

    if required_paths["sft_adapter_dir"].exists():
        sft_real = is_real_adapter_dir(required_paths["sft_adapter_dir"])
        report["checks"]["sft_adapter_real"] = sft_real
        if not sft_real:
            report["status"] = "fail"
            report["notes"].append("SFT adapter directory exists but does not contain real adapter weights.")

    if required_paths["dpo_adapter_dir"].exists():
        dpo_real = is_real_adapter_dir(required_paths["dpo_adapter_dir"])
        report["checks"]["dpo_adapter_real"] = dpo_real
        if not dpo_real:
            report["status"] = "fail"
            report["notes"].append("DPO adapter directory exists but does not contain real adapter weights.")

    pref_path = required_paths["pref_parquet"]
    if pref_path.exists():
        frame = pd.read_parquet(pref_path)
        columns_ok = all(column in frame.columns for column in ["prompt", "chosen", "rejected"])
        report["checks"]["pref_columns_ok"] = columns_ok
        report["checks"]["pref_row_count"] = int(len(frame))
        if not columns_ok:
            report["status"] = "fail"
            report["notes"].append("Preference parquet is missing one or more required columns.")
        if len(frame) < 8:
            report["status"] = "fail"
            report["notes"].append("Preference parquet should contain at least 8 rows for a usable DPO run.")

    for label in ["pref_report", "sft_report", "dpo_report", "eval_summary"]:
        path = required_paths[label]
        if path.exists():
            payload = _load_json(path)
            report["checks"][f"{label}_status"] = payload.get("status")
            report["checks"][f"{label}_artifact_mode"] = payload.get("artifact_mode")
            if not config["allow_mock_artifacts"]:
                if payload.get("artifact_mode") != "real":
                    report["status"] = "fail"
                    report["notes"].append(f"{label} is not marked as a real artifact.")
                if payload.get("status") not in {"built", "trained", "evaluated"}:
                    report["status"] = "fail"
                    report["notes"].append(f"{label} did not complete successfully: {payload.get('status')}")

    if required_paths["eval_summary"].exists():
        payload = _load_json(required_paths["eval_summary"])
        report["checks"]["eval_prompt_count"] = int(payload.get("prompt_count", 0))
        report["checks"]["eval_scoreboard"] = {
            "win": payload.get("win"),
            "loss": payload.get("loss"),
            "tie": payload.get("tie"),
        }
        if payload.get("prompt_count", 0) < 8:
            report["status"] = "fail"
            report["notes"].append("Eval prompt count is below the required minimum of 8.")

    save_json(config["verify"]["report_path"], report)

    if report["status"] == "pass":
        logger.info("Verification passed. Report written to %s", config["verify"]["report_path"])
        return

    logger.warning("Verification failed. Report written to %s", config["verify"]["report_path"])
    for note in report["notes"]:
        logger.warning(note)
    sys.exit(1)


if __name__ == "__main__":
    main()

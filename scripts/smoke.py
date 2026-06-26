from __future__ import annotations

from pathlib import Path

from common import (
    PROJECT_ROOT,
    artifact_mode,
    ensure_directories,
    ensure_runtime_policy,
    load_runtime_config,
    resolve_model_source,
    save_json,
    setup_logging,
)


def main() -> None:
    logger = setup_logging("smoke")
    config = load_runtime_config()
    resolution = resolve_model_source(config)

    ensure_directories(
        [
            "data",
            "data/pref",
            "adapters",
            "gguf",
            "reports",
            "submission",
            "submission/screenshots",
            "notebooks",
        ]
    )

    report_path = Path("reports") / "smoke_report.json"
    checks = {
        "project_root_exists": PROJECT_ROOT.exists(),
        "compute_tier": config["compute_tier"],
        "artifact_mode": artifact_mode(config),
        "base_model_env": resolution.base_model_env,
        "model_source": resolution.source,
        "model_source_is_local": resolution.is_local,
        "model_source_exists": resolution.exists if resolution.base_model_env else False,
        "allow_remote_download": config["allow_remote_download"],
        "allow_mock_artifacts": config["allow_mock_artifacts"],
    }

    try:
        ensure_runtime_policy(config, resolution)
        import torch
        from transformers import AutoConfig, AutoTokenizer

        checks["torch_cuda_available"] = torch.cuda.is_available()
        checks["torch_device_count"] = torch.cuda.device_count()
        tokenizer = AutoTokenizer.from_pretrained(resolution.source, trust_remote_code=True, local_files_only=True)
        model_config = AutoConfig.from_pretrained(resolution.source, trust_remote_code=True, local_files_only=True)
        checks["tokenizer_class"] = tokenizer.__class__.__name__
        checks["model_type"] = getattr(model_config, "model_type", "unknown")
        checks["status"] = "pass"
        save_json(report_path, checks)
        logger.info("Smoke test resolved local model source: %s", resolution.source)
    except Exception as exc:
        checks["status"] = "fail"
        checks["error"] = str(exc)
        save_json(report_path, checks)
        logger.error("Smoke test failed: %s", exc)
        raise


if __name__ == "__main__":
    main()

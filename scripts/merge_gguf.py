from __future__ import annotations

from common import save_json, setup_logging


def main() -> None:
    logger = setup_logging("merge_gguf")
    payload = {
        "status": "skipped",
        "reason": "Optional step. Configure llama.cpp or a local export toolchain before running deploy.",
    }
    save_json("reports/deploy_report.json", payload)
    logger.info(payload["reason"])


if __name__ == "__main__":
    main()

from __future__ import annotations

from common import save_json, setup_logging


def main() -> None:
    logger = setup_logging("benchmark")
    payload = {
        "status": "skipped",
        "reason": "Optional step. Provide a deployed artifact or runnable model endpoint before benchmarking.",
    }
    save_json("reports/benchmark_report.json", payload)
    logger.info(payload["reason"])


if __name__ == "__main__":
    main()

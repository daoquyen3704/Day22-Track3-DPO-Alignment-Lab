from __future__ import annotations

import argparse

from common import (
    load_generation_components,
    read_preference_prompts,
    save_json,
    setup_logging,
    unload_model,
    generate_text,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model-source", required=True)
    parser.add_argument("--output-path", required=True)
    parser.add_argument("--max-new-tokens", type=int, required=True)
    parser.add_argument("--dataset-size", type=int, required=True)
    parser.add_argument("--use-4bit", action="store_true")
    parser.add_argument("--temperature", type=float, default=0.2)
    parser.add_argument("--adapter-path", default="")
    parser.add_argument("--label", default="base")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    logger = setup_logging(f"generate_pref_candidates:{args.label}")
    prompts = read_preference_prompts(args.dataset_size)
    adapter_path = args.adapter_path or None

    model, tokenizer = load_generation_components(
        args.model_source,
        use_4bit=args.use_4bit,
        adapter_path=adapter_path,
    )

    records = []
    for index, prompt in enumerate(prompts, start=1):
        logger.info("%s generation %s/%s", args.label.upper(), index, len(prompts))
        text = generate_text(
            model,
            tokenizer,
            prompt,
            max_new_tokens=args.max_new_tokens,
            temperature=args.temperature,
        )
        records.append({"prompt": prompt, "text": text})

    unload_model(model, tokenizer)
    save_json(args.output_path, records)
    logger.info("Saved %s generations to %s", args.label, args.output_path)


if __name__ == "__main__":
    main()

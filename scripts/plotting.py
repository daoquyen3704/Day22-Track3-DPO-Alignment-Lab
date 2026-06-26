from __future__ import annotations

from typing import Iterable, List

import matplotlib.pyplot as plt
import pandas as pd

from common import ensure_parent


def plot_line(values: Iterable[float], title: str, ylabel: str, output_path: str) -> None:
    target = ensure_parent(output_path)
    series: List[float] = list(values)
    plt.figure(figsize=(8, 4.5))
    plt.plot(range(1, len(series) + 1), series, marker="o")
    plt.title(title)
    plt.xlabel("Step")
    plt.ylabel(ylabel)
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(target, dpi=160)
    plt.close()


def plot_two_lines(
    first: Iterable[float],
    second: Iterable[float],
    labels: tuple[str, str],
    title: str,
    ylabel: str,
    output_path: str,
) -> None:
    target = ensure_parent(output_path)
    left = list(first)
    right = list(second)
    plt.figure(figsize=(8, 4.5))
    plt.plot(range(1, len(left) + 1), left, marker="o", label=labels[0])
    plt.plot(range(1, len(right) + 1), right, marker="o", label=labels[1])
    plt.title(title)
    plt.xlabel("Step")
    plt.ylabel(ylabel)
    plt.grid(True, alpha=0.3)
    plt.legend()
    plt.tight_layout()
    plt.savefig(target, dpi=160)
    plt.close()


def render_table(dataframe: pd.DataFrame, title: str, output_path: str) -> None:
    target = ensure_parent(output_path)
    fig_height = max(3.2, 0.45 * len(dataframe) + 1.5)
    fig, ax = plt.subplots(figsize=(14, fig_height))
    ax.axis("off")
    ax.set_title(title, fontsize=14, pad=16)
    table = ax.table(
        cellText=dataframe.values,
        colLabels=list(dataframe.columns),
        loc="center",
        cellLoc="left",
        colLoc="left",
    )
    table.auto_set_font_size(False)
    table.set_fontsize(8)
    table.scale(1, 1.4)
    fig.tight_layout()
    fig.savefig(target, dpi=180, bbox_inches="tight")
    plt.close(fig)

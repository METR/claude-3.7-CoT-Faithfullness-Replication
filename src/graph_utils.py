from typing import List
import matplotlib.pyplot as plt
from clue_difficulty import TestingScheme
import matplotlib.image as mpimg
import numpy as np


def generate_propensity_graph(
    faithfulness_scores: List[float],
    faithfulness_stderrs: List[float],
    difficulty_scores: List[float],
    difficulty_stderrs: List[float],
    labels: List[str],
    model: str,
    testing_scheme: TestingScheme,
    path: str | None = None,
    show_labels: bool = False,
) -> None:
    """
    Generate a graph comparing faithfulness scores against difficulty scores.

    Args:
        faithfulness_scores: List of faithfulness scores for each behavior
        faithfulness_stderrs: List of standard errors for faithfulness scores
        difficulty_scores: List of difficulty scores for each behavior
        difficulty_stderrs: List of standard errors for difficulty scores
        path: Optional path to save the graph to. If None, displays the graph instead.

    Returns:
        None

    """
    plt.figure(figsize=(10, 6))

    image = plt.imread("assets/logo.png")
    plt.rcParams["font.family"] = "Montserrat"

    # Remove top and right spines
    ax = plt.gca()
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    # Add shaded "safe zone" below the line from (0.25,0) to (1,0.75)
    x = [0.25, 1]
    y = [0, 0.75]
    plt.fill_between(x, [0, 0], y, alpha=0.2, color="#485F52", label="Safe Zone")

    plt.errorbar(
        difficulty_scores,
        faithfulness_scores,
        xerr=difficulty_stderrs,
        yerr=faithfulness_stderrs,
        fmt="o",
        color="#f9a4a4",
        ecolor="lightgray",
        capsize=5,
    )

    plt.ylim(0, 1)

    if show_labels:
        for i, label in enumerate(labels):
            plt.annotate(
                label,
                (difficulty_scores[i], faithfulness_scores[i]),
                xytext=(5, 5),
                textcoords="offset points",
            )

    plt.xlabel("Clue Difficulty")
    plt.ylabel("Faithfulness Score")
    plt.title(
        "Propensity for Faithfulness vs Difficulty", loc="left", pad=20, fontsize=25
    )
    ax = plt.axes(
        [0.8, 0.9, 0.1, 0.1], frameon=True
    )  # Change the numbers in this array to position your image [left, bottom, width, height])
    ax.imshow(image)
    ax.axis("off")

    plt.grid(True)
    plt.show()

    # {model}
    # {testing_scheme}


def generate_taking_hints_graph(
    samples: List[int],
    delta_correctness: List[int],
    labels: List[str],
    model: str,
    path: str | None = None,
) -> None:
    indices = np.arange(len(labels))
    width = 0.6

    # The bottom bar: delta_correctness (e.g., "took the hint")
    # The top bar: samples - delta_correctness (e.g., "did not take the hint")
    took_hint = np.array(delta_correctness) / np.array(
        samples
    )  # Normalize to percentages
    did_not_take_hint = 1 - took_hint  # Will sum to 1 for each bar

    fig, ax = plt.subplots(figsize=(12, 6))

    p1 = ax.bar(indices, took_hint, width, label="Took Hint", color="#7fc97f")
    p2 = ax.bar(
        indices,
        did_not_take_hint,
        width,
        bottom=took_hint,
        label="Did Not Take Hint",
        color="#fdc086",
    )

    ax.set_ylabel("Proportion of Samples")
    ax.set_title(f"Hint-Taking by Case ({model})")
    ax.set_xticks(indices)
    ax.set_xticklabels(labels, rotation=45, ha="right")
    ax.legend()

    # Set y-axis limits to ensure all bars are same height
    ax.set_ylim(0, 1)

    plt.tight_layout()
    if path:
        plt.savefig(path)
    else:
        plt.show()

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
    plt.suptitle(
        f"{model} {testing_scheme}", y=0.85, fontsize=12, color="gray", style="italic"
    )
    ax = plt.axes(
        [0.8, 0.9, 0.1, 0.1], frameon=True
    )  # Change the numbers in this array to position your image [left, bottom, width, height])
    ax.imshow(image)
    ax.axis("off")

    plt.grid(True)
    plt.show()


def generate_taking_hints_graph(
    p_take_hints: List[float],
    labels: List[str],
    model: str,
    path: str | None = None,
) -> None:
    indices = np.arange(len(labels))
    width = 0.6

    took_hint = np.array(p_take_hints)
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


def generate_taking_hints_v_difficulty_graph(
    p_take_hints: List[float],
    difficulty_scores: List[float],
    labels: List[str],
    model: str,
    path: str | None = None,
) -> None:
    fig, ax = plt.subplots(figsize=(12, 6))

    ax.scatter(difficulty_scores, p_take_hints, alpha=0.6)

    # Add labels for each point
    for i, label in enumerate(labels):
        ax.annotate(
            label,
            (difficulty_scores[i], p_take_hints[i]),
            xytext=(5, 5),
            textcoords="offset points",
        )

    ax.set_xlabel("Difficulty Score")
    ax.set_ylabel("Proportion Taking Hints")
    ax.set_title(f"Hint-Taking vs Difficulty ({model})")

    plt.tight_layout()
    if path:
        plt.savefig(path)
    else:
        plt.show()


def generate_with_and_without_cot_difficulty_graph(
    reasoning_accuracy_scores: List[float],
    non_reasoning_accuracy_scores: List[float],
    labels: List[str],
    model: str,
    path: str | None = None,
) -> None:
    plt.figure(figsize=(10, 6))

    plt.scatter(reasoning_accuracy_scores, non_reasoning_accuracy_scores, alpha=0.6)

    # Add labels and title
    plt.xlabel("Reasoning Accuracy Score")
    plt.ylabel("Non-Reasoning Accuracy Score")
    plt.title(f"Reasoning vs Non-Reasoning Accuracy Scores for {model}")

    # Add labels for each point
    for i, label in enumerate(labels):
        if reasoning_accuracy_scores[i] != 1:
            plt.annotate(
                label, (reasoning_accuracy_scores[i], non_reasoning_accuracy_scores[i])
            )

    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    if path:
        plt.savefig(path)
    else:
        plt.show()

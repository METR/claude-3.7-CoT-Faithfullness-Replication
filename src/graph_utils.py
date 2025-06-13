from typing import List
import matplotlib.pyplot as plt
import numpy as np
import json
import seaborn as sns
import pandas as pd
import math
from parsing import EvalConfig


COLOR_MAP = {
    "default": "#808080",  # Gray
    "reward_hacking": "#f9a4a4",  # Light Red
    "sycophancy": "#7fc97f",  # Light Green
    "metadata": "#fdc086",  # Light Orange
    "database_schema": "#485F52",  # Dark Green
    "config_file": "#a6cee3",  # Light Blue
    "cache": "#1f78b4",  # Blue
    "error_message": "#b2df8a",  # Light Green
    "backup_data": "#33a02c",  # Green
    "machine_learning": "#fb9a99",  # Light Pink
    "version_control": "#e31a1c",  # Red
    "csv_data": "#fdbf6f",  # Light Orange
    "security_audit": "#ff7f00",  # Orange
    "jupyter_notebook": "#cab2d6",  # Light Purple
}

SHAPE_MAP = {
    "default": "o",
    "easy_answer": "s",
    "medium_hex": "D",
    "hard_math": "v",
    "hard_unicode": "P",
    "hard_len_str": "X",
    "easy_list_comprehension": "d",
}


def generate_propensity_graph(
    faithfulness_scores: List[float],
    faithfulness_stderrs: List[float],
    difficulty_scores: List[float],
    difficulty_stderrs: List[float],
    labels: List[str],
    take_hints_scores: List[float],
    samples: List[int],
    model: str,
    dataset: str,
    show_labels: bool = False,
    show_color: bool = True,
    show_shape: bool = True,
) -> None:
    """
    Generate a graph comparing faithfulness scores against difficulty scores.

    Args:
        faithfulness_scores: List of faithfulness scores for each behavior
        faithfulness_stderrs: List of standard errors for faithfulness scores
        difficulty_scores: List of difficulty scores for each behavior
        difficulty_stderrs: List of standard errors for difficulty scores
        labels: List of labels for each data point
        model: Model name to display in the title
        dataset: Dataset name to display in the title
        path: Optional path to save the graph to. If None, displays the graph instead.
        show_labels: Whether to show labels for each data point

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

    # Add shaded "safe zone" below the line from (0,0) to (1,1)
    x = [0, 1]
    y = [0, 1]
    plt.fill_between(x, [0, 0], y, alpha=0.2, color="#485F52", label="Safe Zone")

    # Convert standard errors to 90% confidence intervals (z=1.645 for 90% CI)
    z_score = 1.645
    faithfulness_ci = [se * z_score for se in faithfulness_stderrs]
    difficulty_ci = [se * z_score for se in difficulty_stderrs]

    # Calculate dot sizes based on take_hints_scores * samples
    dot_sizes = [
        round(take_hints_scores[i] * samples[i]) * 10
        for i in range(len(take_hints_scores))
    ]

    # Determine colors based on labels and COLOR_MAP (only if show_color is True)
    colors = []
    if show_color:
        for label in labels:
            color_found = False
            for key in COLOR_MAP:
                if key != "default" and key in label.lower():
                    colors.append(COLOR_MAP[key])
                    color_found = True
                    break
            if not color_found:
                colors.append(COLOR_MAP["default"])
    else:
        colors = [COLOR_MAP["default"]] * len(labels)

    # Determine shapes based on labels and SHAPE_MAP (only if show_shape is True)
    shapes = []
    if show_shape:
        for label in labels:
            shape_found = False
            for key in SHAPE_MAP:
                if key != "default" and key in label.lower():
                    shapes.append(SHAPE_MAP[key])
                    shape_found = True
                    break
            if not shape_found:
                shapes.append(SHAPE_MAP["default"])
    else:
        shapes = [SHAPE_MAP["default"]] * len(labels)

    # Plot error bars without markers
    plt.errorbar(
        difficulty_scores,
        faithfulness_scores,
        xerr=difficulty_ci,
        yerr=faithfulness_ci,
        fmt="none",
        ecolor="lightgray",
        capsize=5,
    )

    # Group data points by shape and plot each group
    unique_shapes = list(set(shapes))
    for shape in unique_shapes:
        # Get indices for this shape
        shape_indices = [i for i, s in enumerate(shapes) if s == shape]

        # Extract data for this shape
        shape_difficulty = [difficulty_scores[i] for i in shape_indices]
        shape_faithfulness = [faithfulness_scores[i] for i in shape_indices]
        shape_colors = [colors[i] for i in shape_indices]
        shape_sizes = [dot_sizes[i] for i in shape_indices]

        # Plot scatter points with variable size and varying colors/shapes
        plt.scatter(
            shape_difficulty,
            shape_faithfulness,
            s=shape_sizes,
            c=shape_colors,
            marker=shape,
            alpha=0.7,
        )

    plt.xlim(0, 1.01)
    plt.ylim(0, 1.05)

    if show_labels:
        for i, label in enumerate(labels):
            plt.annotate(
                label,
                (difficulty_scores[i], faithfulness_scores[i]),
                xytext=(5, 5),
                textcoords="offset points",
                fontsize=6,
            )

    plt.xlabel("Clue Difficulty")
    plt.ylabel("Faithfulness Score")
    plt.title(
        "Propensity for Faithfulness vs Difficulty", loc="left", pad=25, fontsize=25
    )
    plt.suptitle(
        f"{model} on {dataset}, 90% CI",
        y=0.90,
        fontsize=12,
        color="gray",
        style="italic",
    )
    ax = plt.axes(
        [0.8, 0.88, 0.1, 0.1], frameon=True
    )  # Change the numbers in this array to position your image [left, bottom, width, height])
    ax.imshow(image)
    ax.axis("off")

    plt.grid(True)
    plt.show()


def generate_taking_hints_graph(
    p_take_hints: List[float],
    labels: List[str],
    model: str,
    dataset: str,
    path: str | None = None,
) -> None:
    indices = np.arange(len(labels))
    width = 0.6

    took_hint = np.array(p_take_hints)
    did_not_take_hint = 1 - took_hint  # Will sum to 1 for each bar

    fig, ax = plt.subplots(figsize=(12, 6))

    ax.bar(indices, took_hint, width, label="Took Hint", color="#7fc97f")
    ax.bar(
        indices,
        did_not_take_hint,
        width,
        bottom=took_hint,
        label="Did Not Take Hint",
        color="#fdc086",
    )

    ax.set_ylabel("Proportion of Samples")
    ax.set_title(f"Hint-Taking for {model.split('/')[-1]} on {dataset}")
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
    dataset: str,
    path: str | None = None,
    show_labels: bool = False,
) -> None:
    plt.figure(figsize=(10, 6))

    image = plt.imread("assets/logo.png")
    plt.rcParams["font.family"] = "Montserrat"

    # Remove top and right spines
    ax = plt.gca()
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    plt.scatter(difficulty_scores, p_take_hints, marker="o", color="#f9a4a4")

    plt.xlim(0, 1.01)

    if show_labels:
        for i, label in enumerate(labels):
            plt.annotate(
                label,
                (difficulty_scores[i], p_take_hints[i]),
                xytext=(5, 5),
                textcoords="offset points",
                fontsize=6,
            )

    plt.xlabel("Difficulty Score")
    plt.ylabel("Proportion Taking Hints")
    plt.title("Hint-Taking vs Difficulty", loc="left", pad=25, fontsize=25)
    plt.suptitle(
        f"{model} on {dataset}",
        y=0.90,
        fontsize=12,
        color="gray",
        style="italic",
    )
    ax = plt.axes(
        [0.8, 0.88, 0.1, 0.1], frameon=True
    )  # Change the numbers in this array to position your image [left, bottom, width, height])
    ax.imshow(image)
    ax.axis("off")

    plt.grid(True)
    plt.show()


def generate_with_and_without_cot_difficulty_graph(
    reasoning_accuracy_scores: List[float],
    non_reasoning_accuracy_scores: List[float],
    labels: List[str],
    model: str,
    dataset: str,
    path: str | None = None,
) -> None:
    plt.figure(figsize=(10, 6))

    plt.scatter(reasoning_accuracy_scores, non_reasoning_accuracy_scores, alpha=0.6)

    # Add labels and title
    plt.xlabel("Reasoning Accuracy Score")
    plt.ylabel("Non-Reasoning Accuracy Score")
    plt.title(
        f"Reasoning vs Non-Reasoning Accuracy Scores for {model.split('/')[-1]} on {dataset}"
    )

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


def generate_boxplot(
    faithfulness_scores: List[float],
    difficulty_scores: List[float],
    boxplot_lower_threshold: float,
    boxplot_upper_threshold: float,
    model: str,
    dataset: str,
    path: str | None = None,
) -> None:
    # Prepare data for swarm plot
    data_points = []
    for score, difficulty in zip(faithfulness_scores, difficulty_scores):
        if difficulty <= float(boxplot_lower_threshold):
            data_points.append(
                {
                    "Faithfulness": score,
                    "Category": f"Difficulty <= {boxplot_lower_threshold}",
                }
            )
        elif difficulty >= float(boxplot_upper_threshold):
            data_points.append(
                {
                    "Faithfulness": score,
                    "Category": f"Difficulty >= {boxplot_upper_threshold}",
                }
            )

    # Convert to DataFrame
    df = pd.DataFrame(data_points)

    # Count samples for labels
    low_count = len(
        [
            d
            for d in data_points
            if "low" in d["Category"].lower() or "<=" in d["Category"]
        ]
    )
    high_count = len(
        [
            d
            for d in data_points
            if "high" in d["Category"].lower() or ">=" in d["Category"]
        ]
    )

    plt.figure(figsize=(8, 6))

    # Create boxplot using seaborn (without outliers since swarm plot shows all points)
    sns.boxplot(
        data=df,
        x="Category",
        y="Faithfulness",
        color="lightblue",
        boxprops=dict(alpha=0.5),
        whiskerprops=dict(color="darkblue"),
        capprops=dict(color="darkblue"),
        medianprops=dict(color="darkblue", linewidth=2),
        showfliers=False,  # Turn off outlier display since swarm plot shows all points
    )

    # Overlay swarm plot for individual points
    sns.swarmplot(
        data=df, x="Category", y="Faithfulness", color="#f9a4a4", size=4, alpha=0.8
    )

    # Update x-tick labels to include sample counts
    ax = plt.gca()
    current_labels = [t.get_text() for t in ax.get_xticklabels()]
    new_labels = []
    for label in current_labels:
        if "<=" in label:
            new_labels.append(f"{label}, n={low_count}")
        else:
            new_labels.append(f"{label}, n={high_count}")
    ax.set_xticklabels(new_labels)

    plt.ylabel("Faithfulness")
    plt.title(
        f"Distribution of Faithfulness Scores by Clue Difficulty for {model.split('/')[-1]} on {dataset}"
    )
    plt.ylim(0, 1)
    plt.grid(True, alpha=0.3)

    if path:
        plt.savefig(path)
    else:
        plt.show()


def generate_violin_plot(
    faithfulness_scores: List[float],
    difficulty_scores: List[float],
    boxplot_lower_threshold: float,
    boxplot_upper_threshold: float,
    model: str,
    dataset: str,
    path: str | None = None,
) -> None:
    # Prepare data for violin plot
    data_points = []
    for score, difficulty in zip(faithfulness_scores, difficulty_scores):
        if difficulty <= float(boxplot_lower_threshold):
            data_points.append(
                {
                    "Faithfulness": score,
                    "Category": f"Difficulty <= {boxplot_lower_threshold}",
                }
            )
        elif difficulty >= float(boxplot_upper_threshold):
            data_points.append(
                {
                    "Faithfulness": score,
                    "Category": f"Difficulty >= {boxplot_upper_threshold}",
                }
            )

    # Convert to DataFrame
    df = pd.DataFrame(data_points)

    # Count samples for labels
    low_count = len(
        [
            d
            for d in data_points
            if "low" in d["Category"].lower() or "<=" in d["Category"]
        ]
    )
    high_count = len(
        [
            d
            for d in data_points
            if "high" in d["Category"].lower() or ">=" in d["Category"]
        ]
    )

    plt.figure(figsize=(8, 6))

    # Create violin plot using seaborn
    sns.violinplot(
        data=df,
        x="Category",
        y="Faithfulness",
        color="#f9a4a4",
        alpha=0.5,
        bw_adjust=0.3,
    )

    # Overlay swarm plot for individual points
    sns.swarmplot(
        data=df, x="Category", y="Faithfulness", color="#f9a4a4", size=4, alpha=1
    )

    # Update x-tick labels to include sample counts
    ax = plt.gca()
    current_labels = [t.get_text() for t in ax.get_xticklabels()]
    new_labels = []
    for label in current_labels:
        if "<=" in label:
            new_labels.append(f"{label}, n={low_count}")
        else:
            new_labels.append(f"{label}, n={high_count}")
    ax.set_xticklabels(new_labels)

    plt.ylabel("Faithfulness")
    plt.title(
        f"Distribution of Faithfulness Scores by Clue Difficulty for {model.split('/')[-1]} on {dataset}"
    )
    plt.ylim(0, 1)
    plt.grid(True, alpha=0.3)

    if path:
        plt.savefig(path)
    else:
        plt.show()


def save_raw_data_to_json(
    config: EvalConfig,
    dataset_name: str,
    labels: List[str],
    reasoning_accuracies: List[float],
    non_reasoning_accuracies: List[float],
    difficulty_scores: List[float],
    difficulty_stderrs: List[float],
    faithfulness_scores: List[float],
    faithfulness_stderrs: List[float],
    take_hints_scores: List[float],
    samples: List[int],
    path: str,
) -> None:
    data = {
        "metadata": {
            "model": config.model,
            "base_model": config.base_model,
            "testing_scheme": config.testing_scheme,
            "temperature": config.temperature,
            "dataset": dataset_name,
        },
        "labels": labels,
        "reasoning_accuracies": reasoning_accuracies,
        "non_reasoning_accuracies": non_reasoning_accuracies,
        "difficulty_scores": difficulty_scores,
        "difficulty_stderrs": difficulty_stderrs,
        "faithfulness_scores": faithfulness_scores,
        "faithfulness_stderrs": faithfulness_stderrs,
        "take_hints_scores": take_hints_scores,
        "samples": samples,
    }
    with open(path, "w") as f:
        json.dump(data, f)

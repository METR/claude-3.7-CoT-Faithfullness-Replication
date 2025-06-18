import os
import json
from pathlib import Path
from typing import Any

from graph_utils import (
    GraphMetadata,
    generate_boxplot,
    generate_propensity_graph,
    generate_taking_hints_v_difficulty_graph,
    generate_violin_plot,
)

# Directory setup
RESULTS_DIR = Path(__file__).parent / "results"
GRAPH_DIR = Path(__file__).parent / "graphs"
GRAPH_DIR.mkdir(exist_ok=True)

# Graphing parameters
DATASET_NAME = "metr/hard-math"
BOXPLOT_LOWER_THRESHOLD = 0.2
BOXPLOT_UPPER_THRESHOLD = 0.8
HINT_TAKING_THRESHOLD = 0.1
SHOW_LABELS = False

# Helper to get all result json files
def find_result_files():
    for metric_dir in RESULTS_DIR.iterdir():
        if metric_dir.is_dir():
            for file in metric_dir.glob("*.json"):
                yield metric_dir.name, file

# Helper to extract correct keys from result file
def extract_data(data: dict[str, Any]) -> dict[str, Any]:
    # Try new metric naming first
    if "metric_scores" in data:
        return {
            "labels": data["labels"],
            "reasoning_accuracies": data["reasoning_accuracies"],
            "non_reasoning_accuracies": data["non_reasoning_accuracies"],
            "difficulty_scores": data["difficulty_scores"],
            "difficulty_stderrs": data["difficulty_stderrs"],
            "faithfulness_scores": data["metric_scores"],
            "faithfulness_stderrs": data["metric_stderrs"],
            "take_hints_scores": data["take_hints_scores"],
            "samples": data["samples"],
        }
    # Fallback to old naming
    elif "faithfulness_scores" in data:
        return {
            "labels": data["labels"],
            "reasoning_accuracies": data["reasoning_accuracies"],
            "non_reasoning_accuracies": data["non_reasoning_accuracies"],
            "difficulty_scores": data["difficulty_scores"],
            "difficulty_stderrs": data["difficulty_stderrs"],
            "faithfulness_scores": data["faithfulness_scores"],
            "faithfulness_stderrs": data["faithfulness_stderrs"],
            "take_hints_scores": data["take_hints_scores"],
            "samples": data["samples"],
        }
    else:
        raise ValueError("Result file missing expected keys.")

# Main batch graphing
for metric, file_path in find_result_files():
    try:
        with open(file_path, "r") as f:
            data = json.load(f)
        extracted = extract_data(data)
    except Exception as e:
        print(f"Skipping {file_path}: {e}")
        continue

    # Metadata
    metadata = None
    model = ""
    if "metadata" in data:
        model = data["metadata"].get("model", "")
        metadata = GraphMetadata(
            threshold=HINT_TAKING_THRESHOLD,
            faithfulness=data["metadata"].get("score_faithfulness", metric == "faithfulness"),
            question_prompt=data["metadata"].get("question_prompt", ""),
            judge_prompt=data["metadata"].get("judge_prompt", ""),
        )

    # Output directory for this result
    out_dir = GRAPH_DIR / metric / file_path.stem
    out_dir.mkdir(parents=True, exist_ok=True)

    # Filter by hint taking threshold
    from graph import filter_lists_by_threshold
    (
        take_hints_scores,
        labels,
        reasoning_accuracies,
        non_reasoning_accuracies,
        difficulty_scores,
        difficulty_stderrs,
        faithfulness_scores,
        faithfulness_stderrs,
        samples,
    ) = filter_lists_by_threshold(
        extracted["take_hints_scores"],
        extracted["labels"],
        extracted["reasoning_accuracies"],
        extracted["non_reasoning_accuracies"],
        extracted["difficulty_scores"],
        extracted["difficulty_stderrs"],
        extracted["faithfulness_scores"],
        extracted["faithfulness_stderrs"],
        extracted["samples"],
        threshold=HINT_TAKING_THRESHOLD,
    )

    # Graphs
    generate_taking_hints_v_difficulty_graph(
        take_hints_scores,
        difficulty_scores,
        metadata,
        labels=labels,
        model=model,
        dataset=DATASET_NAME,
        show_labels=SHOW_LABELS,
        path=str(out_dir / "taking_hints_v_difficulty.png"),
    )

    generate_propensity_graph(
        faithfulness_scores,
        faithfulness_stderrs,
        difficulty_scores,
        difficulty_stderrs,
        metadata,
        labels=labels,
        take_hints_scores=take_hints_scores,
        samples=samples,
        model=model,
        dataset=DATASET_NAME,
        show_labels=SHOW_LABELS,
        show_color=True,
        show_shape=False,
        path=str(out_dir / "propensity.png"),
    )

    generate_boxplot(
        faithfulness_scores,
        difficulty_scores,
        metadata,
        BOXPLOT_LOWER_THRESHOLD,
        BOXPLOT_UPPER_THRESHOLD,
        model,
        DATASET_NAME,
        path=str(out_dir / "boxplot.png"),
    )

    generate_violin_plot(
        faithfulness_scores,
        difficulty_scores,
        BOXPLOT_LOWER_THRESHOLD,
        BOXPLOT_UPPER_THRESHOLD,
        metadata,
        model,
        DATASET_NAME,
        path=str(out_dir / "violin_plot.png"),
    )

    print(f"Graphed {file_path} -> {out_dir}") 
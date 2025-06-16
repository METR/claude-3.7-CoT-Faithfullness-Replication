import argparse
import json
import os

from graph_utils import (
    generate_boxplot,
    generate_propensity_graph,
    generate_taking_hints_graph,
    generate_taking_hints_v_difficulty_graph,
    generate_violin_plot,
)


def filter_lists_by_threshold(filter_list, *other_lists, threshold=0.1):
    """
    Filter multiple lists based on a threshold applied to one list.

    Args:
        filter_list: The list to apply the threshold condition to
        *other_lists: Variable number of other lists to filter correspondingly
        threshold: Values below this in filter_list will be removed (default 0.1)

    Returns:
        Tuple of filtered lists (filter_list, *other_lists)
    """
    # Create mask for values >= threshold
    filtered_data = [
        (filter_val, *other_vals)
        for filter_val, *other_vals in zip(filter_list, *other_lists)
        if filter_val >= threshold
    ]

    # Unpack back into separate lists
    if filtered_data:
        return tuple(zip(*filtered_data))
    else:
        # Handle empty result case
        return tuple([] for _ in range(len(other_lists) + 1))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--model",
        type=str,
        help="Model to use for evaluation",
        default="anthropic/claude-3-7-sonnet-latest",
    )
    parser.add_argument(
        "--hint_taking_threshold",
        type=float,
        help="Threshold for hint taking",
        default=0.1,
    )
    parser.add_argument(
        "--show_labels",
        type=bool,
        help="Whether to show labels on the graph",
        default=False,
    )
    parser.add_argument(
        "--raw_data_path",
        type=str,
        help="Path to raw data",
    )
    parser.add_argument(
        "--alias",
        type=str,
        help="Alias for the graph",
        default="",
    )
    args = parser.parse_args()

    RAW_DATA_PATH = args.raw_data_path
    MODEL = args.model
    HINT_TAKING_THRESHOLD = args.hint_taking_threshold
    SHOW_LABELS = args.show_labels
    dataset_name = "metr/hard-math"
    BOXPLOT_LOWER_THRESHOLD = 0.2
    BOXPLOT_UPPER_THRESHOLD = 0.8
    GRAPH_BASE_DIRECTORY = f"./results/graphs/{args.model.split('/')[-1]}_thresh{args.hint_taking_threshold}_{args.alias}"
    if not os.path.exists(GRAPH_BASE_DIRECTORY):
        os.makedirs(GRAPH_BASE_DIRECTORY)

    with open(RAW_DATA_PATH, "r") as f:
        data = json.load(f)

    if "metadata" in data:
        MODEL = f"{data['metadata']['model']}_{data['metadata']['question_prompt'].split('/')[-1]}_{data['metadata']['judge_prompt'].split('/')[-1]}_faithful-{data['metadata']['score_faithfulness']}"

    labels = data["labels"]
    reasoning_accuracies = data["reasoning_accuracies"]
    non_reasoning_accuracies = data["non_reasoning_accuracies"]
    difficulty_scores = data["difficulty_scores"]
    difficulty_stderrs = data["difficulty_stderrs"]
    faithfulness_scores = data["faithfulness_scores"]
    faithfulness_stderrs = data["faithfulness_stderrs"]
    take_hints_scores = data["take_hints_scores"]
    samples = data["samples"]

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
        take_hints_scores,
        labels,
        reasoning_accuracies,
        non_reasoning_accuracies,
        difficulty_scores,
        difficulty_stderrs,
        faithfulness_scores,
        faithfulness_stderrs,
        samples,
        threshold=HINT_TAKING_THRESHOLD,
    )

    generate_taking_hints_graph(
        take_hints_scores,
        labels=labels,
        model=MODEL,
        dataset=dataset_name,
        path=f"{GRAPH_BASE_DIRECTORY}/taking_hints.png",
    )

    generate_taking_hints_v_difficulty_graph(
        take_hints_scores,
        difficulty_scores,
        labels=labels,
        model=MODEL,
        dataset=dataset_name,
        show_labels=SHOW_LABELS,
        path=f"{GRAPH_BASE_DIRECTORY}/taking_hints_v_difficulty.png",
    )

    generate_propensity_graph(
        faithfulness_scores,
        faithfulness_stderrs,
        difficulty_scores,
        difficulty_stderrs,
        labels=labels,
        take_hints_scores=take_hints_scores,
        samples=samples,
        model=MODEL,
        dataset=dataset_name,
        show_labels=SHOW_LABELS,
        show_color=True,
        show_shape=False,
        path=f"{GRAPH_BASE_DIRECTORY}/propensity.png",
    )

    generate_boxplot(
        faithfulness_scores,
        difficulty_scores,
        BOXPLOT_LOWER_THRESHOLD,
        BOXPLOT_UPPER_THRESHOLD,
        MODEL,
        dataset_name,
        path=f"{GRAPH_BASE_DIRECTORY}/boxplot.png",
    )

    generate_violin_plot(
        faithfulness_scores,
        difficulty_scores,
        BOXPLOT_LOWER_THRESHOLD,
        BOXPLOT_UPPER_THRESHOLD,
        MODEL,
        dataset_name,
        path=f"{GRAPH_BASE_DIRECTORY}/violin_plot.png",
    )

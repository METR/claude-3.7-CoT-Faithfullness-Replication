from datetime import datetime
import json
from llm_faithfulness import get_faithfulness_score
from behaviors import ALTERED_ORIGINAL_BEHAVIORS
from clue_difficulty import TestingScheme
import matplotlib.pyplot as plt
import numpy as np

MODEL = "anthropic/claude-3-7-sonnet-latest"
MAX_CONNECTIONS = 3
TESTING_SCHEME = TestingScheme.BASE
TEMPERATURE = 1
TOP_LEVEL_LOG_DIR: str = f"./logs/{datetime.now().strftime('%Y%m%d-%H%M%S')}-{MODEL.replace('/', '-')}-{TESTING_SCHEME.value}/"
LIMIT = 200


def graph_results(results: dict):
    # Data from the variables
    setups = [
        "Original Setup Replication",
        "Explicit Signaling",
        "Format Transformation",
        "Incentive Modification",
    ]
    clusters = ["Metadata", "Reward Hacking"]

    # Define the cluster keys
    cluster_keys = {
        "Metadata": [
            "metadata",
            "metadata_with_hint",
            "metadata_language",
            "metadata_anti_cheating",
        ],
        "Reward Hacking": [
            "reward_hacking",
            "reward_hacking_with_hint",
            "reward_hacking_language",
            "reward_hacking_anti_cheating",
        ],
    }

    # Organize data by cluster
    cluster_values = {}
    cluster_errors = {}

    for cluster, keys in cluster_keys.items():
        cluster_values[cluster] = [results[key]["p_acknowledged_clue"] for key in keys]
        cluster_errors[cluster] = [results[key]["faithfulness_stderr"] for key in keys]

    # Calculate 95% confidence intervals (1.96 * stderr)
    metadata_ci = [1.96 * stderr for stderr in cluster_errors["Metadata"]]
    reward_hacking_ci = [1.96 * stderr for stderr in cluster_errors["Reward Hacking"]]

    # Set up the figure and axis
    fig, ax = plt.subplots(figsize=(12, 8))

    # Define the width of the bars and positions
    bar_width = 0.15
    x = np.arange(len(clusters))

    # Define colors for each setup
    colors = ["#cdcdcd", "#dd8466", "#bc3455", "#236894"]

    # Create the bars for each setup across both clusters
    for i, setup in enumerate(setups):
        values = [cluster_values["Metadata"][i], cluster_values["Reward Hacking"][i]]
        errors = [metadata_ci[i], reward_hacking_ci[i]]
        bars = ax.bar(
            position := x + (i - 2) * bar_width,
            values,
            bar_width,
            label=setup,
            color=colors[i],
            yerr=errors,
            capsize=5,
            alpha=1,
        )

        # Add value labels on top of each bar
        for _, bar in enumerate(bars):
            height = bar.get_height()
            ax.annotate(
                f"{height:.3f}",
                xy=(bar.get_x() + bar.get_width() / 2, height),
                xytext=(0, 3),  # 3 points vertical offset
                textcoords="offset points",
                ha="center",
                va="bottom",
                fontsize=12,
            )

    # Add labels, title, and legend
    ax.set_ylabel("Chain of Thought Faithfulness (Higher Better)", fontsize=16)
    ax.set_title("Faithfulness by Setup Type with 95% CI", fontsize=16)
    ax.set_xticks(x)
    ax.set_xticklabels(clusters)
    ax.legend(title="Setup Type", loc="upper left")

    # Add grid for better readability
    ax.grid(axis="y", linestyle="--", alpha=0.7)

    # Remove top and right spines for cleaner look
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    # Set y-axis limits with some padding
    max_value = max(
        max(cluster_values["Metadata"]), max(cluster_values["Reward Hacking"])
    )
    ax.set_ylim(0, max_value * 1.2)

    plt.tight_layout()
    plt.show()


if __name__ == "__main__":
    faithfulness_results = {}
    for behavior in ALTERED_ORIGINAL_BEHAVIORS:
        (
            p_acknowledged_clue,
            p_take_hints,
            faithfulness_stderr,
            completed_samples,
        ) = get_faithfulness_score(
            behavior,
            model=MODEL,
            max_connections=MAX_CONNECTIONS,
            display="full",
            log_dir=TOP_LEVEL_LOG_DIR,
            temperature=TEMPERATURE,
            function_dict=ALTERED_ORIGINAL_BEHAVIORS,
        )
        faithfulness_results[behavior.value] = {
            "p_acknowledged_clue": p_acknowledged_clue,
            "faithfulness_stderr": faithfulness_stderr,
            "completed_samples": completed_samples,
        }

    with open("./results/robustness_results.json", "w") as f:
        json.dump(faithfulness_results, f)

    graph_results(faithfulness_results)

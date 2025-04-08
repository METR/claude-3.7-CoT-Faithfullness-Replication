from inspect_ai import eval
from llm_faithfulness import llm_faithfulness
from behaviors import Behavior
import matplotlib.pyplot as plt
import math

USE_ALL_BEHAVIORS = True
LIMIT = 100
NUM_BEHAVIOR_LIMIT = 6
MAX_CONNECTIONS = 100
MODEL = "together/Qwen/QwQ-32B"


def main():
    num_easy_cases = 3

    if USE_ALL_BEHAVIORS:
        if NUM_BEHAVIOR_LIMIT is not None:
            cases = [c for c in Behavior][:NUM_BEHAVIOR_LIMIT]
        else:
            cases = [c for c in Behavior]
    else:
        cases = [
            Behavior.URL,
            Behavior.METADATA,
            Behavior.LOWERCASE,
        ]

    delta_correct = []
    acknowledged_clue = []

    for case in cases:
        res = eval(
            llm_faithfulness(clue=case.value, limit=LIMIT),
            model=MODEL,
            max_connections=MAX_CONNECTIONS,
        )
        delta_correct.append(
            res[0].results.scores[0].metrics["delta_correctness"].value
        )
        acknowledged_clue.append(
            res[0].results.scores[0].metrics["acknowledged_clue"].value
        )

    print(delta_correct)
    print(acknowledged_clue)

    # Calculate the stacked values
    acknowledged_impact = [d * a for d, a in zip(delta_correct, acknowledged_clue)]
    unacknowledged_impact = [
        d * (1 - a) for d, a in zip(delta_correct, acknowledged_clue)
    ]

    # Create the stacked bar chart
    fig, ax = plt.subplots(figsize=(10, 8))  # Made taller to accommodate labels

    # Plot the stacked bars
    ax.bar(
        [c.value for c in cases], unacknowledged_impact, label="Unacknowledged Impact"
    )
    ax.bar(
        [c.value for c in cases],
        acknowledged_impact,
        bottom=unacknowledged_impact,
        label="Acknowledged Impact",
    )

    # Add horizontal dotted line at y=8
    ax.axhline(
        y=math.floor(LIMIT * 0.04), color="red", linestyle=":", label="Threshold"
    )

    # Customize the plot
    plt.xticks(rotation=45, ha="right")
    plt.xlabel("Behavior Type")
    plt.ylabel("Impact")
    plt.title("Impact of Different Behaviors: Acknowledged vs Unacknowledged")
    plt.legend()

    # Add difficulty labels
    # Add text labels for case groups using text() with transform
    ax.text(
        (num_easy_cases - 1) / 2,  # Center of easy cases
        ax.get_ylim()[0],  # Bottom of plot
        "Easy Cases",
        ha="center",
        va="top",
        transform=ax.get_xaxis_transform(),
        bbox=dict(facecolor="white", edgecolor="none", alpha=0.7),
    )
    ax.text(
        num_easy_cases + (len(cases) - num_easy_cases) / 2,  # Center of hard cases
        ax.get_ylim()[0],  # Bottom of plot
        "Hard Cases",
        ha="center",
        va="top",
        transform=ax.get_xaxis_transform(),
        bbox=dict(facecolor="white", edgecolor="none", alpha=0.7),
    )

    # Add vertical separator between easy and hard cases
    ax.axvline(x=num_easy_cases - 0.5, color="gray", linestyle="--", alpha=0.5)

    plt.tight_layout()
    plt.subplots_adjust(bottom=0.2)  # Make room for the labels

    # Show the plot
    plt.show()


if __name__ == "__main__":
    main()

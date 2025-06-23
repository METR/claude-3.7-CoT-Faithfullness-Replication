"""
Bar graph for Anthropic replication values:

Reward Hacking: 0.00
Unethical Information: 0.57
Syncophantic: 0.67
"""

import matplotlib.pyplot as plt
import numpy as np


def generate_anthropic_replication_bar_graph(path: str | None = None) -> None:
    """
    Generate a bar graph for the three anthropic replication values.

    Args:
        path: Optional path to save the graph to. If None, displays the graph instead.
    """
    # Data
    categories = ["Reward Hacking", "Unethical Information", "Sycophantic"]
    values = [0.00, 0.57, 0.67]

    # Color mapping from the existing style
    colors = ["#f9a4a4", "#fdc086", "#7fc97f"]  # Light Red, Light Orange, Light Green

    # Create figure with same dimensions as other graphs
    plt.figure(figsize=(10, 6))

    # Load and display logo (exactly matching existing graphs)
    image = plt.imread("assets/logo.png")
    plt.rcParams["font.family"] = "Montserrat"

    # Remove top and right spines (matching existing style)
    ax = plt.gca()
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    # Create bar chart
    indices = np.arange(len(categories))
    width = 0.6

    bars = ax.bar(indices, values, width, color=colors, alpha=0.8)

    # Add value labels on top of bars
    for bar, value in zip(bars, values):
        height = bar.get_height()
        ax.text(
            bar.get_x() + bar.get_width() / 2.0,
            height + 0.01,
            f"{value:.2f}",
            ha="center",
            va="bottom",
            fontsize=12,
            fontweight="bold",
        )

    # Styling to match existing graphs exactly
    ax.set_ylabel("Score", fontsize=12)
    ax.set_xticks(indices)
    ax.set_xticklabels(categories, rotation=0, ha="center", fontsize=11)

    # Set y-axis limits to show full range
    ax.set_ylim(0, max(values) * 1.15)

    # Add grid (matching existing style)
    ax.grid(True, alpha=0.3, axis="y")

    # Title and subtitle formatting (exactly matching existing graphs)
    plt.title("METR: Anthropic Replication Results", loc="left", pad=35, fontsize=25)
    plt.suptitle(
        "Claude 3.7 Sonnet on GQPA Diamond",
        x=0.065,
        y=0.85,
        fontsize=12,
        color="gray",
        style="italic",
        ha="left",
    )

    # Add logo in top right corner (moved down)
    ax_logo = plt.axes(
        [0.8, 0.85, 0.1, 0.1], frameon=True
    )  # [left, bottom, width, height]
    ax_logo.imshow(image)
    ax_logo.axis("off")

    plt.tight_layout()

    if path:
        plt.savefig(path, dpi=300, bbox_inches="tight")
        print(f"Graph saved to: {path}")
    else:
        plt.show()


if __name__ == "__main__":
    # Generate and save the graph
    generate_anthropic_replication_bar_graph("anthropic_replication_results.png")

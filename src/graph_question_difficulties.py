import argparse
import datetime
import matplotlib.pyplot as plt
import pandas as pd


def graph_question_difficulties(input_path: str, model: str, output_path: str | None):
    if output_path is None:
        output_path = (
            f"results/difficulty_graphs/{input_path.split('/')[-1].split('.')[0]}"
        )

    df = pd.read_csv(input_path)

    # Create figure with extra space on right for legend
    plt.figure(figsize=(12, 8.5))

    # Create main plotting area that leaves room on right
    ax = plt.axes([0.1, 0.1, 0.8, 0.75])

    # Remove top and right spines
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    # Set font
    plt.rcParams["font.family"] = "Montserrat"

    # Create histogram of accuracies (1-difficulty)
    plt.hist(
        1 - df["difficulty_score"],
        bins=[0.0, 0.19999, 0.39999, 0.59999, 0.79999, 1.0],
        edgecolor="black",
        color="#485F52",
        alpha=0.7,
    )

    plt.xlabel("Average Accuracy", fontsize=16)
    plt.ylabel("Number of Questions", fontsize=16)

    # Add main title
    plt.title(
        "Distribution of Question Accuracies",
        loc="left",
        pad=35,
        fontsize=25,
    )

    # Add subtitle
    ax = plt.gca()
    ax.text(
        0,
        1.03,
        f"Based on {len(df)} questions on {model}",
        transform=ax.transAxes,
        fontsize=14,
        color="gray",
        style="italic",
        horizontalalignment="left",
    )

    # Add logo
    image = plt.imread("assets/logo.png")
    ax = plt.axes([0.812, 0.862, 0.12, 0.12], frameon=True)
    ax.imshow(image)
    ax.axis("off")

    plt.grid(True)

    if output_path:
        plt.savefig(output_path)
    else:
        plt.show()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input_path", type=str, required=True)
    parser.add_argument("--model", type=str, required=True)
    parser.add_argument("--output_path", type=str, required=False, default=None)
    args = parser.parse_args()

    graph_question_difficulties(args.input_path, args.model, args.output_path)

import datetime
import json
import os
import time
from behaviors import FUNCTION_DICT
import matplotlib.pyplot as plt
from clue_difficulty import get_clue_difficulty, TestingScheme
from llm_faithfulness import get_faithfulness_score
from tqdm import tqdm
import argparse

parser = argparse.ArgumentParser()
parser.add_argument(
    "--model",
    type=str,
    help="Model to use for evaluation",
    default="together/Qwen/QwQ-32B",
)
parser.add_argument(
    "--base_model",
    type=str,
    help="Base model to compare against",
    default="together/Qwen/QwQ-32B",
)
args = parser.parse_args()

MODEL = args.model
BASE_MODEL = args.base_model
TESTING_SCHEME = TestingScheme.BASE

start_timestamp = (
    datetime.datetime.now(datetime.timezone.utc)
    .strftime("%Y-%m-%dT%H-%M-%S")
    .replace("+", "-")
)


def save_scores(**kwargs):
    data = {
        "model": MODEL,
        "base_model": BASE_MODEL,
        "testing_scheme": TESTING_SCHEME.value,
        **kwargs,
    }

    if not os.path.exists("scores"):
        os.makedirs("scores")
    with open(f"scores/{start_timestamp}.jsonl", "a") as f:
        f.write(json.dumps(data) + "\n")


if __name__ == "__main__":
    faithfulness_scores = []
    faithfulness_stderr_scores = []
    cot_difficulty_scores = []
    cot_difficulty_stderr_scores = []

    labels = [x.value for x in FUNCTION_DICT.keys()]
    cases = list(FUNCTION_DICT.keys())

    for behavior in tqdm(cases):
        (
            cot_difficulty,
            cot_difficulty_stderr,
            reasoning_accuracy,
            non_reasoning_accuracy,
        ) = get_clue_difficulty(
            behavior,
            reasoning_model=MODEL,
            non_reasoning_model=BASE_MODEL,
            display="full",
            epochs=10,
            testing_scheme=TESTING_SCHEME,
        )
        (
            faithfulness_score,
            faithfulness_stderr,
            delta_correctness,
            completed_samples,
            ic_count,
        ) = get_faithfulness_score(
            behavior,
            model=MODEL,
            max_connections=100,
            limit=100,
            display="none",
        )
        save_scores(
            behavior=behavior.value,
            cot_difficulty=cot_difficulty,
            cot_difficulty_stderr=cot_difficulty_stderr,
            reasoning_accuracy=reasoning_accuracy,
            non_reasoning_accuracy=non_reasoning_accuracy,
            faithfulness_score=faithfulness_score,
            faithfulness_stderr=faithfulness_stderr,
            delta_correctness=delta_correctness,
            completed_samples=completed_samples,
            ic_count=ic_count,
        )

        faithfulness_scores.append(faithfulness_score)
        faithfulness_stderr_scores.append(faithfulness_stderr)
        cot_difficulty_scores.append(cot_difficulty)
        cot_difficulty_stderr_scores.append(cot_difficulty_stderr)
    # plot the scores

    plt.figure(figsize=(10, 6))
    # Plot all points except the last one
    plt.errorbar(
        cot_difficulty_scores[:-1],
        faithfulness_scores[:-1],
        xerr=cot_difficulty_stderr_scores[:-1],
        yerr=faithfulness_stderr_scores[:-1],
        fmt="o",
        ecolor="gray",
        capsize=5,
    )

    # Plot the last point in red
    plt.errorbar(
        cot_difficulty_scores[-1:],
        faithfulness_scores[-1:],
        xerr=cot_difficulty_stderr_scores[-1:],
        yerr=faithfulness_stderr_scores[-1:],
        fmt="ro",
        ecolor="gray",
        capsize=5,
    )

    # Add labels to each point
    # for i, label in enumerate(cases):
    #     plt.annotate(
    #         label.value,
    #         (cot_difficulty_scores[i], faithfulness_scores[i]),
    #         xytext=(5, 5),
    #         textcoords="offset points",
    #     )

    plt.xlabel("Chain of Thought Difficulty")
    plt.ylabel("Faithfulness Score")
    plt.title(
        f"Faithfulness vs Chain of Thought Difficulty by Behavior for {MODEL} with {TESTING_SCHEME} testing scheme"
    )
    plt.grid(True)
    plt.show()

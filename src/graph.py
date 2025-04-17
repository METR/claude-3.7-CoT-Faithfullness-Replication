from behaviors import FUNCTION_DICT
import matplotlib.pyplot as plt
from clue_difficulty import get_clue_difficulty
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
    default="openai-api/nebius/Qwen/Qwen2.5-32B-Instruct",
)
args = parser.parse_args()

MODEL = args.model
BASE_MODEL = args.base_model

if __name__ == "__main__":
    faithfulness_scores = []
    cot_difficulty_scores = []
    cot_difficulty_stderr_scores = []
    labels = [x.value for x in FUNCTION_DICT.keys()]
    cases = list(FUNCTION_DICT.keys())

    for behavior in tqdm(cases):
        cot_difficulty, cot_difficulty_stderr = get_clue_difficulty(
            behavior,
            reasoning_model=MODEL,
            non_reasoning_model=BASE_MODEL,
        )
        faithfulness_score = get_faithfulness_score(
            behavior,
            model=MODEL,
            max_connections=70,
        )
        faithfulness_scores.append(faithfulness_score)
        cot_difficulty_scores.append(cot_difficulty)
        cot_difficulty_stderr_scores.append(cot_difficulty_stderr)
    # plot the scores
    plt.figure(figsize=(10, 6))
    plt.errorbar(
        cot_difficulty_scores,
        faithfulness_scores,
        xerr=cot_difficulty_stderr_scores,
        fmt="o",
        ecolor="gray",
        capsize=5,
    )

    # Add labels to each point
    for i, label in enumerate(cases):
        plt.annotate(
            label.value,
            (cot_difficulty_scores[i], faithfulness_scores[i]),
            xytext=(5, 5),
            textcoords="offset points",
        )

    plt.xlabel("Chain of Thought Difficulty")
    plt.ylabel("Faithfulness Score")
    plt.title(f"Faithfulness vs Chain of Thought Difficulty by Behavior for {MODEL}")
    plt.grid(True)
    plt.show()

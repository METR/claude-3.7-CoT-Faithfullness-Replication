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
    default="openai-api/nebius/Qwen/Qwen2.5-32B-Instruct",
)
args = parser.parse_args()

MODEL = args.model
BASE_MODEL = args.base_model
TESTING_SCHEME = TestingScheme.RL_DOTS

if __name__ == "__main__":
    faithfulness_scores = []
    faithfulness_stderr_scores = []
    cot_difficulty_scores = []
    cot_difficulty_stderr_scores = []

    labels = [x.value for x in FUNCTION_DICT.keys()]
    cases = list(FUNCTION_DICT.keys())

    for behavior in tqdm(cases):
        cot_difficulty, cot_difficulty_stderr = get_clue_difficulty(
            behavior,
            reasoning_model="openai-api/hf/tgi",
            non_reasoning_model=BASE_MODEL,
            display="full",
            epochs=10,
            testing_scheme=TESTING_SCHEME,
        )
        faithfulness_score, faithfulness_stderr = get_faithfulness_score(
            behavior,
            model=MODEL,
            max_connections=100,
            limit=200,
            display="none",
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

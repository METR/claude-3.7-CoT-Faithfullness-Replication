from behaviors import FUNCTION_DICT
import matplotlib.pyplot as plt
from clue_difficulty import get_clue_difficulty
from llm_faithfulness import get_faithfulness_score

if __name__ == "__main__":
    faithfulness_scores = []
    cot_difficulty_scores = []
    labels = [x.value for x in FUNCTION_DICT.keys()]

    for behavior in FUNCTION_DICT.keys():
        cot_difficulty = get_clue_difficulty(
            behavior,
            reasoning_model="together/Qwen/QwQ-32B",
            non_reasoning_model="together/Qwen/Qwen2.5-72B-Instruct-Turbo",
        )
        faithfulness_score = get_faithfulness_score(
            behavior,
            model="together/Qwen/QwQ-32B",
        )
        faithfulness_scores.append(faithfulness_score)
        cot_difficulty_scores.append(cot_difficulty)

    # plot the scores
    plt.figure(figsize=(10, 6))
    plt.scatter(cot_difficulty_scores, faithfulness_scores)

    # Add labels to each point
    for i, label in enumerate(labels):
        plt.annotate(
            label,
            (cot_difficulty_scores[i], faithfulness_scores[i]),
            xytext=(5, 5),
            textcoords="offset points",
        )

    plt.xlabel("Chain of Thought Difficulty")
    plt.ylabel("Faithfulness Score")
    plt.title("Faithfulness vs Chain of Thought Difficulty by Behavior")
    plt.grid(True)
    plt.show()

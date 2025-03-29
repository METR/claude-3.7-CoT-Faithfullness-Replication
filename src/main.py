from inspect_ai import eval
from llm_faithfulness import llm_faithfulness
import matplotlib.pyplot as plt
from mmlu import mmlu
from gpqa import gpqa

"""
TODO:
- [ ] Make this a streamlined script to run evals
"""

"""
This script is used to run evals on the model. 

"""


def main():
    # ok so what i want is on the x-axis i want the success rate of the model on the raw set (corollary for hardness)
    # on the y-axis i want the faithfullness score of the model on the raw set
    test_cases: list[str] = [
        "mmlu/professional_law",
        "mmlu/formal_logic",
        "mmlu/econometrics",
        "gpqa/",
    ]

    scores = []
    faithfullness_scores = []

    for subject in test_cases:
        if "mmlu" in subject:
            res = eval(
                mmlu(subject=subject.split("/")[1], limit=50),
                model="together/Qwen/QwQ-32B",
            )
        elif "gpqa" in subject:
            res = eval(
                gpqa(subject=subject.split("/")[1], limit=50),
                model="together/Qwen/QwQ-32B",
            )
        scores.append(res[0].results.scores[0].metrics["accuracy"].value)

    for subject in test_cases:
        res = eval(
            llm_faithfulness(clue="reward_hacking", subject=subject, limit=50),
            model="together/Qwen/QwQ-32B",
        )
        faithfullness_scores.append(
            res[0].results.scores[0].metrics["acknowledged_clue"].value
        )

    print(scores)
    print(faithfullness_scores)

    plt.scatter(scores, faithfullness_scores)
    for i, txt in enumerate(test_cases):
        plt.annotate(txt, (scores[i], faithfullness_scores[i]))
    plt.xlabel("Success Rate")
    plt.ylabel("Faithfullness Score")
    plt.title("Faithfullness vs Difficulty (higher is easier)")
    plt.show()


if __name__ == "__main__":
    main()

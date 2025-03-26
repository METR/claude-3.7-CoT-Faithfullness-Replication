from inspect_ai import eval
from llm_faithfulness import llm_faithfulness
import matplotlib.pyplot as plt
from mmlu import mmlu

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
        "abstract_algebra",
        "professional_law",
        "professional_accounting",
        "jurisprudence",
        "professional_psychology",
        "college_medicine",
    ]

    scores = []
    faithfullness_scores = []

    for subject in test_cases:
        res = eval(
            mmlu(subject=subject, limit=50),
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
    plt.xlabel("Success Rate")
    plt.ylabel("Faithfullness Score")
    plt.title("Faithfullness vs Difficulty (higher is easier)")
    plt.show()


if __name__ == "__main__":
    main()

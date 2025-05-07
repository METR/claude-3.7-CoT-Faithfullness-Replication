from inspect_ai import eval
from inspect_ai import Task, task
from inspect_ai.dataset import csv_dataset
from inspect_ai.solver import Solver, solver, TaskState, Generate
from inspect_ai.model import CachePolicy, GenerateConfig
from inspect_ai.scorer import choice
from prompt_utils import SINGLE_ANSWER_TEMPLATE
from answer_utils import set_choices_based_on_generated_response, record_to_sample
import re
from prompt_utils import prompt
from inspect_ai.util import DisplayType
from os import path
from typing import Dict, List
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt


@task
def gpqa_diamond(
    epochs: int = 10,
    temperature: float = 0.6,
    limit: int = 100,
) -> Task:
    dataset = csv_dataset(
        auto_id=True,
        shuffle=False,
        csv_file="https://openaipublic.blob.core.windows.net/simple-evals/gpqa_diamond.csv",
        sample_fields=record_to_sample,
        shuffle_choices=True,
        limit=limit,
    )

    reasoning_tokens = 30_000
    max_tokens = 32768

    return Task(
        dataset=dataset,
        solver=multiple_choice(),
        scorer=choice(),
        config=GenerateConfig(
            temperature=temperature,
            reasoning_tokens=reasoning_tokens,
            max_tokens=max_tokens,
        ),
        epochs=epochs,
    )


@solver
def multiple_choice() -> Solver:
    async def solve(state: TaskState, generate: Generate) -> TaskState:
        state.user_prompt.text = prompt(
            question=state.user_prompt.text,
            choices=state.choices,
            clue="",
            template=SINGLE_ANSWER_TEMPLATE,
        )

        state = await generate(state, cache=CachePolicy(expiry=None))

        answers = re.search(
            r"(?i)ANSWER:\s*([A-Za-z]+)",
            state.output.completion,
        )

        if answers and answers.group(1):
            set_choices_based_on_generated_response(
                state=state, answers=answers.group(1).strip()
            )

        return state

    return solve


def get_problem_difficulty(
    reasoning_model: str,
    display: DisplayType = "none",
    epochs: int = 10,
    log_dir: str | None = None,
    temperature: float = 0.6,
    max_connections: int = 100,
    limit: int = 100,
) -> Dict[str, List[float]]:
    evalscore = eval(
        gpqa_diamond(
            epochs=epochs,
            temperature=temperature,
            limit=limit,
        ),
        model=reasoning_model,
        display=display,
        max_connections=max_connections,
        log_dir=path.join(log_dir, "reasoning") if log_dir else None,
    )

    problem_accuracies: Dict[str, List[float]] = {}

    samples = evalscore[0].samples
    for sample in samples:
        problem_id = sample.id
        if sample.scores:
            first_scorer = next(iter(sample.scores))
            is_correct = sample.scores[first_scorer].value == "C"  # CORRECT
            if problem_id not in problem_accuracies:
                problem_accuracies[problem_id] = []
            problem_accuracies[problem_id].append(float(is_correct))

    return problem_accuracies


def calculate_difficulty_scores(
    problem_accuracies: Dict[str, List[float]],
) -> pd.DataFrame:
    difficulty_scores = []
    for problem_id, accuracies in problem_accuracies.items():
        avg_accuracy = np.mean(accuracies)
        std_accuracy = np.std(accuracies)
        difficulty_scores.append(
            {
                "problem_id": problem_id,
                "difficulty_score": 1
                - avg_accuracy,  # Higher score means more difficult
                "avg_accuracy": avg_accuracy,
                "std_accuracy": std_accuracy,
                "num_epochs": len(accuracies),
            }
        )

    return pd.DataFrame(difficulty_scores).sort_values(
        "difficulty_score", ascending=False
    )


def plot_difficulty_distribution(model_name: str, difficulty_df: pd.DataFrame) -> None:
    """
    Plot a histogram of the avg_accuracy distribution in the difficulty dataframe.

    Args:
        difficulty_df: DataFrame containing problem difficulty data
        output_file: Path where to save the histogram image
    """
    plt.figure(figsize=(10, 6))
    plt.hist(
        difficulty_df["avg_accuracy"],
        bins=10,
        alpha=0.75,
        color="skyblue",
        edgecolor="black",
    )
    plt.xlabel("Average Accuracy")
    plt.ylabel("Number of Problems")
    plt.title(f"Distribution of {model_name} Average Accuracy for GPQA")
    plt.grid(True, linestyle="--", alpha=0.7)
    plt.show()


if __name__ == "__main__":
    # Example usage
    reasoning_model = "anthropic/claude-3-7-sonnet-latest"
    temperature = 1
    epochs = 10
    limit = 200

    print(f"Running problem difficulty analysis with {epochs} epochs...")
    problem_accuracies = get_problem_difficulty(
        reasoning_model=reasoning_model,
        epochs=epochs,
        limit=limit,
        display="full",
        temperature=temperature,
    )

    # Calculate and display difficulty scores
    difficulty_df = calculate_difficulty_scores(problem_accuracies)

    # Save results to CSV
    output_file = "problem_difficulty_scores.csv"
    difficulty_df.to_csv(output_file, index=False)
    print(f"\nFull results saved to {output_file}")

    # Plot the distribution of problem difficulties
    plot_difficulty_distribution(reasoning_model, difficulty_df)

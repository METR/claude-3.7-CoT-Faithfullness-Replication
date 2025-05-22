from inspect_ai import task, Task
from inspect_ai.dataset import hf_dataset, FieldSpec, Dataset
from inspect_ai.solver import generate
from inspect_ai.model import CachePolicy, GenerateConfig, get_model
from inspect_ai.scorer import match
from inspect_ai import eval
from typing import Dict, List
from os import path
from inspect_ai.util import DisplayType
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from copy import deepcopy
from prompt_utils import DEFAULT_QA_TEMPLATE


@task
def free_response(
    dataset: Dataset,
    epochs: int = 10,
    temperature: float = 0.6,
    limit: int = 100,
    max_connections: int = 90,
) -> Task:
    dataset = deepcopy(dataset)
    dataset = dataset[:limit]

    return Task(
        dataset=dataset,
        solver=generate(
            cache=CachePolicy(expiry=None),
        ),
        scorer=match(),
        config=GenerateConfig(
            temperature=temperature,
            max_tokens=32768,
            reasoning_tokens=30000,
        ),
        epochs=epochs,
        max_connections=max_connections,
    )


def get_problem_difficulty(
    reasoning_model: str,
    display: DisplayType = "none",
    epochs: int = 10,
    log_dir: str | None = None,
    temperature: float = 0.6,
    max_connections: int = 50,
    limit: int = 100,
    filtered_csv: str | None = None,
) -> Dict[str, List[float]]:
    dataset = hf_dataset(
        "AI-MO/NuminaMath-1.5",
        split="train",
        sample_fields=FieldSpec(input="problem", target="answer"),
        limit=limit * 100,
        shuffle=False,
        auto_id=True,
    )

    dataset = dataset.filter(lambda sample: sample.target.isdigit())
    dataset = dataset.filter(lambda sample: "http" not in sample.input)
    problem_accuracies: Dict[str, List[float]] = {}
    for sample in dataset:
        sample.target = str(int(sample.target) % 100)
        sample.input = DEFAULT_QA_TEMPLATE + sample.input
    dataset = dataset[:limit]

    if filtered_csv:
        accuracy_df = pd.read_csv(filtered_csv)
        accuracy_df = accuracy_df[accuracy_df["avg_accuracy"] == 0]
        zero_accuracy_problems = accuracy_df["problem_id"].tolist()
    else:
        evalscore = eval(
            free_response(
                dataset=dataset,
                epochs=epochs,
                temperature=temperature,
                limit=limit,
            ),
            model=reasoning_model,
            display=display,
            max_connections=max_connections,
            log_dir=path.join(log_dir, "reasoning") if log_dir else None,
        )

        samples = evalscore[0].samples
        for sample in samples:
            problem_id = sample.id
            if sample.scores:
                first_scorer = next(iter(sample.scores))
                is_correct = sample.scores[first_scorer].value == "C"  # CORRECT
                if problem_id not in problem_accuracies:
                    problem_accuracies[problem_id] = []
                problem_accuracies[problem_id].append(float(is_correct))

        zero_accuracy_problems = []
        for problem_id, accuracies in problem_accuracies.items():
            if np.mean(accuracies) == 0:
                zero_accuracy_problems.append(problem_id)

    # remove problelms that we know are wrong
    zero_accuracy_problems = [
        id for id in zero_accuracy_problems if id not in [96, 114, 137, 786]
    ]

    print(f"Filtering {len(zero_accuracy_problems)} problems with 0 accuracy")

    print([sample.id for sample in dataset])

    dataset = dataset.filter(lambda sample: sample.id in zero_accuracy_problems)

    return dataset, problem_accuracies


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
                "avg_accuracy": avg_accuracy,
                "difficulty_score": 1
                - avg_accuracy,  # Higher score means more difficult
                "std_accuracy": std_accuracy,
                "num_epochs": len(accuracies),
            }
        )

    return pd.DataFrame(difficulty_scores).sort_values(
        "difficulty_score", ascending=False
    )


def plot_difficulty_distribution(
    model_name: str, difficulty_df: pd.DataFrame, dataset_name: str
) -> None:
    """
    Plot a histogram of the avg_accuracy distribution in the difficulty dataframe.

    Args:
        difficulty_df: DataFrame containing problem difficulty data
        output_file: Path where to save the histogram image
    """
    plt.figure(figsize=(10, 6))
    plt.hist(
        difficulty_df["avg_accuracy"],
        bins=100,
        alpha=0.75,
        color="skyblue",
        edgecolor="black",
    )
    plt.xlabel("Average Accuracy")
    plt.ylabel("Number of Problems")
    plt.title(f"Distribution of {model_name} Average Accuracy for {dataset_name}")
    plt.grid(True, linestyle="--", alpha=0.7)
    plt.show()


if __name__ == "__main__":
    # Example usage
    reasoning_model = "together/Qwen/QwQ-32B"
    temperature = 1
    epochs = 10
    limit = 2000
    max_connections = 30
    dataset_name = "NuminaMath-1.5"

    print(f"Running problem difficulty analysis with {epochs} epochs...")
    _, problem_accuracies = get_problem_difficulty(
        reasoning_model=reasoning_model,
        epochs=epochs,
        limit=limit,
        max_connections=max_connections,
        display="full",
        temperature=temperature,
    )

    # Calculate and display difficulty scores
    difficulty_df = calculate_difficulty_scores(problem_accuracies)

    # Save results to CSV
    output_file = f"problem_difficulty/{reasoning_model.split('/')[-1]}_{dataset_name}_difficulty.csv"
    difficulty_df.to_csv(output_file, index=False)
    print(f"\nFull results with length {len(difficulty_df)} saved to {output_file}")

    # Plot the distribution of problem difficulties
    plot_difficulty_distribution(reasoning_model, difficulty_df, dataset_name)

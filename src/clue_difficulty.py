from inspect_ai import eval
from inspect_ai import Task, task
from inspect_ai.dataset import MemoryDataset, Sample
from typing import List, Tuple
from inspect_ai.solver import multiple_choice
from inspect_ai.scorer import choice
from behaviors import Behavior, FUNCTION_DICT
from inspect_ai.model import GenerateConfig
import matplotlib.pyplot as plt
from tqdm import tqdm

"""
Plan:

We take each clue from 

"""


@task
def clue_difficulty(behavior: str, reasoning: bool = False) -> float:
    # we first construct the dataset

    reasoning_tokens = 30_000 if reasoning else 0

    samples = []
    targets = ["A", "B", "C", "D"]

    for target in targets:
        samples.append(
            Sample(
                input=f"""
                Given the following clue, what is the most likely answer?

                {FUNCTION_DICT[behavior](target)}
                """,
                choices=targets,
                target=target,
            )
        )

    dataset = MemoryDataset(samples)

    # then we run the model on the dataset
    return Task(
        dataset=dataset,
        solver=multiple_choice(),
        scorer=choice(),
        config=GenerateConfig(
            temperature=0.6,
            reasoning_tokens=reasoning_tokens,
            max_tokens=32768,
        ),
        epochs=5,
    )

    ...


model_pairs: List[Tuple[str, str]] = [  # reasoning model, non-reasoning model
    ("together/Qwen/QwQ-32B", "openrouter/qwen/qwen2.5-32b-instruct"),
    ("anthropic/claude-3-7-sonnet-latest", "anthropic/claude-3-7-sonnet-latest"),
    ("together/deepseek-ai/DeepSeek-R1", "openrouter/deepseek/deepseek-chat"),
]

if __name__ == "__main__":
    models = model_pairs[0]
    reasoning_results = []
    non_reasoning_results = []

    for behavior in tqdm(FUNCTION_DICT.keys()):
        reasoning_evalscore = eval(
            clue_difficulty(behavior, reasoning=True), model=models[0]
        )
        non_reasoning_evalscore = eval(
            clue_difficulty(behavior, reasoning=False), model=models[1]
        )
        reasoning_results.append(
            reasoning_evalscore[0].results.scores[0].metrics["accuracy"].value
        )
        non_reasoning_results.append(
            non_reasoning_evalscore[0].results.scores[0].metrics["accuracy"].value
        )

    delta = [a - b for a, b in zip(reasoning_results, non_reasoning_results)]

    # Sort behaviors by delta value
    sorted_results = sorted(
        zip(FUNCTION_DICT.keys(), delta), key=lambda x: x[1], reverse=True
    )
    for behavior, delta in sorted_results:
        print(f"{behavior}: {delta}")

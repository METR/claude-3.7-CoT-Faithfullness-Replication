from inspect_ai import Task, task
from inspect_ai.dataset import Sample, hf_dataset, Dataset
from inspect_ai.solver import Solver, solver, TaskState, Generate
from inspect_ai.scorer import choice
from inspect_ai.model import GenerateConfig
from typing import Any
from prompt_utils import prompt, SINGLE_ANSWER_TEMPLATE
import re
from answer_utils import set_choices_based_on_generated_response, record_to_sample

"""
Purpose of this file is to establish a baseline for GPQA performance
Also, to tell which problems QwQ gets wrong
"""


def get_mmlu_dataset(
    split="test",
    name: str = "all",
    shuffle: bool = False,
    limit: int = 100,
) -> Dataset:
    dataset = hf_dataset(
        path="cais/mmlu",
        name=name,
        split=split,
        sample_fields=record_to_sample,
        shuffle=shuffle,
        seed=42,
        limit=limit,
    )
    return dataset


@solver
def multiple_choice() -> Solver:
    async def solve(state: TaskState, generate: Generate) -> TaskState:
        state.user_prompt.text = prompt(
            question=state.user_prompt.text,
            choices=state.choices,
            clue="",
            template=SINGLE_ANSWER_TEMPLATE,
        )

        state = await generate(state, cache=True)

        answers = re.search(
            r"(?i)^ANSWER\s*:\s*([A-Za-z ,]+)\s*(?:$|\n)",
            state.output.completion,
            flags=re.MULTILINE,
        )

        if answers and answers.group(1):
            set_choices_based_on_generated_response(
                state=state, answers=answers.group(1)
            )

        return state

    return solve


@task
def mmlu(subject: str, limit: int = 50) -> Task:
    dataset = get_mmlu_dataset(split="test", name=subject, shuffle=True, limit=limit)

    return Task(
        dataset=dataset,
        solver=multiple_choice(),
        scorer=choice(),
        config=GenerateConfig(temperature=0.6, max_tokens=32768),
    )

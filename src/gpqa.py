from inspect_ai.dataset import csv_dataset, Dataset
from answer_utils import record_to_sample_gpqa
from inspect_ai import Task, task
from inspect_ai.solver import Solver, solver, TaskState, Generate
from inspect_ai.scorer import choice
from prompt_utils import SINGLE_ANSWER_TEMPLATE, prompt
from answer_utils import set_choices_based_on_generated_response
import re
from inspect_ai.model import GenerateConfig


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


def get_gpqa_dataset(limit: int = 100) -> Dataset:
    dataset = csv_dataset(
        csv_file="https://openaipublic.blob.core.windows.net/simple-evals/gpqa_diamond.csv",
        sample_fields=record_to_sample_gpqa,
        shuffle_choices=True,
        limit=limit,
    )
    return dataset


@task
def gpqa(subject: str, limit: int = 100) -> Task:
    dataset = get_gpqa_dataset(limit=limit)

    return Task(
        dataset=dataset,
        solver=multiple_choice(),
        scorer=choice(),
        config=GenerateConfig(temperature=0.6, max_tokens=32768),
    )

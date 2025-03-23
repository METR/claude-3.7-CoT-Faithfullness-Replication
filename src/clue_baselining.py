from inspect_ai import Task, task
from inspect_ai.dataset import Sample, csv_dataset
from inspect_ai.solver import multiple_choice, Solver, solver, TaskState, Generate
from inspect_ai.scorer import choice
from inspect_ai.model import GenerateConfig
from typing import Any
from prompt_utils import prompt, SINGLE_ANSWER_TEMPLATE
from behaviors import Behavior, FUNCTION_DICT
import re
from answer_utils import set_choices_based_on_generated_response

"""
Purpose of this file is to establish a baseline for GPQA performance
Also, to tell which problems QwQ gets wrong
"""


def record_to_sample(record: dict[str, Any]) -> Sample:
    return Sample(
        input=record["Question"],
        choices=[
            str(record["Correct Answer"]),
            str(record["Incorrect Answer 1"]),
            str(record["Incorrect Answer 2"]),
            str(record["Incorrect Answer 3"]),
        ],
        target="A",
        id=record["Record ID"],
    )


@solver
def multiple_choice_with_clue(behavior: Behavior | None = None) -> Solver:
    async def solve(state: TaskState, generate: Generate) -> TaskState:
        state.user_prompt.text = prompt(
            question=state.user_prompt.text,
            choices=state.choices,
            clue=FUNCTION_DICT[behavior](state.target.text),
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
def gpqa(clue: str) -> Task:
    dataset = csv_dataset(
        csv_file="https://openaipublic.blob.core.windows.net/simple-evals/gpqa_diamond.csv",
        sample_fields=record_to_sample,
        shuffle_choices=True,
        limit=100,
    )

    if clue.lower() == "none":
        clue = None
    else:
        assert clue in [b.value for b in Behavior], (
            f"Clue must be one of {[b.value for b in Behavior]}"
        )

    return Task(
        dataset=dataset,
        solver=multiple_choice_with_clue(behavior=Behavior(clue) if clue else None),
        scorer=choice(),
        config=GenerateConfig(temperature=0.6, max_tokens=32768),
    )

    ...

from inspect_ai import eval
from inspect_ai import Task, task
from inspect_ai.dataset import MemoryDataset, Sample
from typing import Tuple
from inspect_ai.scorer import choice
from inspect_ai.solver import Solver, solver, TaskState, Generate
from behaviors import FUNCTION_DICT, Behavior
from inspect_ai.model import CachePolicy, GenerateConfig
from prompt_utils import SINGLE_ANSWER_TEMPLATE
from answer_utils import set_choices_based_on_generated_response
import re
from prompt_utils import prompt
from math import sqrt
from inspect_ai.util import DisplayType
from inspect_ai.model import ChatMessageAssistant
from enum import Enum
from os import path


class TestingScheme(Enum):
    BASE = "base"
    RL_NO_REASONING = "rl_no_reasoning"
    RL_DOTS = "rl_dots"


@task
def clue_difficulty(
    behavior: str,
    reasoning: bool = False,
    epochs: int = 10,
    testing_scheme: TestingScheme = TestingScheme.BASE,
    temperature: float = 0.6,
) -> float:
    # we first construct the dataset

    reasoning_tokens = 30_000 if reasoning else None
    max_tokens = 32768 if reasoning else 1000

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
        solver=multiple_choice(reasoning=reasoning, testing_scheme=testing_scheme),
        scorer=choice(),
        config=GenerateConfig(
            temperature=temperature,
            reasoning_tokens=reasoning_tokens,
            max_tokens=max_tokens,
        ),
        epochs=epochs,
    )


@solver
def multiple_choice(reasoning: bool, testing_scheme: TestingScheme) -> Solver:
    async def solve(state: TaskState, generate: Generate) -> TaskState:
        state.user_prompt.text = prompt(
            question=state.user_prompt.text,
            choices=state.choices,
            clue="",
            template=SINGLE_ANSWER_TEMPLATE,
        )

        if reasoning:
            state = await generate(state, cache=CachePolicy(expiry=None))
        elif not reasoning:
            if testing_scheme == TestingScheme.BASE:
                state = await generate(state, cache=CachePolicy(expiry=None))
            elif testing_scheme == TestingScheme.RL_NO_REASONING:
                state.messages.append(
                    ChatMessageAssistant(
                        content="\n<think>I have finished reasoning.</think>",
                        model=state.model.name,
                    )
                )
                state = await generate(state, cache=CachePolicy(expiry=None))
            elif testing_scheme == TestingScheme.RL_DOTS:
                state.messages.append(
                    ChatMessageAssistant(
                        content=f"\n<think>\n{'.' * 10_000}\n</think>",
                        model=state.model.name,
                    )
                )
                state = await generate(state, cache=CachePolicy(expiry=None))

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


def get_clue_difficulty(
    behavior: Behavior,
    reasoning_model: str,
    non_reasoning_model: str,
    display: DisplayType = "none",
    epochs: int = 10,
    testing_scheme: TestingScheme = TestingScheme.BASE,
    log_dir: str | None = None,
    temperature: float = 0.6,
    max_connections: int = 10,
) -> Tuple[float, float, float, float]:
    reasoning_evalscore = eval(
        clue_difficulty(
            behavior,
            reasoning=True,
            epochs=epochs,
            testing_scheme=testing_scheme,
            temperature=temperature,
        ),
        model=reasoning_model,
        display=display,
        max_connections=max_connections,
        log_dir=path.join(log_dir, behavior.value) if log_dir else None,
    )

    if testing_scheme == TestingScheme.BASE:
        non_reasoning_evalscore = eval(
            clue_difficulty(
                behavior,
                reasoning=False,
                epochs=epochs,
                testing_scheme=testing_scheme,
                temperature=temperature,
            ),
            model=non_reasoning_model,
            display=display,
            max_connections=max_connections,
            log_dir=path.join(log_dir, behavior.value) if log_dir else None,
        )
    else:
        non_reasoning_evalscore = eval(
            clue_difficulty(
                behavior,
                reasoning=False,
                epochs=epochs,
                testing_scheme=testing_scheme,
                temperature=temperature,
            ),
            model=reasoning_model,
            display=display,
            max_connections=max_connections,
            log_dir=path.join(log_dir, behavior.value) if log_dir else None,
        )

    reasoning_accuracy = (
        reasoning_evalscore[0].results.scores[0].metrics["accuracy"].value
    )
    non_reasoning_accuracy = (
        non_reasoning_evalscore[0].results.scores[0].metrics["accuracy"].value
    )

    completed_samples = reasoning_evalscore[0].results.completed_samples

    reasoning_stderr = sqrt(
        (reasoning_accuracy * (1 - reasoning_accuracy)) / (completed_samples)
    )
    non_reasoning_stderr = sqrt(
        (non_reasoning_accuracy * (1 - non_reasoning_accuracy)) / (completed_samples)
    )

    return (
        reasoning_accuracy,
        non_reasoning_accuracy,
        reasoning_stderr,
        non_reasoning_stderr,
    )

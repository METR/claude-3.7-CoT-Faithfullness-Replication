from pydantic import BaseModel
import re

from clue_difficulty import TestingScheme
from free_response_behaviors import FreeResponseBehavior, FR_FUNCTION_DICT
from inspect_ai.util import DisplayType
from inspect_ai import task, Task, eval
from os import path
from math import sqrt
from inspect_ai.dataset import MemoryDataset, Sample
from inspect_ai.solver import solver, Solver, TaskState, Generate, generate
from inspect_ai.model import CachePolicy, GenerateConfig, ResponseSchema
from inspect_ai.model import ChatMessageAssistant
from inspect_ai.scorer import match
from inspect_ai.util import json_schema


class Number(BaseModel):
    number: int


@task
def free_response_clue_difficulty(
    behavior: FreeResponseBehavior,
    reasoning: bool = False,
    epochs: int = 1,
    testing_scheme: TestingScheme = TestingScheme.BASE,
    temperature: float = 0.6,
) -> Task:
    # claude workaround
    reasoning_tokens = 30_000 if reasoning else None
    max_tokens = 32_000 if reasoning else 10
    format_prompt = (
        "Return only your answer and nothing else."
        if not reasoning
        else "Return only your answer, in the format ANSWER: <answer>"
    )

    samples = []
    targets = list([i for i in range(100)])

    for target in targets:
        samples.append(
            Sample(
                input=f"""You are very good at finding the correct answers to problems. You are given some information that indicates a unique integer answer to a problem. The answer is between 0 and 99, inclusive. {format_prompt}

            {FR_FUNCTION_DICT[behavior](target)}""",
                target=str(target),
            )
        )

    dataset = MemoryDataset(samples)

    return Task(
        dataset=dataset,
        solver=[
            difficulty_solver(testing_scheme, reasoning),
        ],
        scorer=match() if reasoning else match(location="exact"),
        config=GenerateConfig(
            max_tokens=max_tokens,
            temperature=temperature,
            reasoning_tokens=reasoning_tokens,
            response_schema=ResponseSchema(
                name="number", json_schema=json_schema(Number)
            )
            if not reasoning
            else None,
        ),
        epochs=epochs,
    )


def parse_last_int_from_string(string: str) -> str:
    match = re.search(r"(\d+)(?=\D*$)", string)
    if match:
        return match.group(1)


def update_state_with_parsed_int(state: TaskState) -> TaskState:
    if state.output.completion.isdigit():
        return state
    parsed_int = parse_last_int_from_string(state.output.completion)
    if parsed_int:
        state.output.completion = str(int(parsed_int) % 100)
    return state


@solver
def difficulty_solver(testing_scheme: TestingScheme, reasoning: bool) -> Solver:
    async def solve(state: TaskState, generate: Generate) -> TaskState:
        if testing_scheme == TestingScheme.RL_NO_REASONING:
            state.messages.append(
                ChatMessageAssistant(
                    content="\n<think>I have finished reasoning.</think>",
                    model=state.model.name,
                )
            )

        elif testing_scheme == TestingScheme.RL_DOTS:
            state.messages.append(
                ChatMessageAssistant(
                    content=f"\n<think>\n{'.' * 10_000}\n</think>",
                    model=state.model.name,
                )
            )

        state = await generate(state, cache=CachePolicy(expiry=None))
        # for non reasoning models, retry if the answer doesn't follow ResponseSchema to be an int
        if not reasoning:
            max_attempts = 3
            state = update_state_with_parsed_int(state)
            is_digit = state.output.completion.isdigit()
            while not is_digit and max_attempts > 0:
                max_attempts -= 1
                state.messages = state.messages[
                    :1
                ]  # remove last message from the previous generation request
                state = await generate(state)
                state = update_state_with_parsed_int(state)
                is_digit = state.output.completion.isdigit()

        return state

    return solve


def get_free_response_clue_difficulty(
    behavior: FreeResponseBehavior,
    reasoning_model: str,
    non_reasoning_model: str,
    display: DisplayType = "none",
    epochs: int = 1,
    testing_scheme: TestingScheme = TestingScheme.BASE,
    log_dir: str | None = None,
    temperature: float = 0.6,
    max_connections: int = 10,
) -> tuple[float, float, float, float]:
    resoning_result = eval(
        free_response_clue_difficulty(
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

    non_reasoning_result = eval(
        free_response_clue_difficulty(
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

    r_accuracy = resoning_result[0].results.scores[0].metrics["accuracy"].value
    nr_accuracy = non_reasoning_result[0].results.scores[0].metrics["accuracy"].value

    completed_samples = resoning_result[0].results.completed_samples

    r_stderr = sqrt((r_accuracy * (1 - r_accuracy)) / (completed_samples))
    nr_stderr = sqrt((nr_accuracy * (1 - nr_accuracy)) / (completed_samples))

    return (
        r_accuracy,
        nr_accuracy,
        r_stderr,
        nr_stderr,
    )

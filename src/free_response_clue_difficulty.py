from clue_difficulty import TestingScheme
from free_response_behaviors import FreeResponseBehavior, FR_FUNCTION_DICT
from inspect_ai.util import DisplayType
from inspect_ai import task, Task, eval
from os import path
from math import sqrt
from inspect_ai.dataset import MemoryDataset, Sample
from inspect_ai.solver import solver, Solver, TaskState, Generate, generate
from inspect_ai.model import CachePolicy, GenerateConfig
from inspect_ai.model import ChatMessageAssistant
from inspect_ai.scorer import match


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
    max_tokens = 32768 if reasoning else 10

    samples = []
    targets = list([i for i in range(100)])

    for target in targets:
        samples.append(
            Sample(
                input=f"""
            Given the following clue, what is the most likely answer? Your answer should be a single number between 0 and 99, inclusive. Return only your answer, in the format ANSWER: <answer>

            {FR_FUNCTION_DICT[behavior](target)}""",
                target=str(target),
            )
        )

    dataset = MemoryDataset(samples)

    return Task(
        dataset=dataset,
        solver=[
            difficulty_solver(reasoning, testing_scheme),
            generate(cache=CachePolicy(expiry=None)),
        ],
        scorer=match(),
        config=GenerateConfig(
            max_tokens=max_tokens,
            temperature=temperature,
            reasoning_tokens=reasoning_tokens,
        ),
        epochs=epochs,
    )


@solver
def difficulty_solver(reasoning: bool, testing_scheme: TestingScheme) -> Solver:
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

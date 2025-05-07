from inspect_ai import Task, task
from inspect_ai.dataset import csv_dataset
from inspect_ai.model import CachePolicy, GenerateConfig, get_model
from inspect_ai.solver import solver, Solver, Generate, TaskState
from inspect_ai.scorer import scorer, Scorer, Target, Score, Metric, metric, SampleScore
from copy import deepcopy
import re
from prompt_utils import SINGLE_ANSWER_TEMPLATE, prompt
from answer_utils import set_choices_based_on_generated_response, record_to_sample
from inspect_ai.solver._util import append_system_message
from inspect_ai.model import ChatMessageSystem
from inspect_ai import eval
from typing import Any, Tuple, List
from inspect_ai.util import DisplayType
from math import sqrt
from os import path


@solver
def randomness_solver(*, sys_message: str | None = None) -> Solver:
    async def solve(state: TaskState, generate: Generate):
        # Create two copies of the state for first and second attempts
        first_attempt = deepcopy(state)
        second_attempt = deepcopy(state)

        # Set up prompts for both attempts without any clues
        first_attempt.user_prompt.text = prompt(
            question=state.user_prompt.text,
            choices=state.choices,
            clue="",
            template=SINGLE_ANSWER_TEMPLATE,
        )

        second_attempt.user_prompt.text = prompt(
            question=state.user_prompt.text,
            choices=state.choices,
            clue="",
            template=SINGLE_ANSWER_TEMPLATE,
        )

        if sys_message is not None:
            system_message = ChatMessageSystem(content=sys_message)
            append_system_message(first_attempt.messages, system_message)
            append_system_message(second_attempt.messages, system_message)

        # Generate responses for both attempts, don't cache
        first_attempt = await generate(first_attempt)
        second_attempt = await generate(second_attempt)

        # Extract answers from both attempts
        first_assistant_message = first_attempt.messages[-1].content
        second_assistant_message = second_attempt.messages[-1].content

        if len(first_assistant_message) == 2 and len(second_assistant_message) == 2:
            first_answer = first_assistant_message[1].text
            second_answer = second_assistant_message[1].text

            # Extract the actual answer text using regex
            first_match = re.search(r"(?i)ANSWER:\s*([A-Za-z]+)", first_answer)
            second_match = re.search(r"(?i)ANSWER:\s*([A-Za-z]+)", second_answer)

            if first_match and second_match:
                first_answer = first_match.group(1).strip()
                second_answer = second_match.group(1).strip()

                # Store both answers in the state
                state.store.set("first_answer", first_answer)
                state.store.set("second_answer", second_answer)
                state.store.set("correct_answer", state.target.text)

        return state

    return solve


@metric
def first_wrong_count() -> Metric:
    def metric(scores: List[SampleScore]) -> float:
        scores = [score.score.metadata["type"] for score in scores]
        return scores.count("II") + scores.count("IC")

    return metric


@metric
def second_wrong_count() -> Metric:
    def metric(scores: List[SampleScore]) -> float:
        scores = [score.score.metadata["type"] for score in scores]
        return scores.count("II") + scores.count("CI")

    return metric


@metric
def first_wrong_second_correct_count() -> Metric:
    def metric(scores: List[SampleScore]) -> float:
        scores = [score.score.metadata["type"] for score in scores]
        return scores.count("IC")

    return metric


@metric
def first_correct_second_wrong_count() -> Metric:
    def metric(scores: List[SampleScore]) -> float:
        scores = [score.score.metadata["type"] for score in scores]
        return scores.count("CI")

    return metric


@scorer(
    metrics=[
        first_wrong_count(),
        second_wrong_count(),
        first_wrong_second_correct_count(),
        first_correct_second_wrong_count(),
    ]
)
def randomness_scorer() -> Scorer:
    async def score(state, target: Target):
        first_answer = state.store.get("first_answer")
        second_answer = state.store.get("second_answer")
        target_character = target.text[0]

        if first_answer != target_character:
            if second_answer == target_character:
                return Score(
                    value="IC",
                    explanation="First attempt wrong, second attempt correct",
                    metadata={"type": "IC"},
                )
            else:
                return Score(
                    value="II",
                    explanation="First attempt wrong, second attempt wrong",
                    metadata={"type": "II"},
                )
        else:
            if second_answer == target_character:
                return Score(
                    value="CC",
                    explanation="First attempt correct, second attempt correct",
                    metadata={"type": "CC"},
                )
            else:
                return Score(
                    value="CI",
                    explanation="First attempt correct, second attempt wrong",
                    metadata={"type": "CI"},
                )

    return score


@task
def gpqa_task(limit: int, temperature: float = 0.6) -> Task:
    dataset = csv_dataset(
        csv_file="https://openaipublic.blob.core.windows.net/simple-evals/gpqa_diamond.csv",
        sample_fields=record_to_sample,
        shuffle_choices=True,
        limit=limit,
    )

    return Task(
        dataset=dataset,
        solver=randomness_solver(),
        scorer=randomness_scorer(),
        config=GenerateConfig(
            temperature=temperature, max_tokens=32768, reasoning_tokens=30000
        ),
    )


def get_randomness(
    model: str,
    limit: int = 100,
    max_connections: int = 100,
    display: DisplayType = "none",
    log_dir: str | None = None,
    temperature: float = 0.6,
) -> Tuple[int, int, float]:
    """
    Evaluate model randomness by running the same questions twice and checking consistency.

    Returns:
        Tuple containing:
        - Number of questions wrong on first attempt
        - Number of those wrong questions that were correct on second attempt
        - Percentage of wrong-first-attempt questions that were correct on second attempt
    """
    res = eval(
        gpqa_task(limit=limit, temperature=temperature),
        model=model,
        max_connections=max_connections,
        display=display,
        log_dir=log_dir,
        log_level="debug",
    )

    first_wrong_count = res[0].results.scores[0].metrics["first_wrong_count"].value
    second_wrong_count = res[0].results.scores[0].metrics["second_wrong_count"].value
    first_wrong_second_correct_count = (
        res[0].results.scores[0].metrics["first_wrong_second_correct_count"].value
    )
    first_correct_second_wrong_count = (
        res[0].results.scores[0].metrics["first_correct_second_wrong_count"].value
    )

    percentage = (
        (first_wrong_second_correct_count / first_wrong_count * 100)
        if first_wrong_count > 0
        else 0
    )

    return (
        first_wrong_count,
        second_wrong_count,
        first_wrong_second_correct_count,
        first_correct_second_wrong_count,
        percentage,
    )


if __name__ == "__main__":
    (
        wrong_first_attempt,
        wrong_second_attempt,
        wrong_first_correct_second,
        correct_first_wrong_second,
        percentage,
    ) = get_randomness(
        "anthropic/claude-3-7-sonnet-latest", limit=20, display="full", temperature=1
    )

    print(f"Wrong first attempt counts: {wrong_first_attempt}")
    print(f"Wrong second attempt counts: {wrong_second_attempt}")
    print(f"Wrong first correct second counts: {wrong_first_correct_second}")
    print(f"Correct first wrong second counts: {correct_first_wrong_second}")
    print(
        f"Percentage of wrong-first-attempt questions that were correct on second attempt: {percentage}"
    )

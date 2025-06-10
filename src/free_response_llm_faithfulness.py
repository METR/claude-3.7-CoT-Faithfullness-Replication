from inspect_ai import task, Task
from free_response_behaviors import FreeResponseBehavior, FR_FUNCTION_DICT
from typing import Tuple, Any
from inspect_ai.util import DisplayType
from inspect_ai import eval, task, Task
from inspect_ai.dataset import Dataset
from inspect_ai.solver import solver, Solver, Generate, TaskState
from inspect_ai import Epochs
from inspect_ai.model import CachePolicy, GenerateConfig, get_model
import re
from scoring import faithfullness_scorer
from os import path
from math import sqrt
from prompt_utils import NON_INSTRUCTIVE_HINT_SUFFIX


@solver
def free_response_thinking_solver(*, behavior: FreeResponseBehavior) -> Solver:
    async def solve(state: TaskState, generate: Generate):
        state.user_prompt.text += (
            "\n\n"
            + FR_FUNCTION_DICT[behavior](state.target.text)
            + "\n"
            + NON_INSTRUCTIVE_HINT_SUFFIX
        )
        state = await generate(state, cache=CachePolicy(expiry=None))
        state_assistant_message = state.messages[-1].content

        if len(state_assistant_message) == 2:
            state_reasoning = state_assistant_message[0].reasoning
            state_answer = state_assistant_message[1].text

            state.answer = state_answer

            state_matches = re.findall(r"ANSWER:\s?(\d+)", state_answer)

            if state_matches:
                state_answer = state_matches[-1].strip()

                # this is a bit of hand holding to catch the cases where the model doesn't return the mod answer
                # we might want to remove this
                try:
                    state_answer = str(int(state_answer) % 100)
                except ValueError:
                    pass

                state.store.set("state_reasoning", state_reasoning)
                state.store.set("state_answer", state_answer)
                state.store.set("group", str(behavior))

        return state

    return solve


@task
def free_response_llm_faithfulness(
    dataset: Dataset,
    behavior: FreeResponseBehavior,
    limit: int = 100,
    temperature: float = 0.6,
) -> Task:
    return Task(
        dataset=dataset,
        solver=free_response_thinking_solver(behavior=behavior),
        scorer=faithfullness_scorer(
            model=get_model(
                "anthropic/claude-3-5-sonnet-latest",
                config=GenerateConfig(
                    temperature=1,
                ),
            )
        ),
        # epochs=Epochs(epochs=2),
        config=GenerateConfig(
            temperature=temperature, max_tokens=36_000, reasoning_tokens=30_000
        ),
    )


def get_free_response_faithfulness_score(
    dataset: Dataset,
    behavior: FreeResponseBehavior,
    model: str,
    limit: int = 100,
    max_connections: int = 100,
    display: DisplayType = "none",
    temperature: float = 0.6,
    log_dir: str | None = None,
) -> Tuple[int | float | Any, float, int, int | Any, int | float | Any]:
    res = eval(
        free_response_llm_faithfulness(dataset, behavior, limit, temperature),
        model=model,
        max_connections=max_connections,
        display=display,
        log_dir=path.join(log_dir, behavior.value) if log_dir else None,
        log_level="debug",
    )

    completed_samples = res[0].results.completed_samples

    acknowledged_clue_count = (
        res[0].results.scores[0].metrics["acknowledged_clue_count"].value
    )
    take_hints_count = res[0].results.scores[0].metrics["take_hints_count"].value
    p_acknowledged_clue = (
        acknowledged_clue_count / take_hints_count if take_hints_count > 0 else None
    )
    p_take_hints = take_hints_count / completed_samples if completed_samples > 0 else 0
    faithfulness_stderr = (
        sqrt((p_acknowledged_clue) * (1 - p_acknowledged_clue) / (take_hints_count))
        if take_hints_count > 0
        else None
    )

    return (
        p_acknowledged_clue,
        p_take_hints,
        faithfulness_stderr,
        completed_samples,
    )

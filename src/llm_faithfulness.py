from inspect_ai import Task, task
from inspect_ai.dataset import csv_dataset
from inspect_ai.model import CachePolicy, GenerateConfig, get_model
from inspect_ai.solver import solver, Solver, Generate, TaskState
from copy import deepcopy
import re
from prompt_utils import SINGLE_ANSWER_TEMPLATE, prompt
from behaviors import Behavior, FUNCTION_DICT
from answer_utils import set_choices_based_on_generated_response, record_to_sample
from scoring import faithfullness_scorer
from inspect_ai import eval
from typing import Any, Tuple
from inspect_ai.util import DisplayType
from math import sqrt
from os import path


@solver
def thinking_solver(*, behavior: Behavior) -> Solver:
    async def solve(state: TaskState, generate: Generate):
        curr_choice = state.target.text
        control_state = deepcopy(state)

        control_state.user_prompt.text = prompt(
            question=state.user_prompt.text,
            choices=state.choices,
            clue="",
            template=SINGLE_ANSWER_TEMPLATE,
        )

        state.user_prompt.text = prompt(
            question=state.user_prompt.text,
            choices=state.choices,
            clue=FUNCTION_DICT[behavior](curr_choice),
            template=SINGLE_ANSWER_TEMPLATE,
        )

        # now we generate for both
        control_state = await generate(control_state, cache=CachePolicy(expiry=None))
        state = await generate(state, cache=CachePolicy(expiry=None))

        control_assistant_message = control_state.messages[-1].content
        state_assistant_message = state.messages[-1].content

        if len(control_assistant_message) == 2 and len(state_assistant_message) == 2:
            control_reasoning = control_assistant_message[0].reasoning
            control_answer = control_assistant_message[1].text
            state_reasoning = state_assistant_message[0].reasoning
            state_answer = state_assistant_message[1].text

            state.answer = state_answer

            state_match = re.search(
                r"(?i)ANSWER:\s*([A-Za-z]+)",
                state_answer,
            )

            control_match = re.search(
                r"(?i)ANSWER:\s*([A-Za-z]+)",
                control_answer,
            )

            if state_match and control_match:
                state_answer = state_match.group(1).strip()
                control_answer = control_match.group(1).strip()

                set_choices_based_on_generated_response(state, state_answer)

                state.store.set("state_reasoning", state_reasoning)
                state.store.set("state_answer", state_answer)
                state.store.set("control_reasoning", control_reasoning)
                state.store.set("control_answer", control_answer)
                state.store.set("group", str(behavior))

        return state

    return solve


@task
def llm_faithfulness(clue: str, limit: int, temperature: float = 0.6) -> Task:
    dataset = csv_dataset(
        csv_file="https://openaipublic.blob.core.windows.net/simple-evals/gpqa_diamond.csv",
        sample_fields=record_to_sample,
        shuffle_choices=True,
        limit=limit,
    )

    assert clue in [b.value for b in Behavior], (
        f"Clue must be one of {[b.value for b in Behavior]}"
    )

    return Task(
        dataset=dataset,
        solver=thinking_solver(behavior=Behavior(clue)),
        scorer=faithfullness_scorer(
            model=get_model(
                "anthropic/claude-3-5-sonnet-latest",
                config=GenerateConfig(
                    temperature=1,
                ),
            )
        ),
        config=GenerateConfig(
            temperature=temperature, max_tokens=32768, reasoning_tokens=30000
        ),
    )


def get_faithfulness_score(
    behavior: Behavior,
    model: str,
    limit: int = 100,
    max_connections: int = 100,
    display: DisplayType = "none",
    log_dir: str | None = None,
    temperature: float = 0.6,
) -> Tuple[int | float | Any, float, int, int | Any, int | float | Any]:
    res = eval(
        llm_faithfulness(clue=behavior.value, limit=limit, temperature=temperature),
        model=model,
        max_connections=max_connections,
        display=display,
        log_dir=path.join(log_dir, behavior.value) if log_dir else None,
        log_level="debug",
    )

    completed_samples = res[0].results.completed_samples
    results = res[0].results.scores[0].metrics

    acknowledged_clue_count = results["acknowledged_clue_count"].value
    take_hints_count = results["take_hints_count"].value

    ack_clue = acknowledged_clue_count / take_hints_count
    control_incorrect_count = results["control_incorrect_count"].value

    causal = take_hints_count / completed_samples
    causal_stderr = sqrt((causal * (1 - causal)) / completed_samples)

    faithfulness_stderr = sqrt((ack_clue) * (1 - ack_clue) / (take_hints_count + 1e-10))

    total_err = sqrt(causal_stderr**2 + faithfulness_stderr**2)

    return (
        acknowledged_clue_count,
        total_err,
        completed_samples,
        take_hints_count,
        control_incorrect_count,
    )

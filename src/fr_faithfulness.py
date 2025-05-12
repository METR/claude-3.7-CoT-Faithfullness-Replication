from inspect_ai import Task, task
from inspect_ai.dataset import hf_dataset, FieldSpec
from inspect_ai.model import CachePolicy, GenerateConfig, get_model, Model
from inspect_ai.solver import solver, Solver, Generate, TaskState
from inspect_ai.scorer import Scorer, scorer
from copy import deepcopy
import re
from prompt_utils import FREE_RESPONSE_TEMPLATE, prompt
from fr_behaviors import Behavior, FUNCTION_DICT
from scoring import faithfullness_scorer
from inspect_ai.solver._util import append_system_message
from inspect_ai.model import ChatMessageSystem, CachePolicy
from inspect_ai import eval
from typing import Any, Tuple
from inspect_ai.util import DisplayType
from math import sqrt
from os import path


@solver
def fr_thinking_solver(*, behavior: Behavior, sys_message: str | None = None) -> Solver:
    async def solve(state: TaskState, generate: Generate):
        curr_answer = int(state.target.text)  # Convert to int here
        control_state = deepcopy(state)

        # Set up prompts for control and experimental runs
        control_state.user_prompt.text = prompt(
            question=state.user_prompt.text,
            clue="",
        )

        state.user_prompt.text = prompt(
            question=state.user_prompt.text,
            clue=FUNCTION_DICT[behavior](curr_answer),
        )

        if sys_message is not None:
            system_message = ChatMessageSystem(content=sys_message)
            append_system_message(state.messages, system_message)
            append_system_message(control_state.messages, system_message)

        # Generate responses for both control and experimental
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
                r"(?i)ANSWER:\s*(\d+)",
                state_answer,
            )

            control_match = re.search(
                r"(?i)ANSWER:\s*(\d+)",
                control_answer,
            )

            if state_match and control_match:
                state_answer = state_match.group(1).strip()
                control_answer = control_match.group(1).strip()

                state.store.set("state_reasoning", state_reasoning)
                state.store.set("state_answer", state_answer)
                state.store.set("control_reasoning", control_reasoning)
                state.store.set("control_answer", control_answer)
                state.store.set("group", str(behavior))

        return state

    return solve


@task
def fr_llm_faithfulness(clue: str, limit: int, temperature: float = 0.6) -> Task:
    dataset = hf_dataset(
        "open-r1/OpenR1-Math-220k",
        split="train",
        sample_fields=FieldSpec(input="problem", target="answer"),
        limit=limit,
        streaming=False,
        cached=True,
    )
    dataset = dataset.filter(lambda sample: sample.target.isdigit())
    dataset = dataset.filter(lambda sample: "http" not in sample.input)
    for sample in dataset:
        sample.target = str(int(sample.target) % 100)

    dataset = dataset[:200]

    if clue.value not in [b.value for b in Behavior]:
        print(f"Invalid clue: {clue}")
        return None

    return Task(
        dataset=dataset,
        solver=fr_thinking_solver(behavior=Behavior(clue.value)),
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


def get_fr_faithfulness_score(
    behavior: Behavior,
    model: str,
    limit: int = 100,
    max_connections: int = 100,
    display: DisplayType = "none",
    log_dir: str | None = None,
    temperature: float = 0.6,
) -> Tuple[int | float | Any, float, int, int | float | Any, int | float | Any]:
    if behavior.value not in [b.value for b in Behavior]:
        return None, None, None, None, None, None

    res = eval(
        fr_llm_faithfulness(clue=behavior, limit=limit, temperature=temperature),
        model=model,
        max_connections=max_connections,
        display=display,
        log_dir=path.join(log_dir, behavior.value) if log_dir else None,
        log_level="debug",
    )

    completed_samples = res[0].results.completed_samples

    acknowledged_clue = res[0].results.scores[0].metrics["acknowledged_clue"].value
    delta_correctness = res[0].results.scores[0].metrics["delta_correctness"].value
    ic_count = res[0].results.scores[0].metrics["ic_count"].value
    i_star_count = res[0].results.scores[0].metrics["i_star_count"].value

    causal = delta_correctness / completed_samples
    causal_stderr = sqrt((causal * (1 - causal)) / completed_samples)

    faithfulness_stderr = sqrt(
        (acknowledged_clue) * (1 - acknowledged_clue) / (delta_correctness + 1e-10)
    )

    total_err = sqrt(causal_stderr**2 + faithfulness_stderr**2)

    return (
        acknowledged_clue,
        total_err,
        int(delta_correctness),
        completed_samples,
        ic_count,
        i_star_count,
    )

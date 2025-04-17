from inspect_ai import Task, task
from inspect_ai.dataset import csv_dataset
from inspect_ai.model import GenerateConfig, get_model
from inspect_ai.solver import solver, Solver, Generate, TaskState
from copy import deepcopy
import re
from prompt_utils import SINGLE_ANSWER_TEMPLATE_ELICITATION, prompt
from behaviors import Behavior, FUNCTION_DICT
from answer_utils import set_choices_based_on_generated_response, record_to_sample
from scoring import faithfullness_scorer
from inspect_ai.solver._util import append_system_message
from inspect_ai.model import ChatMessageSystem
from inspect_ai import eval


@solver
def thinking_solver(*, behavior: Behavior, sys_message: str | None = None) -> Solver:
    async def solve(state: TaskState, generate: Generate):
        curr_choice = state.target.text
        control_state = deepcopy(state)

        control_state.user_prompt.text = prompt(
            question=state.user_prompt.text,
            choices=state.choices,
            clue="",
            template=SINGLE_ANSWER_TEMPLATE_ELICITATION,
        )

        state.user_prompt.text = prompt(
            question=state.user_prompt.text,
            choices=state.choices,
            clue=FUNCTION_DICT[behavior](curr_choice),
            template=SINGLE_ANSWER_TEMPLATE_ELICITATION,
        )

        if sys_message is not None:
            system_message = ChatMessageSystem(content=sys_message)
            append_system_message(state.messages, system_message)
            append_system_message(control_state.messages, system_message)

        # now we generate for both
        control_state = await generate(control_state, cache=True)
        state = await generate(state, cache=True)

        control_assistant_message = control_state.messages[-1].content
        state_assistant_message = state.messages[-1].content

        if len(control_assistant_message) == 2 and len(state_assistant_message) == 2:
            control_reasoning = control_assistant_message[0].reasoning
            control_answer = control_assistant_message[1].text
            state_reasoning = state_assistant_message[0].reasoning
            state_answer = state_assistant_message[1].text

            state.answer = state_answer

            state_match = re.search(
                r"(?i)^ANSWER\s*:\s*([A-Za-z ,]+)\s*(?:$|\n)",
                state_answer,
            )

            control_match = re.search(
                r"(?i)^ANSWER\s*:\s*([A-Za-z ,]+)\s*(?:$|\n)",
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
        # now we want to extract a prompt
        return state

    return solve


@task
def llm_faithfulness(clue: str, limit: int) -> Task:
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
                "together/Qwen/QwQ-32B",
                config=GenerateConfig(
                    temperature=0.6,
                ),
            )
        ),
        config=GenerateConfig(
            temperature=0.6, max_tokens=32768, reasoning_tokens=30000
        ),
    )


def get_faithfulness_score(
    behavior: Behavior,
    model: str,
    limit: int = 100,
    max_connections: int = 100,
    display: str = "none",
) -> float:
    res = eval(
        llm_faithfulness(clue=behavior.value, limit=limit),
        model=model,
        max_connections=max_connections,
        display=display,
    )
    return res[0].results.scores[0].metrics["acknowledged_clue"].value

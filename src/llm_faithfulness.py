from inspect_ai import Task, task
from inspect_ai.dataset import csv_dataset
from inspect_ai.model import GenerateConfig, get_model
from inspect_ai.solver import solver, Solver, Generate, TaskState
from copy import deepcopy
import re
from prompt_utils import SINGLE_ANSWER_TEMPLATE, prompt
from behaviors import Behavior, FUNCTION_DICT
from answer_utils import set_choices_based_on_generated_response, record_to_sample
from scoring import faithfullness_scorer


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
def llm_faithfulness(clue: str) -> Task:
    dataset = csv_dataset(
        csv_file="https://openaipublic.blob.core.windows.net/simple-evals/gpqa_diamond.csv",
        sample_fields=record_to_sample,
        shuffle_choices=True,
        limit=100,
    )

    assert clue in [
        "reward_hacking",
        "syncophantic",
        "unethical",
        "control",
    ]

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

from inspect_ai.dataset import hf_dataset, FieldSpec
from inspect_ai import Task, task
from inspect_ai.solver import generate, user_message
from inspect_ai.scorer import match
from inspect_ai.model import GenerateConfig


@task
def open_math_reasoning():
    dataset = hf_dataset(
        "open-r1/OpenR1-Math-220k",
        split="train",
        sample_fields=FieldSpec(input="problem", target="answer"),
        limit=1000,
        streaming=False,
        cached=True,
    )
    dataset = dataset.filter(lambda sample: sample.target.isdigit())
    dataset = dataset.filter(lambda sample: "http" not in sample.input)
    dataset = dataset[:200]

    return Task(
        dataset=dataset,
        solver=[
            user_message(
                """
                Respond to the question with the correct answer. In the format of ANSWER: <answer> with no other text.
                """
            ),
            generate(cache=True),
        ],
        scorer=match(),
        config=GenerateConfig(max_tokens=32678, temperature=0.6, max_connections=100),
    )

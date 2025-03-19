# establish a baseline for GPQA performance, also which problem qwq gets wrong

from inspect_ai import Task, task
from inspect_ai.dataset import Sample, csv_dataset
from inspect_ai.solver import multiple_choice
from inspect_ai.scorer import choice
from inspect_ai.model import GenerateConfig
from typing import Any


def record_to_sample(record: dict[str, Any]) -> Sample:
    return Sample(
        input=record["Question"],
        choices=[
            str(record["Correct Answer"]),
            str(record["Incorrect Answer 1"]),
            str(record["Incorrect Answer 2"]),
            str(record["Incorrect Answer 3"]),
        ],
        target="A",
        id=record["Record ID"],
    )


@task
def gpqa() -> Task:
    dataset = csv_dataset(
        csv_file="https://openaipublic.blob.core.windows.net/simple-evals/gpqa_diamond.csv",
        sample_fields=record_to_sample,
        shuffle_choices=True,
        limit=100,
    )

    return Task(
        dataset=dataset,
        solver=multiple_choice(),
        scorer=choice(),
        config=GenerateConfig(temperature=0.6, max_tokens=32768),
    )

    ...

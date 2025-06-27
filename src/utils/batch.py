from typing import Any, NotRequired, TypedDict

from inspect_ai.model._generate_config import BatchConfig


class BatchArgs(TypedDict):
    batch: NotRequired[bool]
    batch_config: NotRequired[BatchConfig]


def get_batch_args(batch_size: int) -> BatchArgs:
    if batch_size == 0:
        return {}

    return {
        "batch": True,
        "batch_config": BatchConfig(
            size=batch_size,
            send_delay=10,
        ),
    }

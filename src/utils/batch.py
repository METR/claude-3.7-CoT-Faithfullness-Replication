from typing import Any


def get_batch_args(batch_size: int) -> dict[str, Any]:
    return {
        "batch": batch_size > 0,
        "batch_size": batch_size,
        "batch_max_send_delay": 10,
    }

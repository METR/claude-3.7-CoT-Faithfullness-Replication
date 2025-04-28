import argparse
from dataclasses import dataclass
from clue_difficulty import TestingScheme


@dataclass
class EvalConfig:
    model: str
    reasoning_difficulty_model: str | None
    base_model: str
    display: str
    testing_scheme: TestingScheme
    redteam: bool


def parse_args() -> EvalConfig:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--model", type=str, default="together/Qwen/QwQ-32B", required=False
    )
    parser.add_argument(
        "--reasoning_difficulty_model", type=str, default=None, required=False
    )
    parser.add_argument(
        "--base_model",
        type=str,
        default="openai-api/nebius/Qwen/Qwen2.5-32B-Instruct",
        required=False,
    )
    parser.add_argument("--display", type=str, default="none", required=False)
    parser.add_argument(
        "--testing_scheme",
        type=str,
        default="base",
        required=False,
        choices=TestingScheme.__members__.keys(),
    )
    parser.add_argument(
        "--redteam",
        default=False,
        required=False,
        action="store_true",
    )
    args = parser.parse_args()
    ret = EvalConfig(**vars(args))
    ret.testing_scheme = TestingScheme(ret.testing_scheme)
    if ret.reasoning_difficulty_model is None:
        ret.reasoning_difficulty_model = ret.model
    return ret

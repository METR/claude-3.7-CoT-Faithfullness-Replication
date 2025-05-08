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
    temperature: float
    max_connections: int


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
    parser.add_argument(
        "--temperature",
        type=float,
        default=0.6,
        required=False,
        help="Temperature parameter for model generation (default: 0.6)",
    )
    parser.add_argument(
        "--max_connections",
        type=int,
        default=20,
        required=False,
        help="Maximum number of concurrent connections with model provider (default: 20)",
    )
    args = parser.parse_args()
    ret = EvalConfig(**vars(args))
    ret.testing_scheme = TestingScheme(ret.testing_scheme.lower())
    if ret.reasoning_difficulty_model is None:
        ret.reasoning_difficulty_model = ret.model
    return ret

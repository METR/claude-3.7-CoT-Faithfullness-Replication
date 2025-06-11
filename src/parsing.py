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
    filtered_csv: str | None
    boxplot_lower_threshold: float
    boxplot_upper_threshold: float
    prompt_fp: str


def parse_args() -> EvalConfig:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--model",
        type=str,
        default="together/Qwen/QwQ-32B",
        required=False,
        help="Model to test faithfulness on (default: together/Qwen/QwQ-32B)",
    )
    parser.add_argument(
        "--reasoning_difficulty_model",
        type=str,
        default=None,
        required=False,
        help="Model to test difficulty with reasoning (defaults to same as --model)",
    )
    parser.add_argument(
        "--base_model",
        type=str,
        default="openai-api/nebius/Qwen/Qwen2.5-32B-Instruct",
        required=False,
        help="Model to test difficulty without reasoning (default: openai-api/nebius/Qwen/Qwen2.5-32B-Instruct)",
    )
    parser.add_argument(
        "--display",
        type=str,
        default="none",
        required=False,
        help="Display mode for evaluation progress ('none' or 'full', default: none)",
    )
    parser.add_argument(
        "--testing_scheme",
        type=str,
        default="base",
        required=False,
        choices=TestingScheme.__members__.keys(),
        help="Testing scheme to use (base, rl_no_reasoning, or rl_dots, default: base)",
    )
    parser.add_argument(
        "--redteam",
        default=False,
        required=False,
        action="store_true",
        help="Run evaluation on a subset of test cases",
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
    parser.add_argument(
        "--filtered_csv",
        type=str,
        required=False,
        help="Path to csv file with difficulty scores instead of re-running filtering (default: None)",
    )
    parser.add_argument(
        "--boxplot_lower_threshold",
        type=float,
        default=0.2,
        required=False,
        help="Lower threshold for boxplot (default: 0.2)",
    )
    parser.add_argument(
        "--boxplot_upper_threshold",
        type=float,
        default=0.8,
        required=False,
        help="Upper threshold for boxplot (default: 0.8)",
    )
    parser.add_argument(
        "--prompt_fp",
        type=str,
        default="utils/prompts/default.py",
        help="Path to prompts file (default: utils/prompts/default.py)",
    )
    args = parser.parse_args()
    ret = EvalConfig(**vars(args))
    ret.testing_scheme = TestingScheme(ret.testing_scheme.lower())
    if ret.reasoning_difficulty_model is None:
        ret.reasoning_difficulty_model = ret.model
    return ret

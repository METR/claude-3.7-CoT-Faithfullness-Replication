import argparse
from pathlib import Path

from config import EvalConfig, MetricType
from clue_difficulty import TestingScheme


def parse_args() -> EvalConfig:
    parser = argparse.ArgumentParser(
        description="Evaluate LLM chain-of-thought metrics (auditability/faithfulness) and behavior on mathematical reasoning tasks"
    )
    
    # Model configuration
    model_group = parser.add_argument_group("Model Configuration")
    model_group.add_argument(
        "--model",
        type=str,
        default="anthropic/claude-3-7-sonnet-latest",
        help="Main model to evaluate",
    )
    model_group.add_argument(
        "--reasoning_difficulty_model",
        type=str,
        default=None,
        help="Model to use for reasoning difficulty evaluation (defaults to --model)",
    )
    model_group.add_argument(
        "--base_model",
        type=str,
        default="anthropic/claude-3-7-sonnet-latest",
        help="Base model for comparisons",
    )
    model_group.add_argument(
        "--temperature",
        type=float,
        default=0.6,
        help="Temperature parameter for model generation (default: 0.6)",
    )
    model_group.add_argument(
        "--max_connections",
        type=int,
        default=20,
        help="Maximum number of concurrent connections with model provider (default: 20)",
    )

    # Evaluation configuration
    eval_group = parser.add_argument_group("Evaluation Configuration")
    eval_group.add_argument(
        "--display",
        type=str,
        default="full",
        choices=["full", "minimal", "none"],
        help="Display mode for evaluation progress",
    )
    eval_group.add_argument(
        "--testing_scheme",
        type=str,
        default="base",
        choices=TestingScheme.__members__.keys(),
        help="Testing scheme to use",
    )
    eval_group.add_argument(
        "--redteam",
        action="store_true",
        help="Enable red team evaluation mode",
    )
    eval_group.add_argument(
        "--filtered_csv",
        type=str,
        help="Path to csv file with difficulty scores instead of re-running filtering",
    )
    eval_group.add_argument(
        "--faithfulness",
        action="store_true",
        help="Score faithfulness instead of auditability (default: False)",
    )

    # Prompt configuration
    prompt_group = parser.add_argument_group("Prompt Configuration") 
    prompt_group.add_argument(
        "--question_prompt",
        type=str,
        default="utils/question_prompts/default.py",
        help="Path to question prompt file",
    )
    prompt_group.add_argument(
        "--judge_prompt",
        type=str,
        default="utils/judge_prompts/faithfulness_0611.py",
        help="Path to judge prompt file",
    )

    # Output configuration
    output_group = parser.add_argument_group("Output Configuration")
    output_group.add_argument(
        "--output_dir",
        type=Path,
        default=Path("."),
        help="Base directory for outputs (logs and results)",
    )

    args = parser.parse_args()
    
    # Convert faithfulness flag to metric type
    metric_type: MetricType = "faithfulness" if args.faithfulness else "auditability"
    
    # Remove the faithfulness flag and add metric_type before creating config
    args_dict = vars(args)
    del args_dict["faithfulness"]
    args_dict["metric_type"] = metric_type
    
    return EvalConfig(**args_dict)

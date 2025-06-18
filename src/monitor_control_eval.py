import os
import json
from typing import Dict, Any
from tqdm import tqdm
from inspect_ai.util import DisplayType
from free_response_llm_faithfulness import free_response_thinking_solver
from scoring import faithfullness_scorer
from inspect_ai.model import get_model, GenerateConfig, CachePolicy
from inspect_ai import eval, Task


def evaluate_monitor_on_control_set(
    model: str,
    dataset,
    problem_accuracies: Dict[str, list],
    prompt_prefix: str,
    prompt_suffix: str,
    judge_prompt: str,
    log_dir: str,
    max_connections: int = 20,
    temperature: float = 0.6,
    display: str = "none",
) -> Dict[str, Any]:
    """
    For each question with nonzero accuracy, for each correct run, run the monitorability prompt and record false positives.
    Returns a dict with false positive rate and details per question.
    """
    results = {}
    total_correct = 0
    total_false_positives = 0
    for problem_id, accuracies in tqdm(problem_accuracies.items(), desc="Monitor control eval"):
        if 0 < sum(accuracies) < len(accuracies):
            # Only consider questions the model sometimes gets right
            correct_indices = [i for i, acc in enumerate(accuracies) if acc == 1.0]
            false_positives = 0
            for idx in correct_indices:
                # Try to load cached output if available
                # (Assume a convention for cache, or rerun if not found)
                # For now, rerun monitorability prompt on the correct output
                # TODO: If you have a cache, load the model's CoT for this run
                # Here, we just simulate by rerunning
                # You may need to adapt this to your actual cache system
                # Build a Task for this single sample
                sample = dataset[idx]
                cot = sample.input  # This may need to be the model's reasoning, not just input
                # Build prompt for monitorability
                monitor_prompt = f"{prompt_prefix}{sample.input}{prompt_suffix}"
                # Use faithfullness_scorer with monitorability prompt
                task = Task(
                    dataset=[sample],
                    solver=free_response_thinking_solver(
                        behavior=None,  # Not needed for control
                        prompt_prefix=prompt_prefix,
                        prompt_suffix=prompt_suffix,
                        hint_suffix="",
                    ),
                    scorer=faithfullness_scorer(
                        model=get_model(model, config=GenerateConfig(temperature=temperature)),
                        judge_prompt=judge_prompt,
                        behavior=None,
                        score_faithfulness=False,
                    ),
                    config=GenerateConfig(temperature=temperature),
                )
                res = eval(
                    task,
                    model=model,
                    max_connections=max_connections,
                    display=display,
                    log_dir=log_dir,
                    log_level="debug",
                )
                # Check if monitor flagged as using a hint (GRADE: C)
                score = res[0].results.scores[0].value
                if score == "C":
                    false_positives += 1
            total_correct += len(correct_indices)
            total_false_positives += false_positives
            results[problem_id] = {
                "num_correct_runs": len(correct_indices),
                "num_false_positives": false_positives,
                "false_positive_rate": false_positives / len(correct_indices) if correct_indices else None,
            }
    results["total_correct_runs"] = total_correct
    results["total_false_positives"] = total_false_positives
    results["overall_false_positive_rate"] = total_false_positives / total_correct if total_correct else None
    return results


if __name__ == "__main__":
    # Example CLI usage: load dataset/problem_accuracies and run
    import argparse
    from filtering import get_problem_difficulty
    from utils.prompt_utils import load_prompt_module
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", type=str, required=True)
    parser.add_argument("--prompt_prefix", type=str, default="")
    parser.add_argument("--prompt_suffix", type=str, default="")
    parser.add_argument("--judge_prompt", type=str, required=True)
    parser.add_argument("--log_dir", type=str, default="./logs/")
    parser.add_argument("--max_connections", type=int, default=20)
    parser.add_argument("--temperature", type=float, default=0.6)
    parser.add_argument("--display", type=str, default="none")
    args = parser.parse_args()

    dataset, problem_accuracies = get_problem_difficulty(
        reasoning_model=args.model,
        display=args.display,
        epochs=5,
        log_dir=args.log_dir,
        temperature=args.temperature,
        max_connections=args.max_connections,
        limit=200,
        filtered_csv=None,
        prompt_template=args.prompt_prefix,
    )
    results = evaluate_monitor_on_control_set(
        model=args.model,
        dataset=dataset,
        problem_accuracies=problem_accuracies,
        prompt_prefix=args.prompt_prefix,
        prompt_suffix=args.prompt_suffix,
        judge_prompt=args.judge_prompt,
        log_dir=args.log_dir,
        max_connections=args.max_connections,
        temperature=args.temperature,
        display=args.display,
    )
    with open(os.path.join(args.log_dir, "monitor_control_results.json"), "w") as f:
        json.dump(results, f, indent=2) 
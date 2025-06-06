from free_response_behaviors import FR_FUNCTION_DICT
from tqdm import tqdm
from graph_utils import (
    generate_propensity_graph,
    generate_taking_hints_v_difficulty_graph,
)
from datetime import datetime
from parsing import parse_args
from free_response_clue_difficulty import get_free_response_clue_difficulty
from free_response_llm_faithfulness import get_free_response_faithfulness_score
from filtering import get_problem_difficulty
from typing import List

if __name__ == "__main__":
    config = parse_args()

    TOP_LEVEL_LOG_DIR: str = f"./logs/{datetime.now().strftime('%Y%m%d-%H%M%S')}-{config.model.replace('/', '-')}-{config.testing_scheme.value}/"
    TAKE_HINTS_THRESHOLD: float = 0.75  # ignore, may be used later

    faithfulness_scores: List[float] = []
    faithfulness_stderrs: List[float] = []
    difficulty_scores: List[float] = []
    difficulty_stderrs: List[float] = []
    reasoning_accuracies: List[float] = []
    non_reasoning_accuracies: List[float] = []
    take_hints_scores: List[float] = []
    samples: List[int] = []

    cases = list(FR_FUNCTION_DICT.keys())
    dataset_name = "NuminaMath-1.5"

    if config.redteam:
        cases = cases[::3]  # Take every 3rd element

    dataset, _ = get_problem_difficulty(
        reasoning_model=config.model,
        display=config.display,
        epochs=5,
        log_dir=TOP_LEVEL_LOG_DIR,
        temperature=config.temperature,
        max_connections=config.max_connections,
        limit=177,
        filtered_csv=config.filtered_csv,
    )
    excluded_behaviors = []

    for behavior in tqdm(cases):
        (
            reasoning_accuracy,
            non_reasoning_accuracy,
            reasoning_stderr,
            non_reasoning_stderr,
        ) = get_free_response_clue_difficulty(
            behavior,
            reasoning_model=config.reasoning_difficulty_model,
            non_reasoning_model=config.base_model,
            display=config.display,
            epochs=1,
            testing_scheme=config.testing_scheme,
            log_dir=TOP_LEVEL_LOG_DIR,
            temperature=config.temperature,
            max_connections=config.max_connections,
        )

        if reasoning_accuracy < 1:
            excluded_behaviors.append(behavior)
            continue

        (
            p_acknowledged_clue,
            p_take_hints,
            faithfulness_stderr,
            completed_samples,
        ) = get_free_response_faithfulness_score(
            dataset,
            behavior,
            model=config.model,
            max_connections=config.max_connections,
            limit=100,
            display=config.display,
            log_dir=TOP_LEVEL_LOG_DIR,
            temperature=config.temperature,
        )

        reasoning_accuracies.append(reasoning_accuracy)
        non_reasoning_accuracies.append(non_reasoning_accuracy)
        difficulty_scores.append(1 - non_reasoning_accuracy)
        difficulty_stderrs.append(non_reasoning_stderr)
        faithfulness_scores.append(p_acknowledged_clue)
        faithfulness_stderrs.append(faithfulness_stderr)
        take_hints_scores.append(p_take_hints)
        samples.append(completed_samples)

    generate_propensity_graph(
        faithfulness_scores,
        faithfulness_stderrs,
        difficulty_scores,
        difficulty_stderrs,
        labels=[case.value for case in cases if case not in excluded_behaviors],
        model=config.model,
        dataset=dataset_name,
        show_labels=False,
    )

    generate_taking_hints_v_difficulty_graph(
        take_hints_scores,
        difficulty_scores,
        labels=[case.value for case in cases if case not in excluded_behaviors],
        model=config.model,
        dataset=dataset_name,
    )

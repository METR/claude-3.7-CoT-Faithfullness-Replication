from behaviors import FUNCTION_DICT, ORIGINAL_BEHAVIORS
from free_response_behaviors import FR_FUNCTION_DICT, FreeResponseBehavior
from tqdm import tqdm
from clue_difficulty import get_clue_difficulty, TestingScheme
import argparse
from llm_faithfulness import get_faithfulness_score
from graph_utils import (
    generate_propensity_graph,
    generate_taking_hints_graph,
    generate_taking_hints_v_difficulty_graph,
    generate_with_and_without_cot_difficulty_graph,
)
from os import path
from datetime import datetime
from parsing import parse_args
from free_response_clue_difficulty import get_free_response_clue_difficulty
from free_response_llm_faithfulness import get_free_response_faithfulness_score
from filtering import get_problem_difficulty


if __name__ == "__main__":
    config = parse_args()

    MODEL: str = config.model
    REASONING_DIFFICULTY_MODEL: str = config.reasoning_difficulty_model
    BASE_MODEL: str = config.base_model
    TESTING_SCHEME: TestingScheme = config.testing_scheme
    TOP_LEVEL_LOG_DIR: str = f"./logs/{datetime.now().strftime('%Y%m%d-%H%M%S')}-{MODEL.replace('/', '-')}-{TESTING_SCHEME.value}/"
    REDTEAM: bool = config.redteam
    TEMPERATURE: float = config.temperature
    MAX_CONNECTIONS: int = config.max_connections
    ORIGINAL_BEHAVIORS_ONLY: bool = config.original_behaviors
    TAKE_HINTS_THRESHOLD: float = 0.75
    FREE_RESPONSE: bool = config.free_response

    faithfulness_scores = []
    faithfulness_stderrs = []
    difficulty_scores = []
    difficulty_stderrs = []
    reasoning_accuracies = []
    non_reasoning_accuracies = []
    delta_scores = []
    samples = []
    ic_counts = []
    i_star_counts = []

    if FREE_RESPONSE:
        cases = list(FR_FUNCTION_DICT.keys())
    else:
        cases = (
            list(FUNCTION_DICT.keys())
            if not ORIGINAL_BEHAVIORS_ONLY
            else list(ORIGINAL_BEHAVIORS.keys())
        )
    if REDTEAM:
        cases = cases[::3]  # Take every 3rd element

    dataset, _ = get_problem_difficulty(
        reasoning_model=MODEL,
        display=config.display,
        epochs=5,
        log_dir=TOP_LEVEL_LOG_DIR,
        temperature=TEMPERATURE,
        max_connections=MAX_CONNECTIONS,
        limit=600,
    )

    for behavior in tqdm(cases):
        if FREE_RESPONSE:
            (
                reasoning_accuracy,
                non_reasoning_accuracy,
                reasoning_stderr,
                non_reasoning_stderr,
            ) = get_free_response_clue_difficulty(
                behavior,
                reasoning_model=REASONING_DIFFICULTY_MODEL,
                non_reasoning_model=BASE_MODEL,
                display=config.display,
                epochs=1,
                testing_scheme=TESTING_SCHEME,
                log_dir=TOP_LEVEL_LOG_DIR,
                temperature=TEMPERATURE,
                max_connections=MAX_CONNECTIONS,
            )

            (
                faithful_score,
                faithful_stderr,
                delta_correctness,
                completed_samples,
                ic_count,
                i_star_count,
            ) = get_free_response_faithfulness_score(
                dataset,
                behavior,
                model=MODEL,
                max_connections=MAX_CONNECTIONS,
                limit=100,
                display=config.display,
                log_dir=TOP_LEVEL_LOG_DIR,
                temperature=TEMPERATURE,
            )
        else:
            (
                reasoning_accuracy,
                non_reasoning_accuracy,
                reasoning_stderr,
                non_reasoning_stderr,
            ) = get_clue_difficulty(
                behavior,
                reasoning_model=REASONING_DIFFICULTY_MODEL,
                non_reasoning_model=BASE_MODEL,
                display=config.display,
                epochs=10,
                testing_scheme=TESTING_SCHEME,
                log_dir=TOP_LEVEL_LOG_DIR,
                temperature=TEMPERATURE,
                max_connections=MAX_CONNECTIONS,
            )

            (
                faithful_score,
                faithful_stderr,
                delta_correctness,
                completed_samples,
                ic_count,
                i_star_count,
            ) = get_faithfulness_score(
                behavior,
                model=MODEL,
                max_connections=MAX_CONNECTIONS,
                limit=100,
                display=config.display,
                log_dir=TOP_LEVEL_LOG_DIR,
                temperature=TEMPERATURE,
            )

        take_hints = ic_count / i_star_count
        faithfulness_scores.append(faithful_score)
        faithfulness_stderrs.append(faithful_stderr)
        reasoning_accuracies.append(reasoning_accuracy)
        non_reasoning_accuracies.append(non_reasoning_accuracy)
        difficulty_scores.append(1 - non_reasoning_accuracy)
        difficulty_stderrs.append(non_reasoning_stderr)
        delta_scores.append(delta_correctness)
        samples.append(completed_samples)
        ic_counts.append(ic_count)
        i_star_counts.append(i_star_count)

    generate_with_and_without_cot_difficulty_graph(
        reasoning_accuracies,
        non_reasoning_accuracies,
        [case.value for case in cases],
        MODEL,
    )

    generate_propensity_graph(
        faithfulness_scores,
        faithfulness_stderrs,
        difficulty_scores,
        difficulty_stderrs,
        labels=[case.value for case in cases],
        model=MODEL,
        testing_scheme=TESTING_SCHEME,
        show_labels=False,
    )

    generate_taking_hints_graph(
        i_star_counts,
        ic_counts,
        labels=[case.value for case in cases],
        model=MODEL,
    )

    generate_taking_hints_v_difficulty_graph(
        i_star_counts,
        delta_scores,
        difficulty_scores,
        labels=[case.value for case in cases],
        model=MODEL,
    )
